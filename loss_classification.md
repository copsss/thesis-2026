# 论文损失函数分类与梯度回传分析

> 基于代码 `D:\underwater\4DGaussians\train.py` 与 `arguments\underwater\default.py`，
> 对应论文 chapter3.tex 中式 \eqref{eq:lossfull} 的 8 项损失。

## 一、优化对象（梯度可流入的模块）

系统中存在的可学习参数集合：

| 简称 | 模块 | 内容 |
|---|---|---|
| **GS-geo** | 高斯几何参数 | $\boldsymbol{\mu}$（位置）、$\boldsymbol{\Sigma}$（尺度+旋转）、$\alpha$（不透明度） |
| **GS-col** | 高斯颜色参数 | DC 项 + SH 系数 $\mathbf{f}$（默认 SH=0，仅 DC） |
| **Def** | 变形网络 | HexPlane 多分辨率特征 + MLP，仅在精细阶段激活 |
| **BS** | BackscatterNet | $B_c^\infty$ 与后向散射衰减系数 $\beta_c^B$ |
| **AT** | AttenuateNet | 直接透射衰减系数 $\beta_c^D$ |

**渲染数据流：**

```
GS → Def → 光栅化 → (J, Z) → BS(Z), AT(Z) → I = J ⊙ A(Z) + B(Z)
```

- GS-geo 同时影响 **J、Z、α**
- GS-col 只影响 **J**
- Def 在精细阶段对 J 与 Z 都有影响

---

## 二、损失分类与梯度流

### 类别 1：重建损失监督（驱动整体颜色/几何对齐）

| 论文符号 | 代码位置 | 形式 | 梯度回传 |
|---|---|---|---|
| $\mathcal{L}_1$ | `train.py:400`/`414` | $\lVert I - I^{\mathrm{gt}}\rVert_1$，$I$=水下合成图 | **GS-geo, GS-col, Def, BS, AT**（全链路） |
| $\mathcal{L}_{\text{D-SSIM}}$ | `train.py:401`/`414` | $1-\text{SSIM}(I, I^{\mathrm{gt}})$ | 同上 |

> 这是唯一**同时回传到水下网络与高斯参数**的"主干光度损失"，
> 是水下模块、几何、颜色联合优化的核心驱动信号。
> 粗训练阶段水下模块未启用，$I=J$，此时回传仅作用于 GS 与 Def。

### 类别 2：单目深度监督（约束几何）

| 论文符号 | 代码位置 | 形式 | 梯度回传 |
|---|---|---|---|
| $\mathcal{L}_{\text{mono}}$ | `train.py:342`/`421-432` | 归一化逆深度的 alpha 加权 L1：$\frac{\sum \alpha\lvert\tilde d_{\text{render}}-\tilde d_{\text{mono}}\rvert}{\sum \alpha+\epsilon}$ | **GS-geo（主要 $\boldsymbol{\mu}_z$、$\alpha$）、Def** |

> $d_{\text{mono}}$ 为预存常量（无梯度），仅 $d_{\text{render}}$ 一侧产生梯度；
> 该损失**不经过水下模块**，因此不会流向 BS/AT。

### 类别 3：水下物理先验损失（约束 J 为干净外观、约束水体网络合理性）

| 论文符号 | 代码位置 | 作用对象 | detach 处理 | 梯度回传 |
|---|---|---|---|---|
| $\mathcal{L}_{\text{dark}}$（暗通道先验） | `train.py:585-599` | $\hat{\mathbf{J}}=\mathbf{I}^{\mathrm{gt}}-B(Z_{\text{detach}})$ 上的暗通道 | `gt.detach()`、`Z.detach()` | **仅 BS**（$B$ 中的可学习参数仍带梯度） |
| $\mathcal{L}_{\text{gray}}$（灰世界） | `train.py:509-535` | 渲染图 $\mathbf{J}$ 的逐通道均值 | 默认走 `image_tensor` 路径 | **GS-col, Def**（J 的颜色端） |
| $\mathcal{L}_{\text{sat}}$（RGB 饱和度） | `train.py:548-559` | 惩罚 $\mathbf{J}$ 中越界像素 | 无 detach | **GS-col, Def**，少量到 GS-geo（透过光栅化权重） |
| $\mathcal{L}_{\text{bg}}$（Alpha 背景） | `train.py:475-494` | 让相机前方水柱区域的 $\alpha$ 与背景色一致 | 渲染图、bg、$B^\infty$ 全部 detach | **仅 GS-geo（$\alpha$，及 $\boldsymbol{\mu},\boldsymbol{\Sigma}$ 通过 alpha 合成）** |
| $\mathcal{L}_{\text{smooth}}$（深度平滑） | `train.py:464-473` | 边缘感知深度平滑：图像梯度引导的 $\nabla Z$ 正则 | gt 用作权重无梯度，$Z$ 不 detach | **GS-geo（$\boldsymbol{\mu}_z$）、Def** |

