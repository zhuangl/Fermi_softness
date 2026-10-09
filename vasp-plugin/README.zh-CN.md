# VASP 内部集成核心

[English](README.md) · [开发者手册](../docs/developer-guide.zh-CN.md)

此目录提供可独立编译的 Fortran 累加核心，**尚不是可直接用于特定 VASP 版本的完整
插件**。本版可用的 VASP 后处理功能由独立 Python 程序提供。

```sh
cmake -S vasp-plugin -B build/fortran
cmake --build build/fortran
ctest --test-dir build/fortran --output-on-failure
```

在合法 VASP 源码中集成时，需要把模块放在调用者之前编译，并向 `accumulate_softness`
提供单个能带的实空间密度。调用层必须实现并验证以下要求：

1. 使用收敛本征值及最终费米能；按导数阈值选择占据和未占据态，不再次乘以 SCF 占据数。
2. 密度转换为 Å⁻³，保留原 PAW 归一化；若输出增广密度，对对应增广贡献使用相同权重。
3. 每个态的 k 点权重只乘一次；非磁标量简并为 2，每个共线通道和旋量为 1，旋量先求
   两个分量的密度之和。
4. 正确处理 VASP 实际对称性和分布式实空间网格。MPI 求和不能重复计算复制的带或 k 点。
5. 导出独立场，不覆盖 SCF 密度、占据或 Hamiltonian；记录单位、kT、阈值、密度表示及积分。
6. 将标量、磁性、旋量和 MPI 结果与独立程序交叉核对，再单独验证 PAW 增广。

通用核心不能独自证明适配成功。选择密度、PAW 和 MPI 接入位置，需要明确的 VASP
版本及合法源码。公开仓库不能包含 VASP 源码或 POTCAR。
