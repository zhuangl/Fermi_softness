# Pt(111) 软件集成验证算例

[English](README.md) · [验证记录](../../docs/validation.zh-CN.md)

三原子、三层 1×1 fcc(111) 表面，晶格常数 3.92 Å，两侧各 10 Å 真空。
它用于检查真实 VASP 输出到软度场的软件流程，不是收敛吸附研究，也不是 2016 原稿复现。

由有权限的使用者提供 PBE Pt POTCAR。本项目不分发它。验证采用 VASP 6.4.2、
ENCUT=400 eV、完整 4×4×1 k 网格、48 带、Fermi–Dirac SCF 展宽 0.1 eV、ISYM=-1、
EDIFF=1e-8 eV，最终 SCF 需要 27 步。

完成本目录输入文件的静态计算后：

```sh
fermi-softness compute --wavecar WAVECAR --vasprun vasprun.xml -o smooth
fermi-softness prepare-parchg --wavecar WAVECAR --vasprun vasprun.xml \
  --incar INCAR -o native-deck
```

用相同 WAVECAR 和 POTCAR 运行生成的 LPARD 目录，使用 KPAR=1。随后：

```sh
fermi-softness compute-parchg native-deck/manifest.json -o native
```

kT=0.4 eV、绝对阈值 0.001 eV⁻¹ 选择了 161 个态。数值及验收范围见
[报告](../../results/pt111-validation.json)。
