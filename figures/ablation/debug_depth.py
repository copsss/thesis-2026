"""Debug normalize_depth_tensor to understand why depth becomes all-255."""
import sys
sys.path.insert(0, 'D:/underwater/4DGaussians')
import torch
from pathlib import Path
from argparse import Namespace
import os

from scene import Scene
from gaussian_renderer import GaussianModel, render, render_depth
from arguments import ModelHiddenParams, PipelineParams
from utils.underwater_utils import normalize_depth_tensor

model_path = 'D:/underwater/4DGaussians/output/Robot_underwater_depth'

# Read cfg_args
cfg_path = os.path.join(model_path, 'cfg_args')
with open(cfg_path, 'rb') as f:
    cfg = f.read().decode('utf-8', errors='replace')
ns_start = cfg.find('Namespace(')
opt = eval(cfg[ns_start:], {'Namespace': Namespace, 'inf': float('inf')})

print(f"opt.norm_depth_max = {getattr(opt, 'norm_depth_max', 'N/A')}")
print(f"opt.normalize_depth = {getattr(opt, 'normalize_depth', 'N/A')}")
print(f"opt.filter_depth = {getattr(opt, 'filter_depth', 'N/A')}")
print(f"opt.depth_norm_strategy = {getattr(opt, 'depth_norm_strategy', 'N/A')}")
print(f"opt.use_gt_depth_supervision = {getattr(opt, 'use_gt_depth_supervision', 'N/A')}")

# Construct dataset
from argparse import Namespace as NS
dataset = NS(
    sh_degree=opt.sh_degree,
    source_path=os.path.join('D:/underwater/4DGaussians', opt.source_path.replace('./', '')),
    model_path=model_path,
    white_background=getattr(opt, 'white_background', True),
    eval=True, images='images', resolution=-1, data_device='cuda',
    llffhold=8, add_points=False, extension='.png', dataloader=False,
    zerostamp_init=False, custom_sampler=None, render_process=True,
)

from argparse import ArgumentParser
dummy = ArgumentParser()
hyperparam = ModelHiddenParams(dummy).extract(NS(
    kplanes_config={'grid_dimensions': 2, 'input_coordinate_dim': 4, 'output_coordinate_dim': 16, 'resolution': [64, 64, 64, 150]},
    multires=[1, 2, 4], net_width=128, timebase_pe=4, defor_depth=1, posebase_pe=10,
    scale_rotation_pe=2, opacity_pe=2, timenet_width=64, timenet_output=32, bounds=1.6,
    plane_tv_weight=0.0002, time_smoothness_weight=0.001, l1_time_planes=0.0001,
    no_dx=False, no_grid=False, no_ds=False, no_dr=False, no_do=True, no_dshs=True,
    empty_voxel=False, grid_pe=0, static_mlp=False, apply_rotation=False,
))
pipeline = PipelineParams(dummy).extract(NS(
    convert_SHs_python=False, compute_cov3D_python=False, debug=False,
))

gaussians = GaussianModel(3, hyperparam)
scene = Scene(dataset, gaussians, load_iteration=14000, shuffle=False)
bg = torch.tensor([1,1,1], dtype=torch.float32, device='cuda')
cam_type = scene.dataset_type
view = scene.getTestCameras()[0]

with torch.no_grad():
    depth_pkg = render_depth(view, gaussians, pipeline, bg, cam_type=cam_type)
    depth = depth_pkg['render']
    print(f'\nRaw depth from render_depth: shape={depth.shape}, dtype={depth.dtype}')
    print(f'  min={depth.min():.4f}, max={depth.max():.4f}, mean={depth.mean():.4f}')
    print(f'  n_finite={torch.isfinite(depth).sum()}/{depth.numel()}')

    # Check for nan/inf
    n_nan = torch.isnan(depth).sum().item()
    n_inf = torch.isinf(depth).sum().item()
    print(f'  n_nan={n_nan}, n_inf={n_inf}')

    # Mimic render.py preprocessing
    if depth.dim() == 3 and depth.shape[0] == 3:
        depth = depth[0:1]
    if depth.dim() == 2:
        depth = depth.unsqueeze(0)
    depth = depth.unsqueeze(0)  # [1,1,H,W]

    print(f'\nBefore normalize_depth_tensor: shape={depth.shape}, min={depth.min():.4f}, max={depth.max():.4f}')

    depth_norm, stats = normalize_depth_tensor(depth, opt)
    print(f'\nAfter normalize_depth_tensor: shape={depth_norm.shape}, min={depth_norm.min():.6f}, max={depth_norm.max():.6f}')
    print(f'Stats: {stats}')

    d_vis = depth_norm.squeeze(0)
    print(f'depth_vis: shape={d_vis.shape}, min={d_vis.min():.6f}, max={d_vis.max():.6f}, n_unique={len(d_vis.unique())}')

    # Also check what happens without normalize_depth_tensor (simple min-max)
    d_simple = depth.squeeze(0)
    valid = torch.isfinite(d_simple)
    if valid.any():
        d_min = d_simple[valid].min()
        d_max = d_simple[valid].max()
        d_simple_norm = torch.where(valid, d_simple, d_max)
        d_simple_norm = (d_simple_norm - d_min) / (d_max - d_min + 1e-6)
        print(f'\nSimple min-max norm: min={d_simple_norm.min():.6f}, max={d_simple_norm.max():.6f}')

    # Now check the render too
    result = render(view, gaussians, pipeline, bg, cam_type=cam_type)
    rendering = result['render']
    print(f'\nClean render (pre-UW): shape={rendering.shape}, R=[{rendering[0].min():.4f},{rendering[0].max():.4f}], G=[{rendering[1].min():.4f},{rendering[1].max():.4f}], B=[{rendering[2].min():.4f},{rendering[2].max():.4f}]')
