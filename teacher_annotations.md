# PDF Annotation Extraction

File: 2213624-申祖铭-面向扰动环境下的水下场景新视角合成-修改意见.pdf

Total annotations: 31

## 1. Page 3 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

中文篇幅写到半页，研究意义多写一点

Selected text:

摘
要

## 2. Page 3 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

和实验结果不一致

Selected text:

实验结果表明，本文方法在多个动态水下场景上取得了优于现有基线的渲染质
量，验证了各组件的有效性与互补性。

## 3. Page 8 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

同上

Selected text:

效
[赵大鹏2023 水下]

## 4. Page 8 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

格式问题校正
参考文献未有对应论文，AI生成的？
严禁用AI生成不存在的问题，请仔细检查

Selected text:

景
[张杰2020 水下机器人, 李建平2019 海洋]

## 5. Page 8 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

校正

Selected text:

了”

## 6. Page 9 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

添加一段这个章节的介绍脉络

Selected text:

第二节
国内外研究现状

## 7. Page 9 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

双引号格式

Selected text:

大量” 浮空” 伪

## 8. Page 13 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

公式下不需要空一行，另外公式后面也需要标点符号

Selected text:

将Σ 分解为缩放矩阵与旋转矩阵的组合形式：

## 9. Page 13 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

R^T,

Selected text:

R⊤

## 10. Page 13 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

不需要缩进
其中，

Selected text:

其中

## 11. Page 13 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

请查看原文，仔细核对相关技术介绍是否准确，目前已发现多处公式不对。
疑是AI生成的

Selected text:

第二章
相关技术基础

## 12. Page 14 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

同上，后文不在赘述

Selected text:

Σ′ = JWΣW⊤J⊤
(2.3)
其中W 为视图变换矩阵，J 为射影变换的仿射近似雅可比矩阵。

## 13. Page 17 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

中文命名

Selected text:

BackscatterNet 网

## 14. Page 17 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

同上

Selected text:

2
AttenuateNet

## 15. Page 20 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

为何要进行两阶段训练策略，动机或缘由说清楚

Selected text:

两阶段训练策略

## 16. Page 22 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

请添加一个方法的overview或者pipeline示意图

Selected text:

第三章
系统设计与实现

## 17. Page 23 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

符号表述不统一

Selected text:

，输出干净场景颜色图J ∈RH×W×3

## 18. Page 24 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

同上，仔细检查比好多表示

Selected text:

射颜色图B(Z)：
Bc(Z) = sigmoid(B∞
c )·
�
1−exp(−β B
c ·Z)
�

## 19. Page 26 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

那里在哪体现呢，消融也没有提现到，为什么要分怎么多步的训练呢
划分依据是什么

Selected text:

分阶段训练策略是本系统应对多组件联合优化不稳定性的核心创新。当水
下网络、变形网络与高斯点集同时从零开始优化时，三者之间存在严重的梯度
干扰：水下网络若过早引入，会将颜色偏差错误地归因于几何结构，导致高斯
几何收敛至错误形态。为此，本系统将训练流程划分为五个连续的阶段，分别

## 20. Page 29 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

可分别加数据集的示意图

Selected text:

4.1.2
数据集

## 21. Page 31 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

psnr不需要单独为一小节，和4.2.2作为定量实验分析

Selected text:

PSNR 定量对比

## 22. Page 32 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

请添加改数据集的可视化结果

Selected text:

（SeaThru-NeRF
[12] 数据集）

## 23. Page 35 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

深度图

Selected text:

的深度热力图。

## 24. Page 35 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

具体指的是什么，重建的GT还增强后的GT

Selected text:

真实参考图像（GT）

## 25. Page 36 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

为何本文和本文UIE结果大差不差，根本就没有增强效果

Selected text:

四个动态水下场景的去水效果对

## 26. Page 38 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

4.6.3-4.6.6的分析如何得到的，AI纯生成的吗，一句在哪

Selected text:

4.6.3
Robot 场景

## 27. Page 40 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

并不直观，没问题的话，可以吧差异的内容用过红框突出出来，abcd下标放在图下

Selected text:

图4.4以Robot 场景为例，给出四种消融配置的渲染效果以及对应的深度热
力图，可直观观察各模块对场景外观与几何重建的影响。

## 28. Page 40 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

突然冒出来的特征分类，依据是什么。分桶是什么呢

Selected text:

明确的适用边界，本文建议将水下场景按” 浑浊度—散射类型—运动复杂度” 三
维特征分桶，按桶选择方法配置。

## 29. Page 42 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

缺少期刊

Selected text:

Thomas Müller, Alex Evans, Christoph Schied, et al. Instant neural graphics
primitives with a multiresolution hash encoding. In: 2022: 1–15.

## 30. Page 42 - Highlight

Author: jieyu_yuan

Subject: 在文本上注释

Comment:

请仔细检查参考文献引用格式。确保文献真实性。里面有很多篇论文的作者，与题目或期刊对应不上。至少一半是有问题的
这涉及到学术态度问题，请严肃对待！！！

Selected text:

参考文献

## 31. Page 43 - Highlight

Author: jieyu_yuan

Subject: 高亮

Comment:

这是我们团队的论文，连这个的引用错了。

Selected text:

Chi Chen et al. 3D-UIR: 3D Gaussian for underwater 3D scene reconstruction
via physics-based appearance-medium decoupling. In: arXiv preprint, 2024.

