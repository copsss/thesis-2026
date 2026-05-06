from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageOps


OUT_DIR = Path(r"D:/underwater/thesis-2026/figures/dewater")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEA_ROOT = Path(r"D:/underwater/4DGaussians/output/baseline_seasplat")

SELECTIONS = {
    "robot": {
        "ours": Path(r"D:/underwater/4DGaussians/output/Robot_underwater_v2depth/test/ours_20000"),
        "sea": SEA_ROOT / "Robot_seasplat_eval_seathru_0327025302" / "test",
        "name": "00002.png",
        "sea_name": "0017.JPG",
    },
    "coral": {
        "ours": Path(r"D:/underwater/4DGaussians/output/coral_329_2true/test/ours_20000"),
        "sea": SEA_ROOT / "coral_seasplat_eval_seathru_0327134211" / "test",
        "name": "00001.png",
        "sea_name": "01003.png",
    },
    "streaks": {
        "ours": Path(r"F:/autoresearch/autoresearch-win-rtx/4dGaussians-seasplat/output/streaks_seathru_only_20260424_224458/test/ours_10000"),
        "sea": SEA_ROOT / "streaks_seasplat_eval_seathru_0327142053" / "test",
        "name": "00000.png",
        "sea_name": "04710.png",
    },
}


def read_rgb(path, size=(256, 192)):
    im = Image.open(path).convert("RGB")
    im = ImageOps.fit(im, size, method=Image.Resampling.BILINEAR)
    return np.asarray(im, dtype=np.float32) / 255.0


def psnr(ref, pred):
    mse = float(np.mean((read_rgb(ref) - read_rgb(pred)) ** 2))
    if mse <= 1e-12:
        return 99.0
    return -10.0 * np.log10(mse)


def mean_abs_diff(a, b):
    return float(np.mean(np.abs(read_rgb(a) - read_rgb(b))))


def copy_checked(src, dst):
    if not src.exists() or src.stat().st_size <= 1000:
        raise FileNotFoundError(f"Missing usable image: {src}")
    shutil.copy2(src, dst)


def copy_scene(prefix, cfg):
    name = cfg["name"]
    sea_name = cfg["sea_name"]
    ours = cfg["ours"]
    sea = cfg["sea"]

    gt = ours / "gt" / name
    ours_i = ours / "renders" / name
    ours_j = ours / "no_water" / name
    sea_i = sea / "with_water" / sea_name
    sea_j = sea / "render" / sea_name

    copy_checked(gt, OUT_DIR / f"{prefix}_gt.png")
    copy_checked(sea_i, OUT_DIR / f"{prefix}_sea_I.png")
    copy_checked(sea_j, OUT_DIR / f"{prefix}_sea_J.png")
    copy_checked(ours_i, OUT_DIR / f"{prefix}_ours_I.png")
    copy_checked(ours_j, OUT_DIR / f"{prefix}_ours_J.png")

    ours_psnr = psnr(gt, ours_i)
    sea_psnr = psnr(gt, sea_i)
    ij_diff = mean_abs_diff(ours_i, ours_j)
    print(
        f"{prefix}: {name}, ours_I_PSNR={ours_psnr:.3f}, "
        f"seasplat_I_PSNR={sea_psnr:.3f}, ours_IJ_diff={ij_diff:.4f}"
    )


def main():
    for prefix, cfg in SELECTIONS.items():
        copy_scene(prefix, cfg)
    print("fish: kept existing row")


if __name__ == "__main__":
    main()
