from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:/All_Images_Collection/All_Images_Collection")
DATA_ROOT = Path(r"D:/underwater/4DGaussians/data/SeaThru-NeRF/SeathruNeRF_dataset2")
OUT_DIR = Path(r"D:/underwater/thesis-2026/figures/static_multimethod")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FNAME = "MTN_1090.png"
CELL = (360, 270)
HEADER_H = 46
LEFT_LABEL_W = 72
PAD = 10
GAP = 8
BG = (255, 255, 255)
TEXT = (25, 25, 25)


ORIGINAL = DATA_ROOT / "JapaneseGradens-RedSea" / "images_wb" / FNAME
COLUMNS = [
    (
        "Original",
        ORIGINAL,
        ORIGINAL,
    ),
    (
        "STN",
        ROOT / "seathru_renders" / "JapaneseGradens-RedSea" / "test" / "rgb" / FNAME,
        ROOT / "seathru_renders" / "JapaneseGradens-RedSea" / "test" / "J" / FNAME,
    ),
    (
        "SeaSplat",
        ROOT / "SeaSplat_Results" / "JapaneseGradens" / "test" / "with_water" / FNAME,
        ROOT / "SeaSplat_Results" / "JapaneseGradens" / "test" / "render" / FNAME,
    ),
    (
        "Ours",
        ROOT / "Ours_Results" / "JapaneseGradens" / "test" / "with_water" / FNAME,
        ROOT / "Ours_Results" / "JapaneseGradens" / "test" / "render" / FNAME,
    ),
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


FONT_HEAD = font(22, True)
FONT_ROW = font(20, True)


def center_text(draw, box, text, fnt):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2 - 1), text, fill=TEXT, font=fnt)


def fit_image(path):
    if not path.exists():
        raise FileNotFoundError(path)
    im = Image.open(path).convert("RGB")
    im = ImageOps.contain(im, CELL, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", CELL, BG)
    canvas.paste(im, ((CELL[0] - im.width) // 2, (CELL[1] - im.height) // 2))
    return canvas


def main():
    width = PAD * 2 + LEFT_LABEL_W + len(COLUMNS) * CELL[0] + (len(COLUMNS) - 1) * GAP
    height = PAD * 2 + HEADER_H + CELL[1] * 2 + GAP
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)

    x0 = PAD + LEFT_LABEL_W
    y_render = PAD + HEADER_H
    y_dewater = y_render + CELL[1] + GAP
    center_text(draw, (PAD, y_render, PAD + LEFT_LABEL_W - 6, y_render + CELL[1]), "Render", FONT_ROW)
    center_text(draw, (PAD, y_dewater, PAD + LEFT_LABEL_W - 6, y_dewater + CELL[1]), "Dewater", FONT_ROW)

    for i, (label, render_path, dewater_path) in enumerate(COLUMNS):
        x = x0 + i * (CELL[0] + GAP)
        center_text(draw, (x, PAD, x + CELL[0], PAD + HEADER_H), label, FONT_HEAD)
        canvas.paste(fit_image(render_path), (x, y_render))
        canvas.paste(fit_image(dewater_path), (x, y_dewater))

    out = OUT_DIR / "japanese_dewater_render_compare.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