---

## 三、整体梯度流总结表

| 损失 | GS-geo | GS-col | Def | BS | AT |
|---|:-:|:-:|:-:|:-:|:-:|
| $\mathcal{L}_1$ | ✔ | ✔ | ✔ | ✔ | ✔ |
| $\mathcal{L}_{\text{D-SSIM}}$ | ✔ | ✔ | ✔ | ✔ | ✔ |
| $\mathcal{L}_{\text{mono}}$ | ✔ | – | ✔ | – | – |
| $\mathcal{L}_{\text{smooth}}$ | ✔ | – | ✔ | – | – |
| $\mathcal{L}_{\text{dark}}$ | – | – | – | ✔ | – |
| $\mathcal{L}_{\text{gray}}$ | – | ✔ | ✔ | – | – |
| $\mathcal{L}_{\text{sat}}$ | (弱) | ✔ | ✔ | – | – |
| $\mathcal{L}_{\text{bg}}$ | ✔（$\alpha$ 主导） | – | – | – | – |

---

## 四、可直接写入论文的段落（建议放在 §3.5 末尾）

> 按梯度回传路径，式 \eqref{eq:lossfull} 中的损失可分为三类：
>
> **（1）主干重建监督**（$\mathcal{L}_1$ 与 $\mathcal{L}_{\text{D-SSIM}}$），其梯度沿 $\mathbf{I}=\mathbf{J}\odot A(\mathbf{Z})+B(\mathbf{Z})$ 的合成路径同时回传至高斯参数、变形网络与水下网络（BS、AT），是各模块联合优化的核心驱动；
>
> **（2）几何先验监督**（$\mathcal{L}_{\text{mono}}$ 与 $\mathcal{L}_{\text{smooth}}$），约束渲染深度 $\mathbf{Z}$，其梯度仅作用于高斯几何与变形网络，不涉及水下网络；
>
> **（3）水下物理先验**（$\mathcal{L}_{\text{dark}}$、$\mathcal{L}_{\text{gray}}$、$\mathcal{L}_{\text{sat}}$、$\mathcal{L}_{\text{bg}}$），其中 $\mathcal{L}_{\text{dark}}$ 通过 $\mathbf{I}^{\mathrm{gt}}-B(\mathbf{Z}_{\text{detach}})$ 仅作用于 BS；$\mathcal{L}_{\text{gray}}$ 与 $\mathcal{L}_{\text{sat}}$ 作用于干净颜色图 $\mathbf{J}$，仅回传至高斯颜色与变形网络；$\mathcal{L}_{\text{bg}}$ 通过累积透明度 $\alpha$ 仅作用于高斯几何。
>
> 这种"分工式"的梯度路径设计（重建项贯通全链路，先验项各自局部化）是分阶段训练能稳定收敛的前提：
> - **预热阶段**冻结高斯，仅由 $\mathcal{L}_1$、$\mathcal{L}_{\text{D-SSIM}}$ 与水下先验更新 BS/AT；
> - **颜色调整阶段**冻结 BS/AT 与几何，仅由颜色相关项更新 GS-col；
> - **联合阶段**所有路径同时打开。

---

## 五、默认配置中启用的损失（`arguments/underwater/default.py`）

| 损失 | 开关 | 权重 $\lambda$ | 启动迭代 | 热启动步数 |
|---|---|---|---|---|
| $\mathcal{L}_1 + \mathcal{L}_{\text{D-SSIM}}$ | 始终启用 | $1-\lambda_{\text{dssim}}=0.8 / 0.2$ | 0 | – |
| $\mathcal{L}_{\text{mono}}$ | `use_mono_depth_supervision=True` | 0.1 → 0.01 衰减 | 0 | 1000 |
| $\mathcal{L}_{\text{smooth}}$ | `use_depth_smooth_loss=True` | 2.0 | 3000 | 1000 |
| $\mathcal{L}_{\text{dark}}$ | `use_dcp_loss=True` | 1.0 | 3000 | 1000 |
| $\mathcal{L}_{\text{gray}}$ | `use_gw_loss=True` | 0.1 | 10000 | 1000 |
| $\mathcal{L}_{\text{sat}}$ | `use_rgb_sat_loss=True` | 2.0 | 3000 | 1000 |
| $\mathcal{L}_{\text{bg}}$ | `learn_background=True` | 0.01 | 0 | – |
| DWR（深度加权重建） | `add_recon_depth_l1=True` | 1.0 | 3000 | 1000 |

> 论文中未列入式 \eqref{eq:lossfull} 的损失（DWR、opacity prior、alpha smooth、rgb_sv、binf、dsc_at 等）在默认配置下要么权重为 0，要么开关关闭，属于工程上预留的实验通道，不参与最终模型训练。
