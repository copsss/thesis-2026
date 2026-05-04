from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import matplotlib.cm as cm


ROOT = Path(r"D:/All_Images_Collection/All_Images_Collection")
OUT_DIR = Path(r"D:/underwater/thesis-2026/figures/static_multimethod")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CELL = (360, 270)
LEFT_LABEL_W = 78
HEADER_H = 48
ROW_LABEL_H = 0
GAP = 8
PAD = 10
BG = (255, 255, 255)
BORDER = (210, 210, 210)
TEXT = (25, 25, 25)
MUTED = (110, 110, 110)


SCENES = [
    {
        "key": "curacao",
        "title": "Curacao",
        "dir": "Curasao",
        "stn_dir": "Curasao",
        "ours_depth": "Curacao",
        "fname": "MTN_1288.png",
        "idx": "00000.png",
    },
    {
        "key": "iui3_redsea",
        "title": "IUI3-RedSea",
        "dir": "IUI3-RedSea",
        "stn_dir": "IUI3-RedSea",
        "ours_depth": "IUI3",
        "fname": "MTN_5894.png",
        "idx": "00000.png",
    },
    {
        "key": "japanese_gardens",
        "title": "JapaneseGardens-RedSea",
        "dir": "JapaneseGradens",
        "stn_dir": "JapaneseGradens-RedSea",
        "ours_depth": "JapaneseGardens",
        "fname": "MTN_1090.png",
        "idx": "00000.png",
    },
    {
        "key": "panama",
        "title": "Panama",
        "dir": "Panama",
        "stn_dir": "Panama",
        "ours_depth": "Panama",
        "fname": "MTN_1529.png",
        "idx": "00000.png",
    },
]


METHODS = [
    {
        "label": "3DGS",
        "render": lambda s: ROOT / "3DGS_Results" / s["dir"] / "test" / "ours_30000" / "renders" / s["idx"],
        "depth": lambda s: None,
    },
    {
        "label": "STN",
        "render": lambda s: find_named(ROOT / "seathru_renders" / s["stn_dir"], "rgb", s["fname"]),
        "depth": lambda s: find_named(ROOT / "seathru_renders" / s["stn_dir"], "depth", s["fname"]),
    },
    {
        "label": "SeaSplat",
        "render": lambda s: ROOT / "SeaSplat_Results" / s["dir"] / "test" / "with_water" / s["fname"],
        "depth": lambda s: ROOT / "SeaSplat_Results" / s["dir"] / "test" / "depth" / s["fname"],
    },
    {
        "label": "4DGS",
        "render": lambda s: ROOT / "4DGS_Baseline_Results" / s["dir"] / "test" / "ours_14000" / "renders" / s["idx"],
        "depth": lambda s: ROOT / "4DGS_Baseline_Results" / s["dir"] / "test" / "ours_14000" / "depth" / s["idx"],
    },
    {
        "label": "Ours",
        "render": lambda s: ROOT / "Ours_Results" / s["dir"] / "test" / "with_water" / s["fname"],
        "depth": lambda s: Path(r"D:/underwater/thesis-2026/figures/best_checkpoints") / s["ours_depth"] / "test_depth_heatmap.png",
        "depth_mode": "image",
    },
]


