# -*- coding: utf-8 -*-
"""
保守方案：只给特定的学术术语添加 \textit{}
需要处理的术语列表由用户指定
"""

import re

# 需要添加 \textit{} 的术语列表（按优先级排序）
TERMS_TO_ITALICIZE = [
    # 方法名
    'NeRF', '3DGS', '3D Gaussian Splatting', '4DGS', '4D Gaussian Splatting',
    'SeaSplat', 'Sea-Thru', 'SeaThru', 'UDR-GS',
    'Depth Anything', 'Depth Anything V2',
    'HexPlane', 'BackscatterNet', 'AttenuateNet',
    'Mip-NeRF', 'Instant-NGP', 'MERF', 'Nerfies', 'D-NeRF',
    'Dynamic 3D Gaussians', '4DGaussians',
    'WaterSplatting', 'UW-GS', 'SeaFree-GS', 'RecGS', '3D-UIR',
    'DualPhys-GS', 'Aquatic-GS',

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
]

# 按长度降序排序，先匹配长的术语
TERMS_TO_ITALICIZE.sort(key=len, reverse=True)


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changes = []

    for term in TERMS_TO_ITALICIZE:
        # 跳过已经在 \textit{} 中的
        pattern = rf'(?<!\\textit\{{)(?<![a-zA-Z]){re.escape(term)}(?![a-zA-Z])(?!\}})'

        def replace_func(match):
            # 检查上下文，避免在命令参数中替换
            start = max(0, match.start() - 20)
            context_before = content[start:match.start()]

            # 跳过在 \upcite{}, \ref{}, \label{} 等中的
            if '\\upcite{' in context_before and '}' not in context_before.split('\\upcite{')[-1]:
                return match.group(0)
            if any(cmd in context_before for cmd in ['\\ref{', '\\label{', '\\eqref{']):
                return match.group(0)

            return f'\\textit{{{match.group(0)}}}'

        new_content, count = re.subn(pattern, replace_func, content)
        if count > 0:
            changes.append(f"  {term}: {count}处")
            content = new_content

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
