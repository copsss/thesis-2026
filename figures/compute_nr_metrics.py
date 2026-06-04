"""
Compute no-reference (NIQE, BRISQUE, PIQE) and full-reference (PSNR, SSIM, LPIPS)
metrics for ALL models and datasets.
Sources: All_Images_Collection + 4DGaussians/output
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from PIL import Image

# Set proxy before any network operations
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

import pyiqa
import torch

AIC = Path("F:/All_Images_Collection/All_Images_Collection")
OUT = Path("D:/underwater/4DGaussians/output")

# ============================================================================
# DYNAMIC SCENES — 4 scenes: Robot, Coral, Fish, Streaks
# ============================================================================
DYNAMIC_EXP = {}

# --- Ours dynamic (from output/) ---
OURS_DYNAMIC_DIRS = {
    "Robot": OUT / "Robot_underwater_v2depth" / "test" / "ours_20000",
    "Coral": OUT / "coral_uw_14k" / "test" / "ours_14000",
    "Fish": OUT / "fish_uw_14k" / "test" / "ours_14000",
    "Streaks": OUT / "streaks_uw_14k" / "test" / "ours_14000",
}
for scene, d in OURS_DYNAMIC_DIRS.items():
    DYNAMIC_EXP[f"{scene}_Ours"] = {
        "renders": d / "renders",
        "gt": d / "gt",
        "category": "dynamic",
        "scene": scene,
        "method": "Ours",
    }

# --- SeaSplat dynamic baseline (from output/baseline_seasplat) ---
SEASPLAT_DIRS = {
    "Robot": "Robot_seasplat_eval_seathru_0327025302",
    "Coral": "coral_seasplat_eval_seathru_0327134211",
    "Fish": "fish_seasplat_eval_seathru_0327033041",
    "Streaks": "streaks_seasplat_eval_seathru_0327142053",
}
for scene, dname in SEASPLAT_DIRS.items():
    DYNAMIC_EXP[f"{scene}_SeaSplat"] = {
        "renders": OUT / "baseline_seasplat" / dname / "test" / "with_water",
        "gt": AIC / "Dewater_Results_4DGS_SeaSplat" / scene / "test" / "gt",  # shared GT
        "category": "dynamic",
        "scene": scene,
        "method": "SeaSplat",
    }

# --- 4DGS dynamic baseline (from output/baseline) ---
DYNAMIC_EXP["Robot_4DGS"] = {
    "renders": OUT / "baseline" / "Robot" / "test" / "ours_14000" / "renders",
    "gt": OUT / "baseline" / "Robot" / "test" / "ours_14000" / "gt",
    "category": "dynamic",
    "scene": "Robot",
    "method": "4DGS",
}

# ============================================================================
# MODULE ABLATION (Robot only) — a/b/c/d from output/
# ============================================================================
ABLATION_MODULE = {
    "Robot_Abl_a_4DGS": {
        "renders": OUT / "baseline" / "Robot" / "test" / "ours_14000" / "renders",
        "gt": OUT / "baseline" / "Robot" / "test" / "ours_14000" / "gt",
        "label": "(a) 4DGS only",
    },
    "Robot_Abl_b_SeaThru": {
        "renders": OUT / "Robot_underwater_v2" / "test" / "ours_20000" / "renders",
        "gt": OUT / "Robot_underwater_v2" / "test" / "ours_20000" / "gt",
        "label": "(b) +SeaThru",
    },
    "Robot_Abl_c_Depth": {
        "renders": OUT / "Robot_underwater_depth" / "test" / "ours_14000" / "renders",
        "gt": OUT / "Robot_underwater_depth" / "test" / "ours_14000" / "gt",
        "label": "(c) +Depth",
    },
    "Robot_Abl_d_Full": {
        "renders": OUT / "Robot_underwater_v2depth" / "test" / "ours_20000" / "renders",
        "gt": OUT / "Robot_underwater_v2depth" / "test" / "ours_20000" / "gt",
        "label": "(d) Full",
    },
}

# ============================================================================
# TRAINING STRATEGY ABLATION (all 4 dynamic scenes, from All_Images_Collection)
# ============================================================================
ABLATION_TRAINING = {}
for scene in ["Robot", "Coral", "Fish", "Streaks"]:
    ab_dir = AIC / "Ablation_Results" / scene
    if ab_dir.exists():
        for subd in sorted(ab_dir.iterdir()):
            if subd.is_dir() and (subd / "test").exists():
                exp_name = subd.name
                test_dir = subd / "test"
                ABLATION_TRAINING[f"{scene}_{exp_name}"] = {
                    "renders": test_dir,  # images are directly in test/
                    "gt": None,  # ablation has no GT
                    "category": "ablation_training",
                    "scene": scene,
                    "label": exp_name,
                }

# ============================================================================
# STATIC SCENES — 4 scenes: Curasao, IUI3-RedSea, JapaneseGardens, Panama
# ============================================================================
STATIC_EXP = {}

# --- 3DGS static (from All_Images_Collection) ---
for scene in ["Curasao", "IUI3-RedSea", "JapaneseGradens", "Panama"]:
    STATIC_EXP[f"{scene}_3DGS"] = {
        "renders": AIC / "3DGS_Results" / scene / "test" / "ours_30000" / "renders",
        "gt": AIC / "3DGS_Results" / scene / "test" / "ours_30000" / "gt",
        "category": "static",
        "scene": scene,
        "method": "3DGS",
    }

# --- 4DGS static (from All_Images_Collection) ---
for scene in ["Curasao", "IUI3-RedSea", "JapaneseGradens", "Panama"]:
    STATIC_EXP[f"{scene}_4DGS"] = {
        "renders": AIC / "4DGS_Baseline_Results" / scene / "test" / "ours_14000" / "renders",
        "gt": AIC / "4DGS_Baseline_Results" / scene / "test" / "ours_14000" / "gt",
        "category": "static",
        "scene": scene,
        "method": "4DGS",
    }

# --- Ours static (from All_Images_Collection) — no GT in dir, use 4DGS GT ---
for scene in ["Curasao", "IUI3-RedSea", "JapaneseGradens", "Panama"]:
    STATIC_EXP[f"{scene}_Ours"] = {
        "renders": AIC / "Ours_Results" / scene / "test" / "with_water",
        "gt": AIC / "4DGS_Baseline_Results" / scene / "test" / "ours_14000" / "gt",  # shared GT
        "category": "static",
        "scene": scene,
        "method": "Ours",
    }

# --- SeaSplat static (from All_Images_Collection) — no GT in dir, use 4DGS GT ---
for scene in ["Curasao", "IUI3-RedSea", "JapaneseGradens", "Panama"]:
    STATIC_EXP[f"{scene}_SeaSplat"] = {
        "renders": AIC / "SeaSplat_Results" / scene / "test" / "with_water",
        "gt": AIC / "4DGS_Baseline_Results" / scene / "test" / "ours_14000" / "gt",
        "category": "static",
        "scene": scene,
        "method": "SeaSplat",
    }

# --- SeaThru-NeRF (STN) renders — rgb = degraded original (treat as method output) ---
for scene in ["Curasao", "IUI3-RedSea", "JapaneseGradens-RedSea", "Panama"]:
    STATIC_EXP[f"{scene}_STN"] = {
        "renders": AIC / "seathru_renders" / scene / "test" / "rgb",
        "gt": AIC / "4DGS_Baseline_Results" / (scene.replace("-RedSea","")) / "test" / "ours_14000" / "gt",
        "category": "static",
        "scene": scene.replace("-RedSea",""),
        "method": "STN(原图)",
    }


# ============================================================================
# Helper functions
# ============================================================================
def load_images_from_dir(path, max_size=1024):
    if path is None or not path.exists():
        return [], []
    files = sorted([f for f in os.listdir(path)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
    images = []
    for f in files:
        img = Image.open(path / f).convert("RGB")
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        images.append(np.array(img))
    return files, images


def to_batch(images, device="cpu"):
    tensors = []
    for img in images:
        t = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        tensors.append(t)
    return torch.cat(tensors, dim=0).to(device)


def compute_nr_metrics(images, device="cpu"):
    if not images:
        return {}
    batch = to_batch(images, device)
    results = {}
    for name in ["niqe", "brisque", "piqe"]:
        try:
            metric = pyiqa.create_metric(name, device=device)
            results[name.upper()] = float(metric(batch).mean().item())
        except Exception as e:
            print(f"    WARN: {name} failed: {e}")
            results[name.upper()] = float("nan")
    return results


def compute_fr_metrics(renders_list, gt_list, device="cpu"):
    if not renders_list or not gt_list:
        return {}
    # Ensure same count AND same size
    n = min(len(renders_list), len(gt_list))
    matched_r, matched_g = [], []
    for ri, gi in zip(renders_list[:n], gt_list[:n]):
        if ri.shape != gi.shape:
            gi_resized = np.array(Image.fromarray(gi).resize(
                (ri.shape[1], ri.shape[0]), Image.LANCZOS))
            matched_r.append(ri)
            matched_g.append(gi_resized)
        else:
            matched_r.append(ri)
            matched_g.append(gi)
    r_batch = to_batch(matched_r, device)
    g_batch = to_batch(matched_g, device)
    results = {}
    for name in ["psnr", "ssim", "lpips"]:
        try:
            metric = pyiqa.create_metric(name, device=device)
            results[name.upper()] = float(metric(r_batch, g_batch).mean().item())
        except Exception as e:
            print(f"    WARN: {name} failed: {e}")
            results[name.upper()] = float("nan")
    return results


# ============================================================================
# Main
# ============================================================================
def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}\n")

    all_results = {}

    # Merge all experiment dicts
    all_exp = {}
    all_exp.update(DYNAMIC_EXP)
    all_exp.update(ABLATION_MODULE)
    all_exp.update(ABLATION_TRAINING)
    all_exp.update(STATIC_EXP)

    print(f"Total configurations: {len(all_exp)}\n")

    for name, cfg in sorted(all_exp.items()):
        rpath = cfg["renders"]
        gpath = cfg.get("gt")

        if not rpath or not rpath.exists():
            print(f"[SKIP] {name} — renders not found: {rpath}")
            continue

        rfiles, rimages = load_images_from_dir(rpath)
        if not rimages:
            print(f"[SKIP] {name} — no images in {rpath}")
            continue

        print(f"[{name}]  {len(rimages)} images", end="", flush=True)

        nr = compute_nr_metrics(rimages, device)
        print(f"  NIQE={nr.get('NIQE', 'N/A'):.2f}  BRISQUE={nr.get('BRISQUE', 'N/A'):.2f}  PIQE={nr.get('PIQE', 'N/A'):.2f}", end="", flush=True)

        fr = {}
        if gpath and gpath.exists():
            _, gimages = load_images_from_dir(gpath)
            if gimages:
                fr = compute_fr_metrics(rimages, gimages, device)
                if fr:
                    print(f"  |  PSNR={fr.get('PSNR', 'N/A'):.2f}  SSIM={fr.get('SSIM', 'N/A'):.4f}  LPIPS={fr.get('LPIPS', 'N/A'):.4f}", end="")
        print()

        all_results[name] = {
            "nr": nr, "fr": fr, "n_images": len(rimages),
            "category": cfg.get("category", ""),
            "scene": cfg.get("scene", ""),
            "method": cfg.get("method", cfg.get("label", "")),
        }

    # ===== SUMMARY TABLES =====
    print("\n" + "=" * 100)
    print("1. DYNAMIC SCENES — Method Comparison")
    print("=" * 100)
    print(f"{'Scene':<12} {'Method':<10} {'NIQE':>8} {'BRISQUE':>10} {'PIQE':>8}  {'PSNR':>8} {'SSIM':>8} {'LPIPS':>8}")
    print("-" * 100)

    for scene in ["Robot", "Coral", "Fish", "Streaks"]:
        first = True
        for method in ["Ours", "SeaSplat"]:
            key = f"{scene}_Ours" if method == "Ours" else f"{scene}_SeaSplat"
            if key in all_results:
                r = all_results[key]
                label = scene if first else ""
                print(f"{label:<12} {method:<10} {r['nr'].get('NIQE',0):>8.2f} {r['nr'].get('BRISQUE',0):>10.2f} {r['nr'].get('PIQE',0):>8.2f}  {r['fr'].get('PSNR',0):>8.2f} {r['fr'].get('SSIM',0):>8.4f} {r['fr'].get('LPIPS',0):>8.4f}")
                first = False
        # 4DGS only available for Robot
        if scene == "Robot" and "Robot_4DGS" in all_results:
            r = all_results["Robot_4DGS"]
            print(f"{'':12} {'4DGS':<10} {r['nr'].get('NIQE',0):>8.2f} {r['nr'].get('BRISQUE',0):>10.2f} {r['nr'].get('PIQE',0):>8.2f}  {r['fr'].get('PSNR',0):>8.2f} {r['fr'].get('SSIM',0):>8.4f} {r['fr'].get('LPIPS',0):>8.4f}")

    print(f"\n{'='*100}")
    print("2. MODULE ABLATION (Robot) — a/b/c/d")
    print("=" * 100)
    print(f"{'Config':<28} {'NIQE':>8} {'BRISQUE':>10} {'PIQE':>8}  {'PSNR':>8} {'SSIM':>8} {'LPIPS':>8}")
    print("-" * 100)
    for key, cfg in ABLATION_MODULE.items():
        if key in all_results:
            r = all_results[key]
            label = cfg["label"]
            print(f"{label:<28} {r['nr'].get('NIQE',0):>8.2f} {r['nr'].get('BRISQUE',0):>10.2f} {r['nr'].get('PIQE',0):>8.2f}  {r['fr'].get('PSNR',0):>8.2f} {r['fr'].get('SSIM',0):>8.4f} {r['fr'].get('LPIPS',0):>8.4f}")

    print(f"\n{'='*100}")
    print(f"3. TRAINING STRATEGY ABLATION — best config per scene")
    print(f"{'='*100}")
    print(f"{'Scene':<12} {'Config':<38} {'NIQE':>8} {'BRISQUE':>10} {'PIQE':>8}  {'PSNR':>8} {'SSIM':>8} {'LPIPS':>8}")
    print("-" * 100)
    for scene in ["Robot", "Coral", "Fish", "Streaks"]:
        scene_results = [(k, v) for k, v in all_results.items()
                         if v.get("category") == "ablation_training" and v.get("scene") == scene]
        if scene_results:
            # Sort by BRISQUE (lower is better) to show best first
            scene_results.sort(key=lambda x: x[1]["nr"].get("BRISQUE", 999))
            # Show best + worst
            best = scene_results[0]
            worst = scene_results[-1]
            bcfg = ABLATION_TRAINING.get(best[0], {})
            print(f"{scene:<12} [BEST] {best[0]:<30} {best[1]['nr'].get('NIQUE',0):>8.2f} {best[1]['nr'].get('BRISQUE',0):>10.2f} {best[1]['nr'].get('PIQE',0):>8.2f}")
            if len(scene_results) > 1:
                wcfg = ABLATION_TRAINING.get(worst[0], {})
                print(f"{'':12} [WORST]{worst[0]:<30} {worst[1]['nr'].get('NIQE',0):>8.2f} {worst[1]['nr'].get('BRISQUE',0):>10.2f} {worst[1]['nr'].get('PIQE',0):>8.2f}")
            # Show all
            for k, v in scene_results[1:-1]:
                print(f"{'':12}        {k:<30} {v['nr'].get('NIQE',0):>8.2f} {v['nr'].get('BRISQUE',0):>10.2f} {v['nr'].get('PIQE',0):>8.2f}")

    print(f"\n{'='*100}")
    print("4. STATIC SCENES — Method Comparison")
    print("=" * 100)
    print(f"{'Scene':<18} {'Method':<10} {'NIQE':>8} {'BRISQUE':>10} {'PIQE':>8}  {'PSNR':>8} {'SSIM':>8} {'LPIPS':>8}")
    print("-" * 100)

    static_scene_labels = {"Curasao": "Curasao", "IUI3-RedSea": "IUI3-RedSea",
                           "JapaneseGradens": "JapaneseGardens", "Panama": "Panama"}
    static_methods = ["STN(原图)", "3DGS", "4DGS", "SeaSplat", "Ours"]

    for scene in ["Curasao", "IUI3-RedSea", "JapaneseGradens", "Panama"]:
        label = static_scene_labels.get(scene, scene)
        first = True
        for method in static_methods:
            if method == "STN(原图)":
                stn_scene = scene if scene != "JapaneseGradens" else "JapaneseGradens-RedSea"
                key = f"{stn_scene}_STN"
            else:
                key = f"{scene}_{method}"
            if key in all_results:
                r = all_results[key]
                slabel = label if first else ""
                print(f"{slabel:<18} {method:<10} {r['nr'].get('NIQE',0):>8.2f} {r['nr'].get('BRISQUE',0):>10.2f} {r['nr'].get('PIQE',0):>8.2f}  {r['fr'].get('PSNR',0):>8.2f} {r['fr'].get('SSIM',0):>8.4f} {r['fr'].get('LPIPS',0):>8.4f}")
                first = False

    # Save
    out_path = Path("D:/underwater/thesis-2026/figures/nr_metrics_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nFull results saved to: {out_path}")


if __name__ == "__main__":
    main()
