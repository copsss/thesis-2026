#!/usr/bin/env python3
"""
生成消融实验对比图（用于论文）
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_comparison_grid():
    """创建对比网格图"""

    base_dir = "D:/underwater/thesis-2026/figures/ablation_stages"

    # 定义对比组 (实验名, 显示标签, 图像路径)
    comparisons = [
        # Robot场景对比
        {
            "dataset": "Robot",
            "configs": [
                ("no_stages_robot", "0 warmup", "test/00000.png"),
                ("no_stages_robot", "200 iter", "test/00000.png"),  # 需要确认实际路径
                ("warmup_robot", "500 iter + coarse/fine", "test/00000.png"),
            ]
        },
    ]

    # 创建大图
    cell_w, cell_h = 400, 300
    margin = 20
    label_h = 40

    for comp in comparisons:
        dataset = comp["dataset"]
        configs = comp["configs"]

        n_cols = len(configs)
        n_rows = 1

        total_w = n_cols * cell_w + (n_cols + 1) * margin
        total_h = n_rows * cell_h + label_h + 2 * margin

        canvas = Image.new('RGB', (total_w, total_h), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", 16)
            font_title = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            font_title = ImageFont.load_default()

        # 绘制标题
        draw.text((margin, margin//2), f"{dataset}场景训练策略对比", fill=(0,0,0), font=font_title)

        for idx, (exp_name, label, img_path) in enumerate(configs):
            x = margin + idx * (cell_w + margin)
            y = margin + label_h

            # 加载图像
            full_path = os.path.join(base_dir, exp_name, img_path)
            if os.path.exists(full_path):
                img = Image.open(full_path)
                img = img.resize((cell_w, cell_h), Image.LANCZOS)
                canvas.paste(img, (x, y))

                # 添加标签
                label_y = y - label_h + 10
                draw.text((x, label_y), label, fill=(0,0,0), font=font)
            else:
                # 绘制占位符
                draw.rectangle([x, y, x+cell_w, y+cell_h], outline=(200,200,200), width=2)
                draw.text((x+10, y+cell_h//2), f"Image not found:\n{img_path}", fill=(150,0,0), font=font)

        # 保存
        output_path = os.path.join(base_dir, f"{dataset}_comparison.png")
        canvas.save(output_path, dpi=(300, 300))
        print(f"Saved: {output_path}")

def create_summary_table_image():
    """创建PSNR对比表格图"""

    from PIL import Image, ImageDraw, ImageFont

    # 表格数据
    data = [
        ["训练配置", "Robot", "Fish", "Coral", "Streaks"],
        ["0 warmup", "14.62", "13.30", "10.75", "13.57"],
        ["200 iter warmup", "25.98", "26.68", "13.82", "20.58"],
        ["500 iter + coarse/fine", "26.35", "26.63", "24.15", "28.91"],
    ]

    # 计算尺寸
    cell_h = 40
    col_w = [200, 100, 100, 100, 100]
    total_w = sum(col_w) + 100
    total_h = len(data) * cell_h + 80

    img = Image.new('RGB', (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
        font_title = ImageFont.truetype("arialbd.ttf", 18)
    except:
        font = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # 标题
    draw.text((20, 20), "表：训练策略消融实验（PSNR / dB）", fill=(0,0,0), font=font_title)

    # 绘制表格
    y_start = 60
    for row_idx, row in enumerate(data):
        y = y_start + row_idx * cell_h

        # 行背景
        if row_idx == 0:
            draw.rectangle([20, y, total_w-20, y+cell_h], fill=(230, 230, 230))
        elif row_idx == len(data) - 1:
            draw.rectangle([20, y, total_w-20, y+cell_h], fill=(240, 255, 240))

        # 绘制单元格
        x = 20
        for col_idx, cell in enumerate(row):
            w = col_w[col_idx]

            # 边框
            draw.rectangle([x, y, x+w, y+cell_h], outline=(0,0,0), width=1)

            # 文字
            f = font_bold if row_idx == 0 or col_idx == 0 else font
            text_w = draw.textlength(cell, font=f)
            text_x = x + (w - text_w) // 2
            text_y = y + (cell_h - 16) // 2
            draw.text((text_x, text_y), cell, fill=(0,0,0), font=f)

            x += w

    # 保存
    output_path = "D:/underwater/thesis-2026/figures/ablation/ablation_psnr_table.png"
    img.save(output_path, dpi=(300, 300))
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    print("Creating comparison figures...")
    create_comparison_grid()
    create_summary_table_image()
    print("Done!")
