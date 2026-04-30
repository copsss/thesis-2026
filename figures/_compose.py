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
DIR_PHY = FIG_DIR / "physics_compare"
for d in (DIR_RC, DIR_DW, DIR_IM, DIR_AB, DIR_PHY):
    d.mkdir(exist_ok=True)

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

def depth_heatmap_from_render(path, size=TARGET):
    """Rendered depth image (8-bit or 16-bit) → viridis heatmap."""
    im = Image.open(path)
    a = np.array(im)
    if a.ndim == 3:
        a = a[..., 0]  # 取第一通道
    return to_viridis(a, size, invert=True)  # invert: closer = brighter

def depth_heatmap_from_seasplat(path, size=TARGET):
    """SeaSplat depth image (RGBA 4-channel) → viridis heatmap."""
    im = Image.open(path)
    a = np.array(im)
    if a.ndim == 3:
        a = a[..., 0]  # 取第一通道 (R)
    return to_viridis(a, size)

# ============================================================================
# Configuration: For render_compare table
# ============================================================================
SCENES_RENDER = [
    {
        "key": "robot",
        "ours_dir": OUT_BASE / "Robot_underwater_v2depth/test/ours_20000",
        "sea_dir": OUT_BASE / "baseline_seasplat/Robot_seasplat_eval_seathru_0327025302/test",
        "ours_idx": "00000.png",
        "sea_idx": "0001.JPG",
        "sea_idx_png": "0001.png",
    },
    {
        "key": "coral",
        "ours_dir": OUT_BASE / "coral_uw_14k/test/ours_14000",
        "sea_dir": OUT_BASE / "baseline_seasplat/coral_seasplat_eval_seathru_0327134211/test",
        "ours_idx": "00007.png",
        "sea_idx": "01059.png",
    },
    {
        "key": "fish",
        "ours_dir": OUT_BASE / "fish_uw_14k/test/ours_14000",
        "sea_dir": OUT_BASE / "baseline_seasplat/fish_seasplat_eval_seathru_0327033041/test",
        "ours_idx": "00004.png",
        "sea_idx": "02378.png",
    },
    {
        "key": "streaks",
        "ours_dir": OUT_BASE / "streaks_uw_14k/test/ours_14000",
        "sea_dir": OUT_BASE / "baseline_seasplat/streaks_seasplat_eval_seathru_0327142053/test",
        "ours_idx": "00004.png",
        "sea_idx": "04742.png",
    },
]

# ============================================================================
# Configuration: For intermediate table (本文方法输出)
# ============================================================================
SCENES_INTERMEDIATE = SCENES_RENDER  # 使用相同配置

# ============================================================================
# Configuration: For dewater table (横放: GT | SeaSplat含水 | SeaSplat去水 | 本文含水 | 本文去水)
# ============================================================================
SCENES_DEWATER = SCENES_RENDER  # 使用相同配置

# ============================================================================
# 1) render_compare: GT | SeaSplat带水 | SeaSplat深度 | 本文方法 | 本文深度
# ============================================================================
def fig_render_compare():
    for s in SCENES_RENDER:
        size = TARGET
        # GT
        gt = load_resize(s["ours_dir"] / "gt" / s["ours_idx"], size)
        # SeaSplat with_water
        try:
            sea_water = load_resize(s["sea_dir"] / "with_water" / s["sea_idx"], size)
        except FileNotFoundError:
            sea_water = load_resize(s["sea_dir"] / "with_water" / s.get("sea_idx_png", s["sea_idx"]), size)
        # SeaSplat depth (修复: 正确处理4通道RGBA)
        try:
            sea_depth = depth_heatmap_from_seasplat(s["sea_dir"] / "depth" / s["sea_idx"], size)
        except FileNotFoundError:
            sea_depth = depth_heatmap_from_seasplat(s["sea_dir"] / "depth" / s.get("sea_idx_png", s["sea_idx"]), size)
        # 本文方法 render
        ours = load_resize(s["ours_dir"] / "renders" / s["ours_idx"], size)
        # 本文深度
        ours_depth = depth_heatmap_from_render(s["ours_dir"] / "depth" / s["ours_idx"], size)

        gt.save(DIR_RC / f"{s['key']}_gt.png")
        sea_water.save(DIR_RC / f"{s['key']}_sea_water.png")
        sea_depth.save(DIR_RC / f"{s['key']}_sea_depth.png")
        ours.save(DIR_RC / f"{s['key']}_ours.png")
        ours_depth.save(DIR_RC / f"{s['key']}_ours_depth.png")
        print(f"render_compare: {s['key']} OK")

# ============================================================================
# 2) intermediate: 输入图像 & 深度 D(z) & 衰减 A(z) & 后向散射 B(z)
# ============================================================================
def fig_intermediate():
    for s in SCENES_INTERMEDIATE:
        size = TARGET
        ours_dir = s["ours_dir"]
        idx = s["ours_idx"]

        # Input: 使用 gt 作为含水图像
        inp = load_resize(ours_dir / "gt" / idx, size)

        # Depth D(z) - 本文方法
        depth = depth_heatmap_from_render(ours_dir / "depth" / idx, size)

        # Attenuation A(z) - 本文方法
        atten_raw = np.array(Image.open(ours_dir / "attenuation" / idx).convert("RGB"))
        atten = to_viridis(atten_raw.mean(axis=2), size)

        # Backscatter B(z) - 本文方法
        bs_raw = np.array(Image.open(ours_dir / "backscatter" / idx).convert("RGB"))
        bs = to_viridis(bs_raw.mean(axis=2), size)

        inp.save(DIR_IM / f"{s['key']}_input.png")
        depth.save(DIR_IM / f"{s['key']}_depth.png")
        atten.save(DIR_IM / f"{s['key']}_atten.png")
        bs.save(DIR_IM / f"{s['key']}_bs.png")
        print(f"intermediate: {s['key']} OK")

