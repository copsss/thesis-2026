"""Render clean_J (pre-UW) for config (d) Robot_underwater_v2depth."""
import sys
sys.path.insert(0, 'D:/underwater/4DGaussians')
import torch
import numpy as np
from pathlib import Path
from PIL import Image
from argparse import Namespace
import os

from scene import Scene
from gaussian_renderer import GaussianModel, render
from arguments import ModelHiddenParams, PipelineParams

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


def main():
    model_path = OUT_BASE / "Robot_underwater_v2depth"
    opt = parse_cfg(str(model_path))
    dataset = build_dataset(opt, str(model_path))
    hyperparam, pipeline = build_hyperparams()

    gaussians = GaussianModel(3, hyperparam)
    scene = Scene(dataset, gaussians, load_iteration=20000, shuffle=False)
    background = torch.tensor([1, 1, 1], dtype=torch.float32, device="cuda")
    cam_type = scene.dataset_type
    view = scene.getTestCameras()[0]

    # Load learned bg
    learned_bg = None
    bg_path = os.path.join(str(model_path), "bg_final.pth")
    if os.path.exists(bg_path) and getattr(opt, 'learn_background', False):
        learned_bg = torch.load(bg_path, map_location='cuda')
        print(f"Loaded bg: sigmoid(bg)={torch.sigmoid(learned_bg).data}")

    with torch.no_grad():
        result = render(view, gaussians, pipeline, background, cam_type=cam_type)
        clean_J = result["render"].clone()

        # Apply learned bg
        alpha = result.get("alpha")
        if learned_bg is not None and alpha is not None:
            bg_color_val = torch.sigmoid(learned_bg).reshape(3, 1, 1)
            bg_image = bg_color_val * (1 - alpha)
            clean_J = clean_J + bg_image

        clean_J = torch.clamp(clean_J, 0, 1)

        print(f"clean_J (d): R=[{clean_J[0].min():.4f},{clean_J[0].max():.4f}] G=[{clean_J[1].min():.4f},{clean_J[1].max():.4f}] B=[{clean_J[2].min():.4f},{clean_J[2].max():.4f}]")

        arr = (clean_J.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        Image.fromarray(arr).resize(TARGET, Image.LANCZOS).save(FIG_AB / "d_full_render_nowater.png")
        print("Saved d_full_render_nowater.png")


if __name__ == "__main__":
    main()
