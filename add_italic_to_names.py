# -*- coding: utf-8 -*-
"""
为论文中的作者人名添加 \textit{} 标记
"""

import re

# 需要添加 \textit{} 的作者人名列表（按长度降序，避免部分匹配）
AUTHOR_NAMES = [
    # 多音节姓（优先匹配）
    'Mildenhall', 'McGlamery', 'Akkaynak', 'Treibitz', 'Pumarola',
    'Kerbl', 'Barron', 'Muller', 'Reiser', 'Park', 'Luiten', 'Levy',
    'Jaffe', 'Wu', 'Cao', 'Yang', 'Wang', 'Zhang', 'Chen', 'Sun', 'Li',
    # 单音节（最后处理，避免误匹配）
    'He',
]


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = []

    for name in AUTHOR_NAMES:
        # 匹配规则：
        # 1. 前面不是 \textit{ （避免重复添加）
        # 2. 前面不是其他字母（避免匹配部分单词）
        # 3. 后面不是字母（避免匹配部分单词）
        # 4. 后面可以跟 "等人" 或 " et al." 或直接跟 \upcite

        pattern = rf'(?<!\\textit\{{)(?<![a-zA-Z]){re.escape(name)}(?![a-zA-Z])'

        def replace_func(match):
            matched_text = match.group(0)
            start = max(0, match.start() - 30)
            context_before = content[start:match.start()]

            # 特殊情况：He 需要更严格的检查
            if matched_text == 'He':
                # 检查上下文，确保是作者引用而非"他"
                # 如果后面跟 \upcite 或 "等人" 或 "et al"，则认为是人名
                end = min(len(content), match.end() + 30)
                context_after = content[match.end():end]

                # 检查是否在引用上下文中
                if '\\upcite' not in context_after and '等人' not in context_after and 'et al' not in context_after:
                    # 可能不是人名，检查前面是否有其他线索
                    if '由' not in context_before and '作者' not in context_before:
                        return matched_text  # 不处理

            # 检查是否在命令参数中（如 \upcite{he2011dcp}）
            if '\\upcite{' in context_before and '}' not in context_before.split('\\upcite{')[-1]:
                return matched_text

            # 检查是否在 \ref{}, \label{} 等中
            if any(cmd in context_before for cmd in ['\\ref{', '\\label{', '\\eqref{', '\\pageref{', '\\nameref{']):
                return matched_text

            return f'\\textit{{{matched_text}}}'

        new_content, count = re.subn(pattern, replace_func, content)
        if count > 0:
            changes.append(f"  {name}: {count}处")
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