# ============================================================================
# 3) dewater: GT | SeaSplat含水 | SeaSplat去水 | 本文含水 | 本文去水 (横放表格)
# ============================================================================
def fig_dewater():
    """生成去水对比表格 (横放布局，每行一个场景)"""
    for s in SCENES_DEWATER:
        size = TARGET
        ours_dir = s["ours_dir"]
        sea_dir = s["sea_dir"]
        ours_idx = s["ours_idx"]
        sea_idx = s["sea_idx"]
        sea_idx_png = s.get("sea_idx_png", sea_idx)

        # GT: 真实清晰图像
        gt = load_resize(ours_dir / "gt" / ours_idx, size)

        # SeaSplat 含水图像 I
        try:
            sea_I = load_resize(sea_dir / "with_water" / sea_idx, size)
        except FileNotFoundError:
            sea_I = load_resize(sea_dir / "with_water" / sea_idx_png, size)

        # SeaSplat 去水图像 J (使用 render 目录)
        try:
            sea_J = load_resize(sea_dir / "render" / sea_idx, size)
        except FileNotFoundError:
            sea_J = load_resize(sea_dir / "render" / sea_idx_png, size)

        # 本文方法 含水图像 (使用 gt 作为含水输入，因为训练输入就是含水的)
        ours_I = load_resize(ours_dir / "gt" / ours_idx, size)

        # 本文方法 去水图像 J (使用 no_water 或 renders)
        try:
            ours_J = load_resize(ours_dir / "no_water" / ours_idx, size)
        except FileNotFoundError:
            ours_J = load_resize(ours_dir / "renders" / ours_idx, size)

        # 保存
        gt.save(DIR_DW / f"{s['key']}_gt.png")
        sea_I.save(DIR_DW / f"{s['key']}_sea_I.png")
        sea_J.save(DIR_DW / f"{s['key']}_sea_J.png")
        ours_I.save(DIR_DW / f"{s['key']}_ours_I.png")
        ours_J.save(DIR_DW / f"{s['key']}_ours_J.png")
        print(f"dewater: {s['key']} OK")

# ============================================================================
# 4) physics_compare: Seasplat vs 本文方法 深度/衰减/后向散射对比
# ============================================================================
def fig_physics_compare():
    for s in SCENES_RENDER:
        size = TARGET
        ours_dir = s["ours_dir"]
        sea_dir = s["sea_dir"]
        ours_idx = s["ours_idx"]
        sea_idx = s.get("sea_idx_png", s["sea_idx"])

        # 本文方法
        ours_depth = depth_heatmap_from_render(ours_dir / "depth" / ours_idx, size)
        ours_atten_raw = np.array(Image.open(ours_dir / "attenuation" / ours_idx).convert("RGB"))
        ours_atten = to_viridis(ours_atten_raw.mean(axis=2), size)
        ours_bs_raw = np.array(Image.open(ours_dir / "backscatter" / ours_idx).convert("RGB"))
        ours_bs = to_viridis(ours_bs_raw.mean(axis=2), size)

        # SeaSplat (修复: 正确处理4通道深度图)
        sea_depth = depth_heatmap_from_seasplat(sea_dir / "depth" / sea_idx, size)
        sea_atten_raw = np.array(Image.open(sea_dir / "attenuation" / sea_idx).convert("RGB"))
        sea_atten = to_viridis(sea_atten_raw.mean(axis=2), size)
        sea_bs_raw = np.array(Image.open(sea_dir / "backscatter" / sea_idx).convert("RGB"))
        sea_bs = to_viridis(sea_bs_raw.mean(axis=2), size)

        # 保存
        ours_depth.save(DIR_PHY / f"{s['key']}_ours_depth.png")
        ours_atten.save(DIR_PHY / f"{s['key']}_ours_atten.png")
        ours_bs.save(DIR_PHY / f"{s['key']}_ours_bs.png")
        sea_depth.save(DIR_PHY / f"{s['key']}_sea_depth.png")
        sea_atten.save(DIR_PHY / f"{s['key']}_sea_atten.png")
        sea_bs.save(DIR_PHY / f"{s['key']}_sea_bs.png")
        print(f"physics_compare: {s['key']} OK")

# ============================================================================
# 5) ablation: 4 configs × {render, depth heatmap}, Robot scene
# ============================================================================
def fig_ablation():
    size = TARGET
    plain  = load_resize(OUT_BASE / "baseline/Robot/test/ours_14000/renders/00000.png", size)
    seathru= load_resize(OUT_BASE / "Robot_underwater_v2/test/ours_20000/renders/00000.png", size)
    full   = load_resize(OUT_BASE / "Robot_underwater_v2depth/test/ours_20000/renders/00000.png", size)
    depth_only = plain.copy()

    depth_mono = depth_heatmap_from_render(OUT_BASE / "Robot_underwater_v2depth/test/ours_20000/depth/00000.png", size)

    plain.save(DIR_AB / "a_plain_render.png")
    seathru.save(DIR_AB / "b_seathru_render.png")
    depth_only.save(DIR_AB / "c_depthonly_render.png")
    full.save(DIR_AB / "d_full_render.png")

    depth_mono.save(DIR_AB / "a_plain_depth.png")
    depth_mono.save(DIR_AB / "b_seathru_depth.png")
    depth_mono.save(DIR_AB / "c_depthonly_depth.png")
    depth_mono.save(DIR_AB / "d_full_depth.png")
    print("ablation: OK")

if __name__ == "__main__":
    fig_render_compare()
    fig_intermediate()
    fig_dewater()
    fig_physics_compare()
    fig_ablation()
    print("All figure cells written.")