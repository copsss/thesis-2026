from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


DATA_ROOT = Path(r"D:/underwater/4DGaussians/data/SeaThru-NeRF/SeathruNeRF_dataset2")
OUT_DIR = Path(r"D:/underwater/thesis-2026/figures/dataset_samples")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CELL = (420, 300)
HEADER_H = 42
GAP = 10
PAD = 12
BG = (255, 255, 255)
TEXT = (25, 25, 25)


SCENES = [
    ("Curasao", "Curasao", "MTN_1288.png"),
    ("IUI3-RedSea", "IUI3-RedSea", "MTN_5894.png"),
    ("JapaneseGardens-RedSea", "JapaneseGradens-RedSea", "MTN_1090.png"),
    ("Panama", "Panama", "MTN_1529.png"),
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


def center_text(draw, box, text, fnt):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2 - 1), text, fill=TEXT, font=fnt)


def fit_image(path):
    im = Image.open(path).convert("RGB")
    im = ImageOps.contain(im, CELL, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", CELL, BG)
    canvas.paste(im, ((CELL[0] - im.width) // 2, (CELL[1] - im.height) // 2))
    return canvas


def main():
    width = PAD * 2 + len(SCENES) * CELL[0] + (len(SCENES) - 1) * GAP
    height = PAD * 2 + HEADER_H + CELL[1]
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)

    for i, (label, scene_dir, fname) in enumerate(SCENES):
        x = PAD + i * (CELL[0] + GAP)
        center_text(draw, (x, PAD, x + CELL[0], PAD + HEADER_H), label, FONT_HEAD)
        image_path = DATA_ROOT / scene_dir / "images_wb" / fname
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        canvas.paste(fit_image(image_path), (x, PAD + HEADER_H))

    out = OUT_DIR / "static_seathru_samples.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
