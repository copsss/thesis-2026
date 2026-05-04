"""Save right (depth) panel of all 4 configs at iter 13399 to inspect."""
from PIL import Image
from pathlib import Path

ITER = 13399
CONFIGS = [
    ("a", "baseline/Robot"),
    ("b", "Robot_underwater_v2"),
    ("c", "Robot_underwater_depth"),
    ("d", "Robot_underwater_v2depth"),
]
OUT = Path(r"D:/underwater/thesis-2026/figures/ablation/_depthcheck")
OUT.mkdir(exist_ok=True)
for tag, sub in CONFIGS:
    p = Path(rf"D:/underwater/4DGaussians/output/{sub}/finetest_render/images/{ITER}_0.jpg")
    im = Image.open(p)
    W, H = im.size
    pw = W // 3
    right = im.crop((2 * pw, 0, 3 * pw, H))
    right.save(OUT / f"{tag}_depth_raw.png")
print("done")
