"""Properly re-render ablation (b) and (c) with full UW processing.
Loads Gaussian + UW models exactly as render.py does, but fixes depth saving.
"""
import sys
sys.path.insert(0, 'D:/underwater/4DGaussians')
import torch
import numpy as np
from pathlib import Path
from PIL import Image
from argparse import Namespace
import os

from scene import Scene
from gaussian_renderer import GaussianModel, render, render_depth
from arguments import ModelHiddenParams, PipelineParams
from utils.underwater_utils import normalize_depth_tensor, apply_underwater_models
from deepseecolor.models import BackscatterNetV2, AttenuateNetV3

OUT_BASE = Path(r"D:/underwater/4DGaussians/output")
FIG_AB = Path(r"D:/underwater/thesis-2026/figures/ablation")
TARGET = (480, 360)


def parse_cfg(model_path):
    cfg_path = os.path.join(model_path, 'cfg_args')
    with open(cfg_path, 'rb') as f:
        cfg = f.read().decode('utf-8', errors='replace')
    ns_start = cfg.find('Namespace(')
    return eval(cfg[ns_start:], {'Namespace': Namespace, 'inf': float('inf')})


def build_dataset(opt, model_path):
    from argparse import Namespace as NS
    return NS(
        sh_degree=opt.sh_degree,
        source_path=os.path.join('D:/underwater/4DGaussians', opt.source_path.replace('./', '')),
        model_path=model_path,
        white_background=getattr(opt, 'white_background', True),
        eval=True, images='images', resolution=-1, data_device='cuda',
        llffhold=8, add_points=False, extension='.png', dataloader=False,
        zerostamp_init=False, custom_sampler=None, render_process=True,
    )


def build_hyperparams():
    from argparse import ArgumentParser, Namespace as NS
    dummy = ArgumentParser()
    hp = ModelHiddenParams(dummy).extract(NS(
        kplanes_config={'grid_dimensions': 2, 'input_coordinate_dim': 4,
                        'output_coordinate_dim': 16, 'resolution': [64, 64, 64, 150]},
        multires=[1, 2, 4], net_width=128, timebase_pe=4, defor_depth=1, posebase_pe=10,
        scale_rotation_pe=2, opacity_pe=2, timenet_width=64, timenet_output=32, bounds=1.6,
        plane_tv_weight=0.0002, time_smoothness_weight=0.001, l1_time_planes=0.0001,
        no_dx=False, no_grid=False, no_ds=False, no_dr=False, no_do=True, no_dshs=True,
        empty_voxel=False, grid_pe=0, static_mlp=False, apply_rotation=False,
    ))
    pipe = PipelineParams(dummy).extract(NS(
        convert_SHs_python=False, compute_cov3D_python=False, debug=False,
    ))
    return hp, pipe


