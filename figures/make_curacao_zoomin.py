"""Create zoom-in crops for all static comparison scenes.

Criterion: SSIM between Ours and each baseline → sliding-window min SSIM.
Generates zoom-in figures for:
  - static_multimethod: curacao, iui3_redsea, japanese_gardens, panama (5-col, render+depth)
  - japanese_dewater (4-col, render+dewater, no 4DGS)
Uses original source images (no white borders).
"""

from pathlib import Path
import matplotlib.cm as cm
import numpy as np
from scipy import ndimage
from skimage.metrics import structural_similarity as ssim
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("F:/All_Images_Collection/All_Images_Collection")
DATA_ROOT = Path("D:/underwater/4DGaussians/data/SeaThru-NeRF/SeathruNeRF_dataset2")
BL_BASE = Path("D:/underwater/4DGaussians/output/baseline_seasplat/错了")
BEST_CKPT = Path("D:/underwater/thesis-2026/figures/best_checkpoints")
OUT_DIR = Path(__file__).resolve().parent / "static_multimethod"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GAP = 8
ROW_GAP = 10
HEADER_H = 52
SSIM_WIN = 11
RED = (220, 40, 40)
FONT_SIZE_LABEL = 34
FONT_SIZE_NUM = 20
OVERVIEW_W_5COL = 240
OVERVIEW_W_4COL = 270
CROP_DISPLAY_5COL = 190
CROP_DISPLAY_4COL = 220