def font(size, bold=False):
    candidates = [
        r"C:/Windows/Fonts/arialbd.ttf" if bold else r"C:/Windows/Fonts/arial.ttf",
        r"C:/Windows/Fonts/calibrib.ttf" if bold else r"C:/Windows/Fonts/calibri.ttf",
        r"C:/Windows/Fonts/segoeuib.ttf" if bold else r"C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT_TITLE = font(25, True)
FONT_HEAD = font(22, True)
FONT_ROW = font(21, True)
FONT_NOTE = font(18, False)


def find_named(base, subdir, fname):
    for split in ("test", "train"):
        path = base / split / subdir / fname
        if path.exists():
            return path
    raise FileNotFoundError(f"Missing {subdir}/{fname} under {base}")


def fit_image(path):
    im = Image.open(path).convert("RGB")
    im = ImageOps.contain(im, CELL, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", CELL, BG)
    x = (CELL[0] - im.width) // 2
    y = (CELL[1] - im.height) // 2
    canvas.paste(im, (x, y))
    return canvas


def depth_heatmap(path):
    im = Image.open(path)
    arr = np.array(im)
    if arr.ndim == 3:
        arr = arr[..., :3].astype(np.float32).mean(axis=2)
    else:
        arr = arr.astype(np.float32)
    finite = np.isfinite(arr)
    if not finite.any() or float(arr[finite].max()) <= float(arr[finite].min()):
        norm = np.zeros_like(arr, dtype=np.float32)
    else:
        lo = float(np.percentile(arr[finite], 1))
        hi = float(np.percentile(arr[finite], 99))
        if hi <= lo:
            lo = float(arr[finite].min())
            hi = float(arr[finite].max())
        norm = np.clip((arr - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    rgb = (cm.viridis(norm)[..., :3] * 255).astype(np.uint8)
    hm = Image.fromarray(rgb, mode="RGB")
    hm = ImageOps.contain(hm, CELL, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", CELL, BG)
    x = (CELL[0] - hm.width) // 2
    y = (CELL[1] - hm.height) // 2
    canvas.paste(hm, (x, y))
    return canvas


def placeholder():
    im = Image.new("RGB", CELL, (245, 245, 245))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, CELL[0] - 1, CELL[1] - 1], outline=BORDER, width=2)
    text = "N/A"
    note = "no depth output"
    tw = draw.textbbox((0, 0), text, font=FONT_HEAD)
    nw = draw.textbbox((0, 0), note, font=FONT_NOTE)
    draw.text(((CELL[0] - (tw[2] - tw[0])) // 2, CELL[1] // 2 - 24), text, fill=MUTED, font=FONT_HEAD)
    draw.text(((CELL[0] - (nw[2] - nw[0])) // 2, CELL[1] // 2 + 10), note, fill=MUTED, font=FONT_NOTE)
    return im


def center_text(draw, box, text, fnt, fill=TEXT):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2 - 1), text, fill=fill, font=fnt)


def paste_cell(canvas, cell, x, y):
    canvas.paste(cell, (x, y))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x, y, x + CELL[0] - 1, y + CELL[1] - 1], outline=BORDER, width=1)


def compose_scene(scene):
    width = LEFT_LABEL_W + len(METHODS) * CELL[0] + (len(METHODS) - 1) * GAP + PAD * 2
    height = HEADER_H + 2 * CELL[1] + GAP + PAD * 2 + 4
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)

    x0 = PAD + LEFT_LABEL_W
    y_head = PAD
    for i, method in enumerate(METHODS):
        x = x0 + i * (CELL[0] + GAP)
        center_text(draw, (x, y_head, x + CELL[0], y_head + HEADER_H), method["label"], FONT_HEAD)

    y_render = PAD + HEADER_H
    y_depth = y_render + CELL[1] + GAP
    center_text(draw, (PAD, y_render, PAD + LEFT_LABEL_W - 8, y_render + CELL[1]), "Render", FONT_ROW)
    center_text(draw, (PAD, y_depth, PAD + LEFT_LABEL_W - 8, y_depth + CELL[1]), "Depth", FONT_ROW)

    for i, method in enumerate(METHODS):
        x = x0 + i * (CELL[0] + GAP)
        render_path = method["render"](scene)
        if not render_path or not Path(render_path).exists():
            raise FileNotFoundError(f"Missing render for {scene['key']} {method['label']}: {render_path}")
        paste_cell(canvas, fit_image(render_path), x, y_render)

        depth_path = method["depth"](scene)
        if depth_path is None:
            depth = placeholder()
        else:
            if not Path(depth_path).exists():
                raise FileNotFoundError(f"Missing depth for {scene['key']} {method['label']}: {depth_path}")
            depth = fit_image(depth_path) if method.get("depth_mode") == "image" else depth_heatmap(depth_path)
        paste_cell(canvas, depth, x, y_depth)

    out = OUT_DIR / f"{scene['key']}_static_models_depth.png"
    canvas.save(out)
    print(out)


def main():
    for scene in SCENES:
        compose_scene(scene)


if __name__ == "__main__":
    main()
