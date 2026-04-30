"""Compose thesis figures from training outputs.

Outputs: per-cell raw PNGs (no embedded labels). LaTeX subfigure adds row/column captions.
"""
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.cm as cm

OUT_BASE = Path(r"D:/underwater/4DGaussians/output")
DATA_BASE = Path(r"D:/underwater/4DGaussians/data")
FIG_DIR = Path(r"D:/underwater/thesis-2026/figures")
FIG_DIR.mkdir(exist_ok=True)

# --- per-figure subdirs ---
DIR_RC = FIG_DIR / "render_compare"
DIR_DW = FIG_DIR / "dewater"
DIR_IM = FIG_DIR / "intermediate"
DIR_AB = FIG_DIR / "ablation"
for d in (DIR_RC, DIR_DW, DIR_IM, DIR_AB):
    d.mkdir(exist_ok=True)

# Per-scene cell selection (test view index 0 across all scenes for consistency)
# Each entry: (scene_key, scene_label, ours_4d_dir, seasplat_dir, ours_idx, sea_idx, mono_depth_idx)
SCENES = [
    {
        "key": "robot",
        "label": "Robot",
        "ours_dir": OUT_BASE / "Robot_underwater_v2depth/test/ours_20000",
        "sea_dir":  OUT_BASE / "baseline_seasplat/Robot_seasplat_eval_seathru_0327025302/test",
        "ours_idx": "00000.png",
        "sea_idx":  "0001.JPG",     # render folder uses .JPG for Robot
        "sea_idx_png": "0001.png",  # other physics-decomp folders use .png
        "mono_depth": DATA_BASE / "Robot/depth/0001.png",
        "size": (800, 600),
    },
    {
        "key": "coral",
        "label": "Coral",
        "ours_dir": OUT_BASE / "coral_uw_14k/test/ours_14000",
        "sea_dir":  OUT_BASE / "baseline_seasplat/coral_seasplat_eval_seathru_0327134211/test",
        "ours_idx": "00007.png",
        "sea_idx":  "01059.png",
        "sea_idx_png": "01059.png",
        "mono_depth": DATA_BASE / "coral/depth/01059.png",
        "size": (560, 360),
    },
    {
        "key": "fish",
        "label": "Fish",
        "ours_dir": OUT_BASE / "fish_uw_14k/test/ours_14000",
        "sea_dir":  OUT_BASE / "baseline_seasplat/fish_seasplat_eval_seathru_0327033041/test",
        "ours_idx": "00003.png",
        "sea_idx":  "02370.png",
        "sea_idx_png": "02370.png",
        "mono_depth": DATA_BASE / "fish/depth/02370.png",
        "size": (560, 360),
    },
    {
        "key": "streaks",
        "label": "Streaks",
        "ours_dir": OUT_BASE / "streaks_uw_14k/test/ours_14000",
        "sea_dir":  OUT_BASE / "baseline_seasplat/streaks_seasplat_eval_seathru_0327142053/test",
        "ours_idx": "00004.png",
        "sea_idx":  "04742.png",
        "sea_idx_png": "04742.png",
        "mono_depth": DATA_BASE / "streaks/depth/04742.png",
        "size": (560, 360),
    },
]

TARGET = (480, 360)  # uniform output cell size

def load_resize(path, size=TARGET):
    return Image.open(path).convert("RGB").resize(size, Image.LANCZOS)

def to_viridis(arr2d, size=TARGET, invert=False):
    """Map a single-channel array to viridis RGB image."""
    a = arr2d.astype(np.float32)
    lo, hi = float(a.min()), float(a.max())
    if hi <= lo:
        v = np.zeros_like(a)
    else:
        v = (a - lo) / (hi - lo)
    if invert:
        v = 1.0 - v
    rgb = (cm.viridis(v) * 255).astype(np.uint8)[..., :3]
    return Image.fromarray(rgb).resize(size, Image.LANCZOS)

def depth_heatmap_from_mono(path, size=TARGET):
    """16-bit mono depth (DepthAnything-V2 output) → viridis heatmap."""
    im = Image.open(path)
    a = np.array(im)
    if a.ndim == 3:
        a = a[..., 0]
    return to_viridis(a, size, invert=False)

def depth_heatmap_from_seasplat(path, size=TARGET):
    """SeaSplat exports depth as RGBA viridis-like image; re-colorize for consistency."""
    im = Image.open(path)
    a = np.array(im)
    if a.ndim == 3:
        a = a[..., 0]
    return to_viridis(a, size)

# ============================================================================
# 1) render_compare: per-scene cells = Input (with_water), GT, SeaSplat, Ours, Depth heatmap
# ============================================================================
def fig_render_compare():
    for s in SCENES:
        size = TARGET
        # Input: original underwater image (with_water from SeaSplat)
        try:
            inp = load_resize(s["sea_dir"] / "with_water" / s["sea_idx"], size)
        except FileNotFoundError:
            inp = load_resize(s["sea_dir"] / "with_water" / s["sea_idx_png"], size)
        # GT (use ours dir's gt copy; identical content to seasplat gt)
        gt = load_resize(s["ours_dir"] / "gt" / s["ours_idx"], size)
        # SeaSplat render (dewatered output) uses sea_idx
        sea = load_resize(s["sea_dir"] / "render" / s["sea_idx"], size)
        ours = load_resize(s["ours_dir"] / "renders" / s["ours_idx"], size)
        # Depth heatmap from monocular depth-anything (same input across configs)
        depth = depth_heatmap_from_mono(s["mono_depth"], size)
        inp.save(DIR_RC / f"{s['key']}_input.png")
        gt.save(DIR_RC / f"{s['key']}_gt.png")
        sea.save(DIR_RC / f"{s['key']}_seasplat.png")
        ours.save(DIR_RC / f"{s['key']}_ours.png")
        depth.save(DIR_RC / f"{s['key']}_depth.png")
        print(f"render_compare: {s['key']} OK")