def render_and_save(model_path, iteration, out_prefix, view_idx=0):
    """Render view 0 with full UW pipeline, save pre-UW and UW-processed."""
    opt = parse_cfg(model_path)
    dataset = build_dataset(opt, model_path)
    hyperparam, pipeline = build_hyperparams()

    gaussians = GaussianModel(3, hyperparam)
    scene = Scene(dataset, gaussians, load_iteration=iteration, shuffle=False)
    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")

    cam_type = scene.dataset_type
    test_cams = scene.getTestCameras()
    view = test_cams[min(view_idx, len(test_cams) - 1)]

    # Load UW models (same as render.py lines 257-289)
    bs_model, at_model, learned_bg = None, None, None
    bs_path = os.path.join(str(model_path), "backscatter_final.pth")
    at_path = os.path.join(str(model_path), "attenuate_final.pth")
    bg_path = os.path.join(str(model_path), "bg_final.pth")

    if os.path.exists(bs_path) and os.path.exists(at_path) and getattr(opt, 'do_seathru', False):
        bs_model = BackscatterNetV2(
            use_residual=getattr(opt, 'use_bs_residual', False),
            scale=getattr(opt, 'bs_scale', 5.0),
            do_sigmoid=getattr(opt, 'do_sigmoid_bs', False)
        ).cuda()
        at_model = AttenuateNetV3(
            scale=getattr(opt, 'at_scale', 5.0),
            do_sigmoid=getattr(opt, 'do_sigmoid_at', False),
            init_vals=not getattr(opt, 'do_sigmoid_at', False)
        ).cuda()
        bs_model.load_state_dict(torch.load(bs_path, map_location='cuda'))
        at_model.load_state_dict(torch.load(at_path, map_location='cuda'))
        bs_model.eval()
        at_model.eval()

    if os.path.exists(bg_path) and getattr(opt, 'learn_background', False):
        learned_bg = torch.load(bg_path, map_location='cuda')

    print(f"Rendering {model_path.name} iter={iteration}")
    print(f"  Gaussians: {gaussians._xyz.shape[0]} points")
    print(f"  UW: bs={bs_model is not None}, at={at_model is not None}, bg={learned_bg is not None}")

    with torch.no_grad():
        result = render(view, gaussians, pipeline, background, cam_type=cam_type)
        rendering = result["render"]
        clean_J = rendering.clone()

        # Render depth
        depth_pkg = render_depth(view, gaussians, pipeline, background, cam_type=cam_type)
        depth = depth_pkg["render"]
        if depth.dim() == 3 and depth.shape[0] == 3:
            depth = depth[0:1]
        if depth.dim() == 2:
            depth = depth.unsqueeze(0)
        depth = depth.unsqueeze(0)  # [1, 1, H, W]

        # Alpha for depth norm
        alpha = result.get("alpha")
        alpha_for_depth = None
        if alpha is not None and getattr(opt, 'use_alpha_depth_norm', False):
            alpha_for_depth = alpha.unsqueeze(0) if alpha.dim() == 3 else alpha

        depth_norm, stats = normalize_depth_tensor(depth, opt, alpha_tensor=alpha_for_depth)
        print(f"  Depth norm: min={stats['depth_min']:.4f}, max={stats['depth_max']:.4f}, mean={stats['depth_mean']:.4f}")

        uw_rendering, at_map, bs_map = apply_underwater_models(rendering, depth_norm, bs_model, at_model, opt)

        # Apply learned background (matching render.py line 136-139)
        if learned_bg is not None and alpha is not None:
            bg_color_val = torch.sigmoid(learned_bg).reshape(3, 1, 1)
            bg_image = bg_color_val * (1 - alpha)
            uw_rendering = uw_rendering + bg_image
            clean_J = clean_J + bg_image

        clean_J = torch.clamp(clean_J, 0, 1)
        uw_rendering = torch.clamp(uw_rendering, 0, 1)

        print(f"  clean_J:  R=[{clean_J[0].min():.4f},{clean_J[0].max():.4f}] G=[{clean_J[1].min():.4f},{clean_J[1].max():.4f}] B=[{clean_J[2].min():.4f},{clean_J[2].max():.4f}]")
        print(f"  UW out:   R=[{uw_rendering[0].min():.4f},{uw_rendering[0].max():.4f}] G=[{uw_rendering[1].min():.4f},{uw_rendering[1].max():.4f}] B=[{uw_rendering[2].min():.4f},{uw_rendering[2].max():.4f}]")

        # Save UW-processed (main render)
        arr_uw = (uw_rendering.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        Image.fromarray(arr_uw).resize(TARGET, Image.LANCZOS).save(FIG_AB / f"{out_prefix}_render.png")
        print(f"  -> {out_prefix}_render.png")

        # Save clean_J (pre-UW, for comparison)
        arr_clean = (clean_J.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        Image.fromarray(arr_clean).resize(TARGET, Image.LANCZOS).save(FIG_AB / f"{out_prefix}_render_nowater.png")
        print(f"  -> {out_prefix}_render_nowater.png")

        # Save depth viridis heatmap
        import matplotlib.cm as cm
        d_arr = depth_norm.squeeze(0).squeeze(0).cpu().numpy()
        v = 1.0 - d_arr
        rgb = (cm.viridis(v) * 255).astype(np.uint8)[..., :3]
        Image.fromarray(rgb).resize(TARGET, Image.LANCZOS).save(FIG_AB / f"{out_prefix}_depth.png")
        print(f"  -> {out_prefix}_depth.png")


def main():
    render_and_save(OUT_BASE / "Robot_underwater_v2", 20000, "b_seathru")
    render_and_save(OUT_BASE / "Robot_underwater_depth", 14000, "c_depthonly")


if __name__ == "__main__":
    main()
