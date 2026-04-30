"""Compose thesis figures from training outputs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_BASE = Path(r"D:/underwater/4DGaussians/output")
FIG_DIR = Path(r"D:/underwater/thesis-2026/figures")
FIG_DIR.mkdir(exist_ok=True)

# Try to load a font for labels (Chinese-capable)
def get_font(size=22):
    for path in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc", "arial.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

import numpy as np

def normalize_image(im, lo_pct=1, hi_pct=99):
    """Percentile-stretch contrast for visibility."""
    a = np.array(im).astype(np.float32)
    if a.ndim == 3 and a.shape[2] == 4:
        a = a[..., :3]
    lo = np.percentile(a, lo_pct)
    hi = np.percentile(a, hi_pct)
    if hi <= lo:
        return im
    a = np.clip((a - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    return Image.fromarray(a)

def label_image(img, text, font_size=22):
    """Add a black bar with white text on top of image."""
    bar_h = font_size + 12
    new = Image.new("RGB", (img.size[0], img.size[1] + bar_h), (0, 0, 0))
    new.paste(img, (0, bar_h))
    d = ImageDraw.Draw(new)
    f = get_font(font_size)
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    d.text(((img.size[0] - tw) // 2, 6), text, fill=(255, 255, 255), font=f)
    return new

def hstack(imgs, gap=6, bg=(255, 255, 255)):
    h = max(i.size[1] for i in imgs)
    w = sum(i.size[0] for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGB", (w, h), bg)
    x = 0
    for i in imgs:
        out.paste(i, (x, 0))
        x += i.size[0] + gap
    return out

def vstack(imgs, gap=6, bg=(255, 255, 255)):
    w = max(i.size[0] for i in imgs)
    h = sum(i.size[1] for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGB", (w, h), bg)
    y = 0
    for i in imgs:
        out.paste(i, (0, y))
        y += i.size[1] + gap
    return out

def left_label(text, height, width=120, font_size=22):
    img = Image.new("RGB", (width, height), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f = get_font(font_size)
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(((width - tw) // 2, (height - th) // 2 - 4), text, fill=(255, 255, 255), font=f)
    return img

def open_resized(path, target_w=None, target_h=None):
    im = Image.open(path).convert("RGB")
    if target_w and target_h:
        im = im.resize((target_w, target_h), Image.LANCZOS)
    return im

# ============================================================================
# Figure 1: render_compare — GT / SeaSplat / 4DGS / Ours across 3 scenes
# ============================================================================

def fig_render_compare():
    """4-row × 4-col comparison: rows=Robot/Fish/Coral/Streaks, cols=GT/SeaSplat/4DGS/Ours.

    For Fish/Coral/Streaks the 4DGS-only checkpoint is unavailable; we substitute
    the Ours render rendered with the SeaThru module disabled by re-using GT-rendered
    SeaSplat (acts as best static-scene baseline). To avoid mis-labelling we
    simply drop the 4DGS column for those rows and align the three remaining cells.
    """
    target_w, target_h = 480, 360
    rows_data = [
        ("Robot",  OUT_BASE / "Robot_underwater_v2depth/test/ours_20000/gt/00000.png",
                   OUT_BASE / "baseline_seasplat/Robot_seasplat_eval_seathru_0327025302/test/render/0001.JPG",
                   OUT_BASE / "baseline/Robot/test/ours_14000/renders/00000.png",
                   OUT_BASE / "Robot_underwater_v2depth/test/ours_20000/renders/00000.png"),
        ("Coral",  OUT_BASE / "coral_uw_14k/test/ours_14000/gt/00007.png",
                   OUT_BASE / "baseline_seasplat/coral_seasplat_eval_seathru_0327134211/test/render/01059.png",
                   None,  # 4DGS-only checkpoint not available
                   OUT_BASE / "coral_uw_14k/test/ours_14000/renders/00007.png"),
        ("Streaks", OUT_BASE / "streaks_uw_14k/test/ours_14000/gt/00004.png",
                    OUT_BASE / "baseline_seasplat/streaks_seasplat_eval_seathru_0327142053/test/render/04742.png",
                    None,
                    OUT_BASE / "streaks_uw_14k/test/ours_14000/renders/00004.png"),
        ("Fish",   OUT_BASE / "fish_uw_14k/test/ours_14000/gt/00003.png",
                   OUT_BASE / "baseline_seasplat/fish_seasplat_eval_seathru_0327033041/test/render/02370.png",
                   None,
                   OUT_BASE / "fish_uw_14k/test/ours_14000/renders/00003.png"),
    ]

    rows = []
    for name, gt, sea, four, ours in rows_data:
        gt_im = open_resized(gt, target_w, target_h)
        sea_im = open_resized(sea, target_w, target_h)
        ours_im = open_resized(ours, target_w, target_h)
        if four is not None:
            four_im = open_resized(four, target_w, target_h)
        else:
            four_im = Image.new("RGB", (target_w, target_h), (32, 32, 32))
            d = ImageDraw.Draw(four_im)
            f = get_font(26)
            txt = "未提供 4DGS-only 模型"
            bbox = d.textbbox((0, 0), txt, font=f)
            d.text(((target_w - (bbox[2] - bbox[0])) // 2,
                    (target_h - (bbox[3] - bbox[1])) // 2 - 6), txt,
                   fill=(180, 180, 180), font=f)
        row = hstack([gt_im, sea_im, four_im, ours_im], gap=4)
        rows.append(hstack([left_label(name, row.size[1]), row], gap=4))

    # Header
    label_blank = Image.new("RGB", (120, 36), (0, 0, 0))
    hdr_imgs = [label_blank]
    for n in ["GT", "SeaSplat", "4DGS", "本文方法 (Ours)"]:
        hdr = Image.new("RGB", (target_w, 36), (0, 0, 0))
        d = ImageDraw.Draw(hdr)
        f = get_font(22)
        bbox = d.textbbox((0, 0), n, font=f)
        d.text(((target_w - (bbox[2] - bbox[0])) // 2, 6), n, fill=(255, 255, 255), font=f)
        hdr_imgs.append(hdr)
    header = hstack(hdr_imgs, gap=4)

    final = vstack([header] + rows, gap=6)
    out_path = FIG_DIR / "render_compare.png"
    final.save(out_path)
    print(f"Saved {out_path}")

# ============================================================================
# Figure 2: dewater — I (with water) vs J (clean) for Coral
# ============================================================================

def fig_dewater():
    target_w, target_h = 640, 480
    # Compute J (clean radiance) by removing backscatter and inverse attenuation
    # I = J * exp(-beta_d * z) + B_inf * (1 - exp(-beta_b * z))
    # SeaSplat exports: attenuation (= exp(-beta_d z)), backscatter (= B_inf (1 - exp(-beta_b z))), with_water (=I), render (=I as well)
    # So J = (I - backscatter) / attenuation
    base = OUT_BASE / "baseline_seasplat/coral_seasplat_eval_seathru_0327134211/test"
    idx = "01059.png"
    I = np.array(Image.open(base / "with_water" / idx).convert("RGB")).astype(np.float32)
    A = np.array(Image.open(base / "attenuation" / idx).convert("RGB")).astype(np.float32) / 255.0
    B = np.array(Image.open(base / "backscatter" / idx).convert("RGB")).astype(np.float32)
    A = np.clip(A, 0.05, 1.0)  # avoid div-by-zero
    J = (I - B) / A
    J = np.clip(J, 0, 255).astype(np.uint8)
    j_img = Image.fromarray(J).resize((target_w, target_h), Image.LANCZOS)
    i_img = Image.open(base / "with_water" / idx).convert("RGB").resize((target_w, target_h), Image.LANCZOS)
    li = label_image(i_img, "原始水下图像 I（含水体退化）", 22)
    lj = label_image(j_img, "去水后清洁场景 J（恢复结果）", 22)
    out = hstack([li, lj], gap=8)
    out_path = FIG_DIR / "dewater.png"
    out.save(out_path)
    print(f"Saved {out_path}")

# ============================================================================
# Figure 3: intermediate — depth, attenuation, backscatter (Coral)
# ============================================================================

def fig_intermediate():
    """Compose depth + attenuation + backscatter using viridis colormap for clarity."""
    import matplotlib.cm as cm
    target_w, target_h = 480, 360
    base = OUT_BASE / "baseline_seasplat/fish_seasplat_eval_seathru_0327033041/test"
    name = "02370.png"

    def to_viridis(path, single_channel=True, invert=False):
        a = np.array(Image.open(path).convert("RGBA"))
        if single_channel:
            v = a[..., 0].astype(np.float32)
        else:
            v = a[..., :3].mean(axis=2).astype(np.float32)
        if v.max() == v.min():
            v_norm = np.zeros_like(v)
        else:
            v_norm = (v - v.min()) / (v.max() - v.min())
        if invert:
            v_norm = 1.0 - v_norm
        rgba = (cm.viridis(v_norm) * 255).astype(np.uint8)
        return Image.fromarray(rgba[..., :3]).resize((target_w, target_h), Image.LANCZOS)

    depth = to_viridis(base / "depth" / name, single_channel=True)
    atten = to_viridis(base / "attenuation" / name, single_channel=False)
    bs = to_viridis(base / "backscatter" / name, single_channel=False)

    ld = label_image(depth, "深度图 D(z)", 20)
    la = label_image(atten, "衰减系数分布 A(z)", 20)
    lb = label_image(bs, "后向散射 B(z)", 20)
    out = hstack([ld, la, lb], gap=6)
    out_path = FIG_DIR / "intermediate.png"
    out.save(out_path)
    print(f"Saved {out_path}")

# ============================================================================
# Figure 4: ablation_qualitative — Coral & Streaks across configs
# ============================================================================

def fig_ablation_qualitative():
    target_w, target_h = 480, 360

    # Coral column: GT / SeaThru-only (seasplat) / Ours (Full)
    coral_gt = open_resized(OUT_BASE / "coral_uw_14k/test/ours_14000/gt/00007.png", target_w, target_h)
    coral_sea = open_resized(OUT_BASE / "baseline_seasplat/coral_seasplat_eval_seathru_0327134211/test/render/01059.png", target_w, target_h)
    coral_full = open_resized(OUT_BASE / "coral_uw_14k/test/ours_14000/renders/00007.png", target_w, target_h)
    coral_col = vstack([
        label_image(coral_gt, "Coral · GT", 18),
        label_image(coral_sea, "Coral · SeaThru-only (SeaSplat)", 18),
        label_image(coral_full, "Coral · Full (Ours)", 18),
    ], gap=4)

    streaks_gt = open_resized(OUT_BASE / "streaks_uw_14k/test/ours_14000/gt/00004.png", target_w, target_h)
    streaks_sea = open_resized(OUT_BASE / "baseline_seasplat/streaks_seasplat_eval_seathru_0327142053/test/render/04742.png", target_w, target_h)
    streaks_full = open_resized(OUT_BASE / "streaks_uw_14k/test/ours_14000/renders/00004.png", target_w, target_h)
    streaks_col = vstack([
        label_image(streaks_gt, "Streaks · GT", 18),
        label_image(streaks_sea, "Streaks · SeaThru-only (SeaSplat)", 18),
        label_image(streaks_full, "Streaks · Full (Ours)", 18),
    ], gap=4)

    out = hstack([coral_col, streaks_col], gap=10)
    out_path = FIG_DIR / "ablation_qualitative.png"
    out.save(out_path)
    print(f"Saved {out_path}")

# ============================================================================
# Figure 5: ablation_curves — copy training_curves.png from plots dir
# ============================================================================

def fig_ablation_curves():
    src = Path(r"D:/underwater/4DGaussians/plots/training_curves.png")
    if src.exists():
        im = Image.open(src).convert("RGB")
        out_path = FIG_DIR / "ablation_curves.png"
        im.save(out_path)
        print(f"Saved {out_path}")
    else:
        print(f"WARN: {src} not found")

# ============================================================================
if __name__ == "__main__":
    fig_render_compare()
    fig_dewater()
    fig_intermediate()
    fig_ablation_qualitative()
    fig_ablation_curves()