def font(size, bold=False):
    if bold:
        candidates = [
            r"C:/Windows/Fonts/simhei.ttf",
            r"C:/Windows/Fonts/msyhbd.ttc",
            r"C:/Windows/Fonts/arialbd.ttf",
        ]
    else:
        candidates = [
            r"C:/Windows/Fonts/simsun.ttc",
            r"C:/Windows/Fonts/msyh.ttc",
            r"C:/Windows/Fonts/arial.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def find_named(base, preferred_split, subdir, fname):
    for split in (preferred_split, "test", "train"):
        p = base / split / subdir / fname
        if p.exists():
            return p
    return None


# ============================================================
# Image loading
# ============================================================

def load_rgb(path, target_size):
    im = Image.open(path).convert("RGB")
    if im.size != target_size:
        im = im.resize(target_size, Image.LANCZOS)
    return np.array(im, dtype=np.float32)


def load_depth_heatmap(path, target_size):
    im = Image.open(path)
    arr = np.array(im)
    if arr.ndim == 3:
        arr = arr[..., 0].astype(np.float32)
    else:
        arr = arr.astype(np.float32)
    finite = np.isfinite(arr)
    if finite.any() and float(arr[finite].max()) > float(arr[finite].min()):
        lo = float(np.percentile(arr[finite], 1))
        hi = float(np.percentile(arr[finite], 99))
        if hi <= lo:
            lo, hi = float(arr[finite].min()), float(arr[finite].max())
        norm = np.clip((arr - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    else:
        norm = np.zeros_like(arr)
    rgb = (cm.viridis(norm)[..., :3] * 255).astype(np.uint8)
    hm = Image.fromarray(rgb).resize(target_size, Image.LANCZOS)
    return np.array(hm)


def blank(target_size):
    return np.full((target_size[1], target_size[0], 3), 255, dtype=np.uint8)


# ============================================================
# SSIM-based region finders
# ============================================================

def ssim_map(img1, img2):
    maps = []
    for c in range(3):
        _, s = ssim(img1[..., c], img2[..., c],
                     data_range=255.0, win_size=SSIM_WIN,
                     full=True, channel_axis=None)
        maps.append(s)
    return np.mean(maps, axis=0)


def find_best_region(ours, baselines, baseline_names, h, w, crop_size):
    """Find CROP_SIZE region with lowest mean SSIM(ours, baselines)."""
    half = crop_size // 2
    ssim_maps = [ssim_map(ours, bl) for bl in baselines]
    ssim_combined = np.mean(ssim_maps, axis=0)
    dissim = 1.0 - ssim_combined
    window_mean = ndimage.uniform_filter(dissim, size=crop_size)
    sh, sw = window_mean.shape
    mask = np.zeros_like(window_mean)
    mask[half: sh - half, half: sw - half] = 1.0
    best_y, best_x = np.unravel_index(np.argmax(np.where(mask, window_mean, -1.0)),
                                       window_mean.shape)
    cx, cy = int(best_x), int(best_y)
    info = {}
    for name, sm in zip(baseline_names, ssim_maps):
        info[name] = float(sm[cy-half:cy+half, cx-half:cx+half].mean())
    return cx, cy, info


def find_best_region_gt_ref(ours, gt, baselines, baseline_names, h, w, crop_size):
    """Find region where Ours is MOST similar to GT while baselines are LEAST similar.

    Criterion: SSIM(Ours, GT) x (SSIM(Ours, GT) - mean(SSIM(baseline_i, GT))) -> maximize.
    """
    half = crop_size // 2
    ssim_ours_gt = ssim_map(ours, gt)
    ssim_bl_gt = [ssim_map(bl, gt) for bl in baselines]
    ssim_bl_mean = np.mean(ssim_bl_gt, axis=0)

    advantage = ssim_ours_gt - ssim_bl_mean
    score = advantage * np.maximum(ssim_ours_gt, 0.0)

    window_score = ndimage.uniform_filter(score, size=crop_size)
    window_ours_gt = ndimage.uniform_filter(ssim_ours_gt, size=crop_size)

    sh, sw = window_score.shape
    mask = np.zeros_like(window_score)
    mask[half: sh - half, half: sw - half] = 1.0
    mask[window_ours_gt < 0.3] = 0

    best_y, best_x = np.unravel_index(np.argmax(np.where(mask, window_score, -1.0)),
                                       window_score.shape)
    cx, cy = int(best_x), int(best_y)
    info = {}
    info["Ours vs GT"] = float(ssim_ours_gt[cy-half:cy+half, cx-half:cx+half].mean())
    for name, sm in zip(baseline_names, ssim_bl_gt):
        info[f"{name} vs GT"] = float(sm[cy-half:cy+half, cx-half:cx+half].mean())
    info["advantage"] = advantage[cy-half:cy+half, cx-half:cx+half].mean()
    return cx, cy, info


# ============================================================
# Figure builders (labels at TOP, larger fonts)
# ============================================================

def draw_labels_top(draw, labels, methods, overview_w, col_x_fn):
    """Draw method name labels at the top of the figure."""
    fnt = font(FONT_SIZE_LABEL, False)
    for j, label in enumerate(labels):
        x = col_x_fn(j)
        tw = draw.textbbox((0, 0), label, font=fnt)
        tx = x + (overview_w - (tw[2] - tw[0])) // 2
        draw.text((tx, 5), label, fill=(0, 0, 0), font=fnt)


def paste_crop_centered(canvas, crop_im, col_center, y, crop_display):
    canvas.paste(crop_im, (col_center - crop_display // 2, y))


def build_figure_5col(renders, depths, methods, labels,
                      cx, cy, half, target_size,
                      out_path, crop_dir):
    h, w = target_size[1], target_size[0]
    overview_w = OVERVIEW_W_5COL
    overview_h = int(overview_w * h / w)
    scale = overview_w / w
    scaled_half = int(half * scale)
    n_cols = len(methods)
    crop_display = CROP_DISPLAY_5COL

    canvas_w = n_cols * overview_w + (n_cols - 1) * GAP
    canvas_h = (HEADER_H + ROW_GAP
                + overview_h * 2 + ROW_GAP
                + crop_display * 2 + ROW_GAP)
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    def col_x(j):
        return j * (overview_w + GAP)

    # ===== Labels at top =====
    draw_labels_top(draw, labels, methods, overview_w, col_x)

    y_cur = HEADER_H + ROW_GAP

    # ===== Overview render row =====
    for j, m in enumerate(methods):
        im = Image.fromarray(renders[m].astype(np.uint8))
        im = im.resize((overview_w, overview_h), Image.LANCZOS)
        im_d = ImageDraw.Draw(im)
        scx, scy = int(cx * scale), int(cy * scale)
        im_d.rectangle([scx - scaled_half, scy - scaled_half,
                        scx + scaled_half, scy + scaled_half], outline=RED, width=2)
        canvas.paste(im, (col_x(j), y_cur))
    y_cur += overview_h + ROW_GAP

    # ===== Overview depth row =====
    for j, m in enumerate(methods):
        im = Image.fromarray(depths[m].astype(np.uint8))
        im = im.resize((overview_w, overview_h), Image.LANCZOS)
        if m != "orig":
            im_d = ImageDraw.Draw(im)
            scx, scy = int(cx * scale), int(cy * scale)
            im_d.rectangle([scx - scaled_half, scy - scaled_half,
                            scx + scaled_half, scy + scaled_half], outline=RED, width=2)
        canvas.paste(im, (col_x(j), y_cur))
    y_cur += overview_h + ROW_GAP

    x1, y1 = cx - half, cy - half
    x2, y2 = cx + half, cy + half

    # ===== Render crops =====
    for j, m in enumerate(methods):
        crop = renders[m][y1:y2, x1:x2].astype(np.uint8)
        crop_im = Image.fromarray(crop).resize((crop_display, crop_display), Image.LANCZOS)
        if m == "ours":
            b = 3
            bordered = Image.new("RGB", (crop_display + 2*b, crop_display + 2*b), RED)
            bordered.paste(crop_im, (b, b))
            crop_im = bordered.resize((crop_display, crop_display), Image.LANCZOS)
        paste_crop_centered(canvas, crop_im, col_x(j) + overview_w // 2, y_cur, crop_display)
    y_cur += crop_display + ROW_GAP

    # ===== Depth crops =====
    for j, m in enumerate(methods):
        crop = depths[m][y1:y2, x1:x2].astype(np.uint8)
        crop_im = Image.fromarray(crop).resize((crop_display, crop_display), Image.LANCZOS)
        if m == "ours":
            b = 3
            bordered = Image.new("RGB", (crop_display + 2*b, crop_display + 2*b), RED)
            bordered.paste(crop_im, (b, b))
            crop_im = bordered.resize((crop_display, crop_display), Image.LANCZOS)
        paste_crop_centered(canvas, crop_im, col_x(j) + overview_w // 2, y_cur, crop_display)

    canvas.save(out_path)
    print(f"  Saved: {out_path}")

    crop_dir.mkdir(parents=True, exist_ok=True)
    for m in methods:
        Image.fromarray(renders[m][y1:y2, x1:x2].astype(np.uint8)).save(crop_dir / f"crop_render_{m}.png")
        Image.fromarray(depths[m][y1:y2, x1:x2].astype(np.uint8)).save(crop_dir / f"crop_depth_{m}.png")


def build_figure_dewater(renders, dewatered, methods, labels,
                         cx, cy, half, target_size,
                         out_path, crop_dir):
    h, w = target_size[1], target_size[0]
    overview_w = OVERVIEW_W_4COL
    overview_h = int(overview_w * h / w)
    scale = overview_w / w
    scaled_half = int(half * scale)
    n_cols = len(methods)
    crop_display = CROP_DISPLAY_4COL

    canvas_w = n_cols * overview_w + (n_cols - 1) * GAP
    canvas_h = (HEADER_H + ROW_GAP
                + overview_h * 2 + ROW_GAP
                + crop_display * 2 + ROW_GAP)
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    def col_x(j):
        return j * (overview_w + GAP)

    # ===== Labels at top =====
    draw_labels_top(draw, labels, methods, overview_w, col_x)

    y_cur = HEADER_H + ROW_GAP

    # ===== Overview render row =====
    for j, m in enumerate(methods):
        im = Image.fromarray(renders[m].astype(np.uint8))
        im = im.resize((overview_w, overview_h), Image.LANCZOS)
        im_d = ImageDraw.Draw(im)
        scx, scy = int(cx * scale), int(cy * scale)
        im_d.rectangle([scx - scaled_half, scy - scaled_half,
                        scx + scaled_half, scy + scaled_half], outline=RED, width=2)
        canvas.paste(im, (col_x(j), y_cur))
    y_cur += overview_h + ROW_GAP

    # ===== Overview dewater row =====
    for j, m in enumerate(methods):
        im = Image.fromarray(dewatered[m].astype(np.uint8))
        im = im.resize((overview_w, overview_h), Image.LANCZOS)
        im_d = ImageDraw.Draw(im)
        scx, scy = int(cx * scale), int(cy * scale)
        im_d.rectangle([scx - scaled_half, scy - scaled_half,
                        scx + scaled_half, scy + scaled_half], outline=RED, width=2)
        canvas.paste(im, (col_x(j), y_cur))
    y_cur += overview_h + ROW_GAP

    x1, y1 = cx - half, cy - half
    x2, y2 = cx + half, cy + half

    # ===== Render crops =====
    for j, m in enumerate(methods):
        crop = renders[m][y1:y2, x1:x2].astype(np.uint8)
        crop_im = Image.fromarray(crop).resize((crop_display, crop_display), Image.LANCZOS)
        if m == "ours":
            b = 3
            bordered = Image.new("RGB", (crop_display + 2*b, crop_display + 2*b), RED)
            bordered.paste(crop_im, (b, b))
            crop_im = bordered.resize((crop_display, crop_display), Image.LANCZOS)
        paste_crop_centered(canvas, crop_im, col_x(j) + overview_w // 2, y_cur, crop_display)
    y_cur += crop_display + ROW_GAP

    # ===== Dewater crops =====
    for j, m in enumerate(methods):
        crop = dewatered[m][y1:y2, x1:x2].astype(np.uint8)
        crop_im = Image.fromarray(crop).resize((crop_display, crop_display), Image.LANCZOS)
        if m == "ours":
            b = 3
            bordered = Image.new("RGB", (crop_display + 2*b, crop_display + 2*b), RED)
            bordered.paste(crop_im, (b, b))
            crop_im = bordered.resize((crop_display, crop_display), Image.LANCZOS)
        paste_crop_centered(canvas, crop_im, col_x(j) + overview_w // 2, y_cur, crop_display)

    canvas.save(out_path)
    print(f"  Saved: {out_path}")

    crop_dir.mkdir(parents=True, exist_ok=True)
    for m in methods:
        Image.fromarray(renders[m][y1:y2, x1:x2].astype(np.uint8)).save(crop_dir / f"crop_render_{m}.png")
        Image.fromarray(dewatered[m][y1:y2, x1:x2].astype(np.uint8)).save(crop_dir / f"crop_dewater_{m}.png")


# ============================================================
# Scene processors
# ============================================================

def process_5col(name, dir_name, stn_dir, split, fname, idx,
                 baseline_sea_dir, ours_depth_dir, gt_ref=False):
    print(f"\n{'='*60}")
    print(f"Processing: {name}" + (" [GT-referenced]" if gt_ref else ""))

    orig_path = DATA_ROOT / stn_dir / "images_wb" / fname
    with Image.open(orig_path) as im:
        ts = im.size
    crop_size = int(ts[0] * 0.124)

    if baseline_sea_dir:
        seasplat_base = BL_BASE / baseline_sea_dir / split
    else:
        seasplat_base = ROOT / "SeaSplat_Results" / dir_name / split

    renders = {
        "orig": load_rgb(orig_path, ts),
        "stn": load_rgb(find_named(ROOT / "seathru_renders" / stn_dir, split, "rgb", fname), ts),
        "seasplat": load_rgb(seasplat_base / "with_water" / fname, ts),
        "fdgs": load_rgb(find_named(ROOT / "4DGS_Baseline_Results" / dir_name, split, "ours_14000/renders", idx), ts),
        "ours": load_rgb(find_named(ROOT / "Ours_Results" / dir_name, split, "with_water", fname), ts),
    }

    ours_depth_path = BEST_CKPT / ours_depth_dir / "test_depth_heatmap.png"
    depths = {
        "orig": blank(ts),
        "stn": load_depth_heatmap(find_named(ROOT / "seathru_renders" / stn_dir, split, "depth", fname), ts),
        "seasplat": load_depth_heatmap(seasplat_base / "depth" / fname, ts),
        "fdgs": load_depth_heatmap(find_named(ROOT / "4DGS_Baseline_Results" / dir_name, split, "ours_14000/depth", idx), ts),
        "ours": load_rgb(ours_depth_path, ts) if ours_depth_path.exists() else blank(ts),
    }

    methods = ["orig", "stn", "seasplat", "fdgs", "ours"]
    labels = ["GT(原图)", "STN", "SeaSplat", "4DGS", "Ours"]

    ours = renders["ours"]
    baselines = [renders["seasplat"], renders["fdgs"], renders["stn"]]
    bl_names = ["SeaSplat", "4DGS", "STN"]

    if gt_ref:
        cx, cy, info = find_best_region_gt_ref(ours, renders["orig"],
                                                baselines, bl_names,
                                                ts[1], ts[0], crop_size)
    else:
        cx, cy, info = find_best_region(ours, baselines, bl_names,
                                         ts[1], ts[0], crop_size)

    print(f"  Image: {ts[0]}x{ts[1]}, crop: {crop_size}")
    print(f"  Best center: ({cx}, {cy})")
    for k, v in info.items():
        print(f"  {k}: {v:.4f}")

    half = crop_size // 2
    suffix = "_gtref" if gt_ref else ""
    out_path = OUT_DIR / f"{name}_zoomin{suffix}.png"
    crop_dir = OUT_DIR / "cells" / f"{name}_zoomin{suffix}"
    build_figure_5col(renders, depths, methods, labels,
                      cx, cy, half, ts, out_path, crop_dir)


def process_dewater():
    name = "japanese_dewater"
    print(f"\n{'='*60}")
    print(f"Processing: {name}")

    fname = "MTN_1090.png"
    split = "test"
    orig_path = DATA_ROOT / "JapaneseGradens-RedSea" / "images_wb" / fname
    with Image.open(orig_path) as im:
        ts = im.size
    crop_size = int(ts[0] * 0.124)

    methods = ["orig", "stn", "seasplat", "ours"]
    labels = ["GT(原图)", "STN", "SeaSplat", "Ours"]

    renders = {
        "orig": load_rgb(orig_path, ts),
        "stn": load_rgb(ROOT / "seathru_renders/JapaneseGradens-RedSea" / split / "rgb" / fname, ts),
        "seasplat": load_rgb(ROOT / "SeaSplat_Results/JapaneseGradens" / split / "with_water" / fname, ts),
        "ours": load_rgb(ROOT / "Ours_Results/JapaneseGradens" / split / "with_water" / fname, ts),
    }

    dewatered = {
        "orig": load_rgb(orig_path, ts),
        "stn": load_rgb(ROOT / "seathru_renders/JapaneseGradens-RedSea" / split / "J" / fname, ts),
        "seasplat": load_rgb(ROOT / "SeaSplat_Results/JapaneseGradens" / split / "render" / fname, ts),
        "ours": load_rgb(ROOT / "Ours_Results/JapaneseGradens" / split / "render" / fname, ts),
    }

    ours = renders["ours"]
    baselines = [renders["seasplat"], renders["stn"]]
    bl_names = ["SeaSplat", "STN"]
    cx, cy, info = find_best_region_gt_ref(ours, renders["orig"],
                                            baselines, bl_names,
                                            ts[1], ts[0], crop_size)

    print(f"  Image: {ts[0]}x{ts[1]}, crop: {crop_size}")
    print(f"  Best center: ({cx}, {cy})")
    for k, v in info.items():
        print(f"  {k}: {v:.4f}")

    half = crop_size // 2
    out_path = OUT_DIR / f"{name}_zoomin.png"
    crop_dir = OUT_DIR / "cells" / f"{name}_zoomin"
    build_figure_dewater(renders, dewatered, methods, labels,
                         cx, cy, half, ts, out_path, crop_dir)


# ============================================================
# Main
# ============================================================

def main():
    # Default criterion (max inter-method difference)
    process_5col("curacao",
                 dir_name="Curasao", stn_dir="Curasao",
                 split="train", fname="MTN_1299.png", idx="00009.png",
                 baseline_sea_dir="Curasao_seasplat_seathru1_fixopencv",
                 ours_depth_dir="Curacao")

    process_5col("iui3_redsea",
                 dir_name="IUI3-RedSea", stn_dir="IUI3-RedSea",
                 split="train", fname="MTN_5927.png", idx="00020.png",
                 baseline_sea_dir="IUI3-RedSea_seasplat_seathru1_fixopencv",
                 ours_depth_dir="IUI3")

    process_5col("panama",
                 dir_name="Panama", stn_dir="Panama",
                 split="test", fname="MTN_1529.png", idx="00000.png",
                 baseline_sea_dir=None,
                 ours_depth_dir="Panama")

    # GT-referenced criterion
    process_5col("curacao",
                 dir_name="Curasao", stn_dir="Curasao",
                 split="train", fname="MTN_1299.png", idx="00009.png",
                 baseline_sea_dir="Curasao_seasplat_seathru1_fixopencv",
                 ours_depth_dir="Curacao", gt_ref=True)

    process_5col("iui3_redsea",
                 dir_name="IUI3-RedSea", stn_dir="IUI3-RedSea",
                 split="train", fname="MTN_5927.png", idx="00020.png",
                 baseline_sea_dir="IUI3-RedSea_seasplat_seathru1_fixopencv",
                 ours_depth_dir="IUI3", gt_ref=True)

    process_5col("japanese_gardens",
                 dir_name="JapaneseGradens", stn_dir="JapaneseGradens-RedSea",
                 split="test", fname="MTN_1090.png", idx="00000.png",
                 baseline_sea_dir=None,
                 ours_depth_dir="JapaneseGardens", gt_ref=True)

    process_5col("panama",
                 dir_name="Panama", stn_dir="Panama",
                 split="test", fname="MTN_1529.png", idx="00000.png",
                 baseline_sea_dir=None,
                 ours_depth_dir="Panama", gt_ref=True)

    process_dewater()

    print("\nAll done!")


if __name__ == "__main__":
    main()
