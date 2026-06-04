"""为消融配置 (b) Robot_underwater_v2 和 (c) Robot_underwater_depth
单独渲染相机空间 Z 深度（不经过水下深度归一化）。

原因：这两个配置启用了 SeaThru 但没有深度监督，normalize_depth_tensor
把深度全部推到 255，导致深度图完全不可用。

方案：加载 Gaussian 模型，仅用 render_depth 获取原始 Z-buffer 深度，
用 min/max 归一化（与 baseline 无 UW 时的处理一致）。
"""
import sys
sys.path.insert(0, r"D:/underwater/4DGaussians")

import torch
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.cm as cm

from scene import Scene
from gaussian_renderer import GaussianModel, render_depth
from arguments import ModelHiddenParams, PipelineParams
from arguments import ModelParams, PipelineParams, ModelHiddenParams

OUT_BASE = Path(r"D:/underwater/4DGaussians/output")
TARGET = (480, 360)


def render_depth_z_normalized(model_path, iteration, view_idx=0):
    """Render raw Z-buffer depth for view 0, normalize by min/max."""
    import os

    # Read cfg_args file
    cfg_path = os.path.join(str(model_path), "cfg_args")
    with open(cfg_path, 'rb') as f:
        cfg_content = f.read().decode('utf-8', errors='replace')

    # Parse cfg_args to get proper dataset params (eval the Namespace)
    cfg_content_clean = cfg_content.replace('\n', ' ').strip()
    # Extract the Namespace(...) part
    ns_start = cfg_content_clean.find('Namespace(')
    from argparse import Namespace
    cfg_ns = eval(cfg_content_clean[ns_start:], {"Namespace": Namespace, "inf": float('inf')})

    # Construct dataset namespace from cfg_args values
    from argparse import Namespace as NS
    dataset = NS(
        sh_degree=cfg_ns.sh_degree,
        source_path=os.path.join(r"D:/underwater/4DGaussians", cfg_ns.source_path.replace('./', '')),
        model_path=str(model_path),
        white_background=getattr(cfg_ns, 'white_background', True),
        eval=getattr(cfg_ns, 'eval', True),
        images=getattr(cfg_ns, 'images', 'images'),
        resolution=getattr(cfg_ns, 'resolution', -1),
        data_device=getattr(cfg_ns, 'data_device', 'cuda'),
        # Scene.__init__ needs these
        llffhold=getattr(cfg_ns, 'llffhold', 8),
        add_points=getattr(cfg_ns, 'add_points', False),
        extension=getattr(cfg_ns, 'extension', '.png'),
        dataloader=getattr(cfg_ns, 'dataloader', False),
        zerostamp_init=getattr(cfg_ns, 'zerostamp_init', False),
        custom_sampler=getattr(cfg_ns, 'custom_sampler', None),
        render_process=getattr(cfg_ns, 'render_process', True),
    )

    from argparse import ArgumentParser, Namespace as NS2
    dummy_parser = ArgumentParser()
    hyperparam = ModelHiddenParams(dummy_parser).extract(NS2(
        kplanes_config={'grid_dimensions': 2, 'input_coordinate_dim': 4, 'output_coordinate_dim': 16,
                        'resolution': [64, 64, 64, 150]},
        multires=[1, 2, 4], net_width=128, timebase_pe=4, defor_depth=1, posebase_pe=10,
        scale_rotation_pe=2, opacity_pe=2, timenet_width=64, timenet_output=32, bounds=1.6,
        plane_tv_weight=0.0002, time_smoothness_weight=0.001, l1_time_planes=0.0001,
        no_dx=False, no_grid=False, no_ds=False, no_dr=False, no_do=True, no_dshs=True,
        empty_voxel=False, grid_pe=0, static_mlp=False, apply_rotation=False,
    ))
    pipeline = PipelineParams(dummy_parser).extract(NS2(
        convert_SHs_python=False, compute_cov3D_python=False, debug=False,
    ))

    gaussians = GaussianModel(3, hyperparam)
    scene = Scene(dataset, gaussians, load_iteration=iteration, shuffle=False)
    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    cam_type = scene.dataset_type
    test_cameras = scene.getTestCameras()

    if view_idx >= len(test_cameras):
        view_idx = 0

    view = test_cameras[view_idx]
    cam = scene.getTrainCameras()[0] if len(scene.getTrainCameras()) > 0 else view

    print(f"  Scene: {model_path.name}, iter={iteration}, view {view_idx}/{len(test_cameras)}")
    print(f"  Gaussians: {gaussians._xyz.shape[0]} points")

    with torch.no_grad():
        depth_pkg = render_depth(view, gaussians, pipeline, background, cam_type=cam_type)
        depth = depth_pkg["render"]  # [3, H, W] or [1, H, W]
        if depth.dim() == 3 and depth.shape[0] == 3:
            depth = depth[0:1]
        if depth.dim() == 2:
            depth = depth.unsqueeze(0)
        depth = depth.squeeze(0)  # [H, W]

        # Simple min/max normalization (same as render.py else-branch)
        valid = torch.isfinite(depth)
        if valid.any():
            d_min = depth[valid].min()
            d_max = depth[valid].max()
            depth_norm = torch.where(valid, depth, d_max)
            depth_norm = (depth_norm - d_min) / (d_max - d_min + 1e-6)
        else:
            depth_norm = torch.zeros_like(depth)

        depth_vis = depth_norm.repeat(3, 1, 1)  # [3, H, W]

        # Convert to PIL
        arr = (depth_vis.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        return Image.fromarray(arr)


def save_viridis_heatmap(depth_img, out_path):
    """Convert grayscale depth to viridis heatmap."""
    a = np.array(depth_img)
    if a.ndim == 3:
        a = a[..., 0]
    arr = a.astype(np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi <= lo:
        v = np.zeros_like(arr)
    else:
        v = (arr - lo) / (hi - lo)
    v = 1.0 - v
    rgb = (cm.viridis(v) * 255).astype(np.uint8)[..., :3]
    img = Image.fromarray(rgb).resize(TARGET, Image.LANCZOS)
    img.save(out_path)
    return img


def main():
    configs = {
        "b": {
            "model_path": OUT_BASE / "Robot_underwater_v2",
            "iteration": 20000,
        },
        "c": {
            "model_path": OUT_BASE / "Robot_underwater_depth",
            "iteration": 14000,
        },
    }

    FIG_AB = Path(r"D:/underwater/thesis-2026/figures/ablation")

    for tag, info in configs.items():
        print(f"\nRendering Z-depth for ({tag})...")
        depth_img = render_depth_z_normalized(info["model_path"], info["iteration"])

        # Save as PNG
        out_path = FIG_AB / f"{tag}_{'seathru' if tag=='b' else 'depthonly'}_depth.png"
        save_viridis_heatmap(depth_img, out_path)

        # Verify
        a = np.array(Image.open(out_path))
        print(f"  Saved: {out_path.name}")
        print(f"  shape={a.shape}, range=[{a.min()},{a.max()}], unique={len(np.unique(a))}")


if __name__ == "__main__":
    main()
