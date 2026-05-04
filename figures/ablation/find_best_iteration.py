"""Pick the training iteration where the four ablation configurations
diverge most visibly, and use the matching mid-training snapshots as the
a/b/c/d render AND depth tiles for the qualitative ablation figure.

The training-time snapshots in `<run>/finetest_render/images/{iter}_0.jpg`
are 2400x600 montages of [GT | render | depth] for view 0. Both the
middle (render) and rightmost (depth) panels have no text overlay, so we
extract both and use them for the figure tiles.

Configurations:
  (a) plain 4DGS                : output/baseline/Robot
  (b) +SeaThru                  : output/Robot_underwater_v2
  (c) +Depth supervision        : output/Robot_underwater_depth
  (d) Full (SeaThru + Depth)    : output/Robot_underwater_v2depth

Depth tiles: extracted from the rightmost panel of each config's snapshot
at the selected iteration, normalized per-config and mapped to viridis.
"""
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.cm as cm

OUT_BASE = Path(r"D:/underwater/4DGaussians/output")
FIG_AB   = Path(r"D:/underwater/thesis-2026/figures/ablation")
FIG_AB.mkdir(parents=True, exist_ok=True)

TARGET = (480, 360)

CONFIGS = {
    "a": OUT_BASE / "baseline/Robot",
    "b": OUT_BASE / "Robot_underwater_v2",
    "c": OUT_BASE / "Robot_underwater_depth",
    "d": OUT_BASE / "Robot_underwater_v2depth",
}
LABELS = {"a": "plain", "b": "seathru", "c": "depthonly", "d": "full"}


def crop_render_panel(montage_path):
    """Extract the middle (render) panel from a 2400x600 [GT|render|depth] montage."""
    im = Image.open(montage_path).convert("RGB")
    W, H = im.size
    panel_w = W // 3
    return im.crop((panel_w, 0, 2 * panel_w, H))


def crop_depth_panel(montage_path):
    """Extract the rightmost (depth) panel from a 2400x600 [GT|render|depth] montage."""
    im = Image.open(montage_path).convert("RGB")
    W, H = im.size
    panel_w = W // 3
    return im.crop((2 * panel_w, 0, 3 * panel_w, H))


def depth_panel_to_viridis(montage_path, size=TARGET, invert=True):
    """Extract depth panel and convert to viridis heatmap."""
    panel = crop_depth_panel(montage_path)
    arr = np.array(panel)
    # Use first channel as depth (grayscale)
    if arr.ndim == 3:
        depth = arr[..., 0].astype(np.float32)
    else:
        depth = arr.astype(np.float32)
    lo, hi = float(depth.min()), float(depth.max())
    v = np.zeros_like(depth) if hi <= lo else (depth - lo) / (hi - lo)
    if invert:
        v = 1.0 - v
    rgb = (cm.viridis(v) * 255).astype(np.uint8)[..., :3]
    return Image.fromarray(rgb).resize(size, Image.LANCZOS)


def panel_array(montage_path):
    return np.asarray(crop_render_panel(montage_path), dtype=np.float32) / 255.0


def to_viridis(arr2d, size=TARGET, invert=True):
    a = arr2d.astype(np.float32)
    lo, hi = float(a.min()), float(a.max())
    v = np.zeros_like(a) if hi <= lo else (a - lo) / (hi - lo)
    if invert:
        v = 1.0 - v
    rgb = (cm.viridis(v) * 255).astype(np.uint8)[..., :3]
    return Image.fromarray(rgb).resize(size, Image.LANCZOS)


def build_iter_index(stage_subdir):
    """Map iter -> {config_letter: file_path} for snapshots present in all configs."""
    per_cfg = {}
    for k, base in CONFIGS.items():
        d = base / stage_subdir / "images"
        per_cfg[k] = {}
        if not d.is_dir():
            continue
        for f in d.iterdir():
            stem = f.stem
            parts = stem.split("_")
            if len(parts) == 2 and parts[1] == "0":
                try:
                    per_cfg[k][int(parts[0])] = f
                except ValueError:
                    pass
    common = set.intersection(*[set(v.keys()) for v in per_cfg.values()])
    return {it: {k: per_cfg[k][it] for k in CONFIGS} for it in common}


def score_iter(snapshot_paths):
    """Sum of pairwise MAD between the four configs' render panels."""
    imgs = {k: panel_array(p) for k, p in snapshot_paths.items()}
    keys = list(imgs)
    h = min(im.shape[0] for im in imgs.values())
    w = min(im.shape[1] for im in imgs.values())
    for k in keys:
        imgs[k] = imgs[k][:h, :w]
    total = 0.0
    pairs = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            d = float(np.mean(np.abs(imgs[keys[i]] - imgs[keys[j]])))
            pairs[f"{keys[i]}-{keys[j]}"] = d
            total += d
    return total, pairs


def main():
    stage = "finetest_render"
    index = build_iter_index(stage)
    print(f"Common iterations in {stage}: {len(index)} range=[{min(index)},{max(index)}]")

    scored = []
    for it in sorted(index):
        total, pairs = score_iter(index[it])
        scored.append((it, total, pairs))

    scored_sorted = sorted(scored, key=lambda x: -x[1])
    print("\nTop 10 iterations by total pairwise MAD (render panel only):")
    for it, total, pairs in scored_sorted[:10]:
        bd = " ".join(f"{k}={v:.4f}" for k, v in pairs.items())
        print(f"  iter={it:>5d}  total={total:.4f}  [{bd}]")

    # Sweet spot: large divergence AND iter >= 5000 (so the FULL model has
    # mostly converged; the laggards are visibly worse, not just early-stage).
    candidates = [s for s in scored_sorted if s[0] >= 5000]
    if not candidates:
        candidates = scored_sorted
    best_it, best_total, best_pairs = candidates[0]
    bd = " ".join(f"{k}={v:.4f}" for k, v in best_pairs.items())
    print(f"\nSelected iter={best_it}  total MAD={best_total:.4f}  [{bd}]")

    snapshots = index[best_it]
    for tag in ("a", "b", "c", "d"):
        panel = crop_render_panel(snapshots[tag]).resize(TARGET, Image.LANCZOS)
        out = FIG_AB / f"{tag}_{LABELS[tag]}_render.png"
        panel.save(out)
        print(f"  wrote {out.name}  <- {snapshots[tag].relative_to(OUT_BASE)} (middle panel)")

    # Depth tiles: extract right panel from each config's snapshot
    for tag in ("a", "b", "c", "d"):
        depth_img = depth_panel_to_viridis(snapshots[tag], size=TARGET, invert=True)
        out = FIG_AB / f"{tag}_{LABELS[tag]}_depth.png"
        depth_img.save(out)
        print(f"  wrote {out.name}  <- {snapshots[tag].relative_to(OUT_BASE)} (depth panel)")


if __name__ == "__main__":
    main()
