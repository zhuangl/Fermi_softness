# Bader 原子体积与费米软度

[English](bader.md) · [完整使用手册](user-guide.zh-CN.md)

原论文 Experimental Section 明确规定：用 Bader 方法确定表面原子体积，再在其中
积分局域费米软度。原子分区与三维着色图是不同操作：

$$
S_A=\int_{\Omega_A}s_F(\mathbf r)\,d^3r
=\sum_{n\mathbf k\sigma}g_\sigma w_{\mathbf k}w(E_{n\mathbf k\sigma})
\int_{\Omega_A}|\psi_{n\mathbf k\sigma}(\mathbf r)|^2\,d^3r.
$$

同一原子体积可以用于电荷、单态密度或加权软度场的空间归属。波函数本身的精度仍由
电子结构计算与网格决定；Bader 分区并不生成独立的局域轨道。

## 实现与参考密度

工具调用官方 **Henkelman Bader near-grid 算法**，即原论文引用的 Tang–Sanville–
Henkelman 2009 方法。它根据参考密度的零通量边界生成原子标签，软件再与 ACF.dat
核对并积分软度。没有使用最近原子归属或原子球近似。

VASP 推荐参考为 `AECCAR0+AECCAR2`，由收敛静态计算中 `LAECHG=.TRUE.` 生成。
也可以显式选择一个电荷参考文件。参考文件名和校验和写入结果，便于复现边界定义。

参考密度负责确定边界；可选的原始 CHGCAR 用于价电子数积分。采样核密度的积分不能
直接解释为原子电荷，因为核尖峰即使在足以定位边界的网格上也可能积分不准。
应通过加密网格检查原子软度收敛。

## 命令行

```sh
fermi-softness install-bader
fermi-softness bader softness.npz \
  --reference AECCAR0 AECCAR2 --charge CHGCAR \
  --surface-atoms 1 7 10 13 -o bader-results
```

原子编号从 1 开始。示例编号只对应内置 Pt₃Y 顶层；自己的体系需使用实际表面原子。
省略 `--surface-atoms` 时输出全部原子值，不自动猜测表面层。总和不会自动除以原子数
或面积。默认 `--vacuum off`；可改为 `auto` 并单独统计真空区域软度。

输出文件：

- `atoms.csv`：原子坐标、体积、软度和可选的价电子数。
- `report.json`：来源、数值检查及所选表面层总和。
- `basins.npz`：整数原子标签与完整网格几何。
- `softness-on-bader-grid.npz`：积分网格上的软度场。
- `ACF.dat`、`AtIndex.dat`、`bader.log`：Bader 程序的原始结果与日志。

如果软度网格比参考网格粗，软件进行守恒的周期 Fourier 重采样。这增加采样点，
不增加电子结构信息；程序不会隐式降低参考网格分辨率。

```sh
fermi-softness select-basins softness.npz --basins bader-results/basins.npz \
  --atoms 1 7 -o selected-atoms.npz
```

选区外数值为零，元数据明确标记 Bader 选区，原结构保留用于定位。对于外部已经对齐
的整数标签，可以使用 `integrate --labels labels.npy`；ACF.dat 只有积分表，不能单独
用于恢复完整三维分区。

## GUI

加载软度场后，在 **Bader** 页选择参考文件、可选 CHGCAR、Bader 可执行文件和输出
父目录。结果写入父目录下的 `bader-result`。表格支持选择原子并显示相应区域，
**Restore full field** 恢复完整软度场；**Export** 可保存当前选区的场和图像。

程序路径可由 GUI、`--executable` 或 `FERMI_SOFTNESS_BADER` 指定。自动下载支持
macOS arm64/Linux x86_64；其他平台可编译官方源码。Bader 为独立外部依赖，
其源码与二进制没有重新按本项目 BSD 许可证分发。

## 与原稿的关系

原稿和找到的 SI 已核查，但没有记录历史参考密度文件名和完整 Bader 命令。因此，
现版采用相同分区思想和真实算法，同时明确记录新的参考选择；不能据此断言两次计算
的边界逐点相同。当前 Pt₃Y 将参考网格由 80×80×320 加密到 160×160×640 后，原子
软度最大相对变化为 0.4352%，表面层总和变化为 0.0147%。

参考：[原论文](https://doi.org/10.1002/anie.201601824)、
[Henkelman Bader](https://github.com/henkelmangroup/bader)、
[Tang et al. 2009](https://doi.org/10.1088/0953-8984/21/8/084204)。
