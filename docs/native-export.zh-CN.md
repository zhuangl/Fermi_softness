# VASP 原生密度导出

[English](native-export.md) · [完整操作步骤](user-guide.zh-CN.md)

原生密度路线补充直接 WAVECAR 平滑场重建：

| 路线 | 用途 | 支持范围 |
|---|---|---|
| `prepare-parchg` / `compute-parchg` | 逐态密度，可用于独立交叉验证 | 非磁标量与共线自旋 |
| `prepare-frozen` / `compute-frozen` | 一个紧凑加权密度文件 | 非磁标量；已在 VASP 6.4.2 验证 |

紧凑路线令 $c=4kT$，把临时占据数设置为 $c\,w(E)$，其范围为 [0,1]。
在保持轨道和本征值不变的条件下，VASP 根据这些权重构造原生价电子密度。
再将输出除以 c，即得到包含 VASP 电荷增广的局域软度。

生成设置采用 `ALGO=None`、`LDIAG=.FALSE.`、`NELM=1`、`ISMEAR=-2`、`ICHARG=0`，
并保留原始带数和 k 点顺序。由于 vasprun.xml 中的能量可能被舍入，权重使用 WAVECAR
中的完整精度本征值。导入器检查源文件指纹、算法参数、输出能量、占据数、结构和总积分。

临时 NELECT 和占据数只服务于数学加权导出。导出目录的总能量、费米能和 CHGCAR
不构成新的基态自洽结果，不能作为物理重启输入。电荷包络面必须使用**原始 SCF CHGCAR**，
Bader 边界必须使用**原始 AECCAR0+AECCAR2**。

Pt(111) 标量验证逐网格点对照了 161 个独立 PARCHG 的加权和：RMS 差异为
2.09×10⁻⁷ eV⁻¹ Å⁻³，相对 L2 差异为 3.03×10⁻⁶。Pt₃Y 原生场积分与谱求和相对
差异为 3.19×10⁻⁹。参见[数值报告](../results/pt3y-validation.json)。

两条路线均保留原始 WAVECAR，紧凑导出显式设置 `LWAVE=.FALSE.`。使用相同 POTCAR，
并选择不会改变 NBANDS 的并行布局。导出应在独立目录运行，具体遵循生成的 RUN.md。
原生密度表示仍不等于全电子轨道重建。

参考：[FERWE](https://vasp.at/wiki/FERWE)、[ALGO](https://vasp.at/wiki/ALGO)、
[LPARD](https://vasp.at/wiki/LPARD)。