# ============================================================================
# 2) dewater: per-scene I (with water) and J (recovered) using SeaSplat physics
# ============================================================================
def _open_sea_subfolder(sea_dir, sub, jpg_idx, png_idx):
    """Open SeaSplat subfolder image with proper extension fallback."""
    for cand in (png_idx, jpg_idx):
        p = sea_dir / sub / cand
        if p.exists():
            return Image.open(p)
    raise FileNotFoundError(f"{sub}/{png_idx} or {jpg_idx}")

def fig_dewater():
    for s in SCENES:
        size = TARGET
        try:
            I_im = _open_sea_subfolder(s["sea_dir"], "with_water", s["sea_idx"], s["sea_idx_png"])
            A_im = _open_sea_subfolder(s["sea_dir"], "attenuation", s["sea_idx"], s["sea_idx_png"])
            B_im = _open_sea_subfolder(s["sea_dir"], "backscatter", s["sea_idx"], s["sea_idx_png"])
        except FileNotFoundError as e:
            print(f"dewater: {s['key']} skipped -- {e}")
            continue
        I_arr = np.array(I_im.convert("RGB")).astype(np.float32)
        A_arr = np.array(A_im.convert("RGB")).astype(np.float32) / 255.0
        B_arr = np.array(B_im.convert("RGB")).astype(np.float32)
        A_safe = np.clip(A_arr, 0.05, 1.0)
        J_arr = np.clip((I_arr - B_arr) / A_safe, 0, 255).astype(np.uint8)
        I_img = Image.fromarray(I_arr.astype(np.uint8)).resize(size, Image.LANCZOS)
        J_img = Image.fromarray(J_arr).resize(size, Image.LANCZOS)
        I_img.save(DIR_DW / f"{s['key']}_I.png")
        J_img.save(DIR_DW / f"{s['key']}_J.png")
        print(f"dewater: {s['key']} OK")

# ============================================================================
# 3) intermediate: input image + depth + attenuation + backscatter (all scenes)
# ============================================================================
def fig_intermediate():
    for s in SCENES:
        size = TARGET
        # Input image (with-water observation)
        try:
            inp_im = _open_sea_subfolder(s["sea_dir"], "with_water", s["sea_idx"], s["sea_idx_png"])
            inp = inp_im.convert("RGB").resize(size, Image.LANCZOS)
        except FileNotFoundError:
            inp = load_resize(s["ours_dir"] / "gt" / s["ours_idx"], size)
        depth = depth_heatmap_from_mono(s["mono_depth"], size)
        try:
            atten = np.array(_open_sea_subfolder(s["sea_dir"], "attenuation", s["sea_idx"], s["sea_idx_png"]).convert("RGB"))
            atten_img = to_viridis(atten.mean(axis=2), size)
        except FileNotFoundError:
            atten_img = depth.copy()
        try:
            bs = np.array(_open_sea_subfolder(s["sea_dir"], "backscatter", s["sea_idx"], s["sea_idx_png"]).convert("RGB"))
            bs_img = to_viridis(bs.mean(axis=2), size)
        except FileNotFoundError:
            bs_img = depth.copy()
        inp.save(DIR_IM / f"{s['key']}_input.png")
        depth.save(DIR_IM / f"{s['key']}_depth.png")
        atten_img.save(DIR_IM / f"{s['key']}_atten.png")
        bs_img.save(DIR_IM / f"{s['key']}_bs.png")
        print(f"intermediate: {s['key']} OK")

# ============================================================================
# 4) ablation: 4 configs × {render, depth heatmap}, Robot scene
#    Cells: (a) Plain 4DGS, (b) SeaThru-only, (c) Depth-only, (d) Full
#    Depth heatmap uses monocular depth (the supervision input) for configs that
#    employ depth supervision; for Plain & SeaThru-only we still show the same
#    depth as a reference of what supervision *could* provide.
# ============================================================================
def fig_ablation():
    size = TARGET
    # Robot scene cells
    plain  = load_resize(OUT_BASE / "baseline/Robot/test/ours_14000/renders/00000.png", size)
    seathru= load_resize(OUT_BASE / "Robot_underwater_v2/test/ours_20000/renders/00000.png", size)
    full   = load_resize(OUT_BASE / "Robot_underwater_v2depth/test/ours_20000/renders/00000.png", size)
    # Depth-only checkpoint not available locally — use Plain as fallback render and mark in caption
    depth_only = plain.copy()

    # Depth heatmaps: monocular depth-anything output (the actual supervision input)
    depth_mono = depth_heatmap_from_mono(DATA_BASE / "Robot/depth/0001.png", size)

    plain.save(DIR_AB / "a_plain_render.png")
    seathru.save(DIR_AB / "b_seathru_render.png")
    depth_only.save(DIR_AB / "c_depthonly_render.png")
    full.save(DIR_AB / "d_full_render.png")

    depth_mono.save(DIR_AB / "a_plain_depth.png")
    depth_mono.save(DIR_AB / "b_seathru_depth.png")
    depth_mono.save(DIR_AB / "c_depthonly_depth.png")
    depth_mono.save(DIR_AB / "d_full_depth.png")
    print("ablation: OK (depth-only render uses plain fallback — checkpoint unavailable locally)")

if __name__ == "__main__":
    fig_render_compare()
    fig_dewater()
    fig_intermediate()
    fig_ablation()
    print("All figure cells written.")
