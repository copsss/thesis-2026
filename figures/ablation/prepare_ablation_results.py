#!/usr/bin/env python3
"""
将消融实验结果整理到论文目录
"""

import os
import shutil
import json
from pathlib import Path

# 源目录
SOURCE_DIR = "D:/All_Images_Collection/All_Images_Collection/Ablation_Results"
# 目标目录
TARGET_DIR = "D:/underwater/thesis-2026/figures/ablation_stages"

def copy_experiment_results():
    """复制消融实验结果到论文目录"""

    os.makedirs(TARGET_DIR, exist_ok=True)

    # 定义要复制的关键实验（每个数据集选一个代表性实验）
    key_experiments = {
        "Robot": [
            ("ablation_minimal_warmup_robot", "warmup_robot"),
            ("ablation_no_stages_robot_v3", "no_stages_robot"),
        ],
        "Fish": [
            ("ablation_no_stages_fish_v3", "no_stages_fish"),
        ],
        "Coral": [
            ("ablation_no_stages_coral_v3", "no_stages_coral"),
        ],
        "Streaks": [
            ("ablation_no_coarse_fine_streaks", "no_coarse_streaks"),
            ("ablation_no_stages_streaks_v3", "no_stages_streaks"),
        ]
    }

    summary = {
        "experiments": [],
        "total_train_images": 0,
        "total_test_images": 0
    }

    for dataset, experiments in key_experiments.items():
        for exp_name, display_name in experiments:
            exp_dir = os.path.join(SOURCE_DIR, dataset, exp_name)
            if not os.path.exists(exp_dir):
                print(f"跳过 {exp_name}: 目录不存在")
                continue

            # 创建目标目录
            target_exp_dir = os.path.join(TARGET_DIR, display_name)
            os.makedirs(f"{target_exp_dir}/train", exist_ok=True)
            os.makedirs(f"{target_exp_dir}/test", exist_ok=True)

            # 复制图像
            train_dir = os.path.join(exp_dir, "train")
            test_dir = os.path.join(exp_dir, "test")

            train_count = 0
            if os.path.exists(train_dir):
                for f in os.listdir(train_dir):
                    if f.endswith('.png'):
                        shutil.copy(os.path.join(train_dir, f),
                                  os.path.join(target_exp_dir, "train", f))
                        train_count += 1

            test_count = 0
            if os.path.exists(test_dir):
                for f in os.listdir(test_dir):
                    if f.endswith('.png'):
                        shutil.copy(os.path.join(test_dir, f),
                                  os.path.join(target_exp_dir, "test", f))
                        test_count += 1

            # 读取实验信息
            info_file = os.path.join(exp_dir, "experiment_info.json")
            if os.path.exists(info_file):
                with open(info_file, 'r') as f:
                    info = json.load(f)
            else:
                info = {}

            summary["experiments"].append({
                "name": exp_name,
                "display_name": display_name,
                "dataset": dataset,
                "train_images": train_count,
                "test_images": test_count,
                "info": info
            })
            summary["total_train_images"] += train_count
            summary["total_test_images"] += test_count

            print(f"{display_name}: train={train_count}, test={test_count}")

    # 保存摘要
    with open(os.path.join(TARGET_DIR, "summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n总计: {summary['total_train_images']} 张训练图像, {summary['total_test_images']} 张测试图像")
    print(f"结果保存至: {TARGET_DIR}")

if __name__ == "__main__":
    copy_experiment_results()
