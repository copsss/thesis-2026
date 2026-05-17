"""One-shot slicer: extract per-cell sub-images from the composed
static_multimethod PNGs so they can be referenced individually in the
chapter4.tex tabular layout (dewater-style).

Geometry matches compose_static_multimethod.py and
compose_static_japanese_dewater.py:
    PAD=10, LEFT_LABEL_W=96, HEADER_H=62, CELL=(360, 270), GAP=8.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent / "static_multimethod"
OUT_ROOT = ROOT / "cells"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

PAD = 10
LEFT_LABEL_W = 96
HEADER_H = 62
CELL_W, CELL_H = 360, 270
GAP = 8


def col_x(i: int) -> int:
    return PAD + LEFT_LABEL_W + i * (CELL_W + GAP)


Y_RENDER = PAD + HEADER_H
Y_DEPTH = Y_RENDER + CELL_H + GAP


SCENES_5COL = [
    ("curacao", "curacao_static_models_depth.png"),
    ("iui3_redsea", "iui3_redsea_static_models_depth.png"),
    ("japanese_gardens", "japanese_gardens_static_models_depth.png"),
    ("panama", "panama_static_models_depth.png"),
]
METHODS_5 = ["orig", "stn", "seasplat", "fdgs", "ours"]

DEWATER_SRC = "japanese_dewater_render_compare.png"
METHODS_4 = ["orig", "stn", "seasplat", "ours"]


def crop_cell(im: Image.Image, col: int, y: int) -> Image.Image:
    x = col_x(col)
    return im.crop((x, y, x + CELL_W, y + CELL_H))


def slice_5col(scene_key: str, src_name: str) -> None:
    src = ROOT / src_name
    if not src.exists():
        raise FileNotFoundError(src)
    im = Image.open(src).convert("RGB")
    out_dir = OUT_ROOT / scene_key
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, m in enumerate(METHODS_5):
        crop_cell(im, i, Y_RENDER).save(out_dir / f"render_{m}.png")
        crop_cell(im, i, Y_DEPTH).save(out_dir / f"depth_{m}.png")
    print(f"[ok] {scene_key}: 10 cells -> {out_dir}")


def slice_dewater() -> None:
    src = ROOT / DEWATER_SRC
    if not src.exists():
        raise FileNotFoundError(src)
    im = Image.open(src).convert("RGB")
    out_dir = OUT_ROOT / "japanese_dewater"
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, m in enumerate(METHODS_4):
        crop_cell(im, i, Y_RENDER).save(out_dir / f"render_{m}.png")
        crop_cell(im, i, Y_DEPTH).save(out_dir / f"dewater_{m}.png")
    print(f"[ok] japanese_dewater: 8 cells -> {out_dir}")


def main() -> None:
    for key, name in SCENES_5COL:
        slice_5col(key, name)
    slice_dewater()


if __name__ == "__main__":
    main()
