# -*- coding: utf-8 -*-
"""
移除之前脚本添加的 \textit{} 标记
保留数学模式中原本的 \textit{}
"""

import re

# 本次添加 \textit{} 的术语列表（需要移除的）
TERMS_TO_REMOVE_ITALIC = [
    # 方法名
    'NeRF', '3DGS', '3D Gaussian Splatting', '4DGS', '4D Gaussian Splatting',
    'SeaSplat', 'Sea-Thru', 'SeaThru', 'UDR-GS',
    'Depth Anything', 'Depth Anything V2',
    'HexPlane', 'BackscatterNet', 'AttenuateNet',
    'Mip-NeRF', 'Instant-NGP', 'MERF', 'Nerfies', 'D-NeRF',
    'Dynamic 3D Gaussians', '4DGaussians',
    'WaterSplatting', 'UW-GS', 'SeaFree-GS', 'RecGS', '3D-UIR',
    'DualPhys-GS', 'Aquatic-GS', 'WaterSplatting',

    # 技术术语
    'MLP', 'CNN', 'RNN', 'LSTM', 'GRU', 'Transformer',
    'ReLU', 'Sigmoid', 'Tanh', 'Softmax', 'BatchNorm', 'LayerNorm',
    'Adam', 'SGD', 'RMSprop', 'AdamW',
    'PSNR', 'SSIM', 'LPIPS', 'MSE', 'MAE', 'RMSE',
    'GPU', 'CPU', 'TPU', 'CUDA', 'OpenGL', 'Vulkan',
    'RGB', 'RGBA', 'HSV', 'HSL', 'YCbCr', 'CIE',

    # 数学符号和术语
    'PDF', 'CDF', 'MAP', 'MLE', 'EM', 'KL', 'JS',
    'GAN', 'VAE', 'AE', 'CVAE', 'Diffusion', 'Flow',

    # 数据集和基准
    'ImageNet', 'COCO', 'CIFAR', 'MNIST', 'KITTI', 'NYU',
    'SeaThru-NeRF', 'ScanNet', 'ModelNet', 'ShapeNet',

    # 其他学术术语
    'SfM', 'SLAM', 'COLMAP', 'OpenCV', 'Open3D', 'PyTorch', 'TensorFlow',
    'AUV', 'ROV', 'DCP', 'TV', 'SSIM', 'LPIPS',

    # 作者人名
    'Mildenhall', 'McGlamery', 'Akkaynak', 'Treibitz', 'Pumarola',
    'Kerbl', 'Barron', 'Muller', 'Reiser', 'Park', 'Luiten', 'Levy',
    'Jaffe', 'Wu', 'Cao', 'Yang', 'Wang', 'Zhang', 'Chen', 'Sun', 'Li',
    'He',

    # 其他术语
    'Neural Radiance Field', 'Tile-based',
]

# 按长度降序排序，避免部分匹配
TERMS_TO_REMOVE_ITALIC.sort(key=len, reverse=True)


def remove_italic_from_term(content, term):
    """从特定术语中移除 \textit{}"""
    pattern = rf'\\textit\{{{re.escape(term)}\}}'
    new_content, count = re.subn(pattern, term, content)
    return new_content, count


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    for term in TERMS_TO_REMOVE_ITALIC:
        new_content, count = remove_italic_from_term(content, term)
        if count > 0:
            changes.append(f"  {term}: {count}处")
            content = new_content

    # 额外处理：移除连续出现的 \textit{英文单词} 模式
    # 如 \textit{由} 或 \textit{等人} 等（这些是中文，不应有 \textit）
    # 但保留数学符号如 \textit{$...$} 中的内容

    if changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已处理 {filepath}:")
        for c in changes:
            print(c)
    else:
        print(f"无需修改 {filepath}")


def main():
    files = [
        'chapter1.tex', 'chapter2.tex', 'chapter3.tex',
        'chapter4.tex', 'chapter5.tex', 'abstract.tex',
    ]

    for filename in files:
        filepath = f'D:/underwater/thesis-2026/{filename}'
        try:
            process_file(filepath)
        except Exception as e:
            print(f"错误 {filepath}: {e}")


if __name__ == '__main__':
    main()
