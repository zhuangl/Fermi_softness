# 费米软度工具包

[English](../README.md) · [完整使用手册](user-guide.zh-CN.md) ·
[全部文档](index.md) · [命令行参考](cli-reference.zh-CN.md)

这个工具把 VASP 的波函数转换成局域费米软度，并提供可旋转、调色和高精度
导出的桌面界面 **Fermi Softness Studio**。方法来源：B. Huang、L. Xiao、J. Lu、L. Zhuang，
[Angew. Chem. Int. Ed. 2016, 55, 6239–6243](https://doi.org/10.1002/anie.201601824)。

> **引用要求：使用本软件或费米软度方法开展研究、发表论文或进行学术报告时，应引用
> Huang 等人的原始论文：Angew. Chem. Int. Ed. 2016, 55, 6239–6243，
> [DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824)。**
> [完整书目信息和 BibTeX](../CITING.md)。仅引用软件仓库不能代替原始论文。

[![Fermi Softness Studio 中的 Pt₃Y(111) 费米软度图](images/studio-overview.png)](images/studio-overview.png)

*Fermi Softness Studio 中的 Pt₃Y(111) 费米软度图与交互式显示设置。*

## 费米软度的来历

Huang、Xiao、Lu 和 Zhuang 于 [2016 年](https://doi.org/10.1002/anie.201601824)
提出费米软度，将分子前线轨道的反应性分析思路拓展到固体表面。通过对费米能级附近
的电子态加权，该方法既给出表面反应性描述符，也能显示局域反应性的空间分布。

**2016 年 6 月 9 日**，ChemistryViews 以 *Frontier Orbital Theory for Solid Catalysts*
（固体催化剂的前线轨道理论）介绍了这项研究，展示 Pt₃Y 表面图像，并介绍了 MoS₂
边缘的应用。下图是庄林保存并提供的当年报道截图。本工具包将这一方法带入 VASP
计算流程，提供交互式绘图和逐原子分析。

[![ChemistryViews 于 2016 年 6 月 9 日刊登的费米软度介绍](images/chemistryviews-2016.jpg)](images/chemistryviews-2016.jpg)

*历史报道出处：ChemistryViews / Angewandte Chemie International Edition，
2016 年 6 月 9 日。截图标注版权：Wiley-VCH Verlag GmbH & Co. KGaA, Weinheim。
点击图片可查看原始分辨率。[图片来源与署名说明](../THIRD_PARTY.md#历史-chemistryviews-报道截图)。*

## 软件功能

**v0.2.2 研究版本**提供独立计算引擎、CLI/Python 接口、GUI、离线示例和 Bader 分析。
Fortran 部分提供独立验证的累加核心，特定 VASP 版本的源码接入见开发文档。
完整范围见[版本说明](release-0.2.2.md)。

## 安装与启动

克隆仓库或解压源码包，使用 Python 3.10 或更新版本：

```sh
git clone https://github.com/zhuangl/Fermi_softness.git
cd Fermi_softness
```

在项目目录中安装：

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install ".[gui]"
fermi-softness gui --demo
```

Windows 激活环境使用 `.venv\Scripts\Activate.ps1`。macOS 安装 GUI 后再运行一次：

```sh
fermi-softness install-app --open
```

以后从“应用程序”或 Spotlight 搜索 **Fermi Softness Studio** 即可启动。
源码用户也可以双击 **Install Fermi Softness Studio.command** 完成安装和应用入口创建。
详见[桌面安装说明](desktop-app.md)。
Data 页的示例列表现在包含真实 Pt(111)、Pt₃Y(111) 重建、Pt 的单原子 Bader
贡献和合成教学示例。数据已随程序附带，查看时不需要 VASP 或联网。

```sh
fermi-softness gui --example pt3y111
```

Pt₃Y 示例采用 PW91 和四层表面模型，展示 Pt 高、Y 低的空间对比，
启动时使用作者保存的视角和自动色标设置。

## 从 VASP 结果开始

准备同一次收敛静态计算的 `WAVECAR` 和 `vasprun.xml`，可另加同次计算的
`CHGCAR`。计算时建议 `NSW=0`、`IBRION=-1`、`LWAVE=.TRUE.`、
`LCHARG=.TRUE.`、`ISYM=-1`。标量波函数也支持 `ISYM=0`。

```sh
fermi-softness compute --wavecar 路径/WAVECAR --vasprun 路径/vasprun.xml \
  --kt 0.4 -o my-softness
fermi-softness gui my-softness/softness.npz --charge 路径/CHGCAR
```

也可在界面 **Data** 页选择两个文件，点击 **Calculate softness**。
计算完成后，到 **Export** 页保存结果。

未占据态必须足够多：默认参数要求能带覆盖费米能上下约 3.13 eV。
程序会检查缺失能带、文件是否匹配、对称性和网格精度。若需要增加空带，
调整 `NBANDS` 后重新做静态计算。费米软度的 `kT` 是描述符参数，
不等同于 VASP 自洽计算使用的 `SIGMA`。

需要保留 VASP 的 PAW 电荷增广时，可用第二条路线：

```sh
fermi-softness prepare-parchg --wavecar 路径/WAVECAR --vasprun 路径/vasprun.xml \
  --incar 路径/INCAR -o native-deck
# 将原 WAVECAR 和匹配的 POTCAR 放到 native-deck，再在该目录运行 VASP。
fermi-softness compute-parchg native-deck/manifest.json -o native-softness
```

界面 Data 页也提供 **Prepare native VASP densities** 和 **Combine native densities**。
这条路线让 VASP 生成逐能带、逐 k 点的 PARCHG，工具再加权合成软度，检查单态
归一化和总积分。它支持非磁和共线自旋体系；VASP 自身的 LPARD 不支持非共线体系。

## 调整图像

**Scene** 页有三种显示：

- **Softness isosurface**：局域软度的三维等值面。
- **Charge surface · softness colors**：把软度映射到电荷等值面；默认曲面包围 95% 电荷。
- **Planar section**：沿晶胞方向查看平面截面。

鼠标拖动旋转，Shift 加拖动平移，滚轮缩放。可改变色标、等值面、透明度、
超胞重复次数和正交投影。比较不同材料时，关闭自动色标，使用相同上下限。
**Save view** 保存相机和显示参数，**Load view** 恢复视角。

**Style** 页可以选择科研浅色、原论文黑底、演示深色和灰度打印四套风格，
以及横向、纵向、紧凑、两端刻度或隐藏颜色棒。字体、刻度格式、配色反转和
eV/keV 单位都可调整。单位切换仅改变显示；数据仍以 eV⁻¹ Å⁻³ 保存。

**Export** 页可导出 PNG/TIFF，设置实际像素尺寸、DPI 和透明背景。
同时提供 Cube 输出，可继续在 VMD 或 VESTA 中处理。
这里图像分辨率和计算网格精度是两个独立设置。

## 数值结果的含义

输出的局域软度单位是 eV⁻¹ Å⁻³；乘以 1000 即为原文图中的 keV⁻¹ Å⁻³。
直接从 WAVECAR 重建的是 PAW 平滑波函数贡献，不包含核区的 PAW 增广。
程序保留原系数，不会为了让积分等于一而强制归一化；因此分别报告平滑场积分
和完整能态求和得到的谱软度。
原生 PARCHG 路线则保留 VASP 的电荷增广，并核对积分与谱软度的一致性；
这仍应称为 VASP 原生电荷表示，不能当成全电子波函数重建。

原论文的表面描述符来自第一层表面原子的 Bader 体积积分。
现在程序已接入原论文引用的 Henkelman Bader 算法：先根据参考电荷密度的
零通量面定义原子体积，再在同一体积内积分软度。VASP 推荐用 AECCAR0+AECCAR2
作分区参考，CHGCAR 用于价电子数积分。

```sh
fermi-softness install-bader
fermi-softness bader softness.npz --reference AECCAR0 AECCAR2 \
  --charge CHGCAR --surface-atoms 1 7 10 13 -o bader-results
```

原子编号从 1 开始；示例编号适用于内置 Pt₃Y 的表面层，自己的体系需选取实际
表面原子。在 **Bader** 页可查看逐原子结果，选择某些原子或已记录的表面层
单独显示，再从 Export 页保存选区软度场。详见 [Bader 方法说明](bader.zh-CN.md)。

非磁体系还可使用紧凑原生导出，避免生成大量逐态文件：

```sh
fermi-softness prepare-frozen --wavecar WAVECAR --vasprun vasprun.xml \
  --incar INCAR -o compact-deck
# 按 compact-deck/RUN.md 运行 VASP 后：
fermi-softness compute-frozen compact-deck/manifest.json -o native-softness
```

## 当前版本

独立后处理、桌面 GUI、Cube/PNG/TIFF 输出和数值校验已经实现。
`vasp-plugin` 目录提供可编译的 Fortran 权重与累加核心；
具体 VASP 版本的源码接入和 PAW 增广仍需要专门验证，不能把这个核心模块
当作已经完成集成的 VASP 插件。

具体通过了哪些测试、哪些案例尚未验收，见[验证记录](validation.zh-CN.md)。

完整的安装、计算、绘图和故障排查见[使用手册](user-guide.zh-CN.md)；数值定义见
[科学方法](science.zh-CN.md)，接口、源码和打包说明见[开发者手册](developer-guide.zh-CN.md)。
项目采用 [BSD-3-Clause](../LICENSE)。请引用原方法论文并注明软件版本，引用信息见
[CITATION.cff](../CITATION.cff)。贡献及问题反馈见[参与开发](../CONTRIBUTING.zh-CN.md)。
