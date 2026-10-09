# 开发者手册

[English](developer-guide.en.md) · [文档目录](index.md)

## 代码结构

| 路径 | 职责 |
|---|---|
| `src/fermi_softness/kernel.py` | 稳定的费米函数导数及能窗 |
| `wavecar.py`、`vasprun.py` | 二进制电子态和安全 XML 元数据解析 |
| `compute.py` | 逐态平滑场重建 |
| `parchg.py`、`frozen.py` | VASP 原生导出准备及带检查的导入 |
| `field.py`、`io.py` | 几何、周期采样、积分及 NPZ/Cube/密度读写 |
| `bader.py`、`install_bader.py` | 参考密度分区、积分及可选程序安装 |
| `render.py`、`gui.py` | 场景模型、PyVista 绘图及 Qt 界面 |
| `demos.py`、`data/` | 可移植离线数据及来源记录 |
| `cli.py` | 命令行接口 |
| `tests/` | 数值及输入完整性回归检查 |
| `validation/` | 可选真实文件、GUI、发布检查和可分发 VASP 输入 |
| `vasp-plugin/` | 原创 Fortran 核心及独立测试驱动 |

表中没有目录前缀的 Python 文件都位于 `src/fermi_softness/`。计算模块应保持无需图形
环境即可运行。

## 开发环境与检查

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[gui,dev]"
python -m pytest -q
ruff check src tests validation
python validation/generate_cli_reference.py --check
python validation/check_docs.py
python -m build
```

Windows 激活方式见使用手册。`dev` 包含 pytest、Ruff 和 build。数值测试不强制需要
GUI 依赖，缺少图形依赖时相关测试跳过；公开真实文件测试在下载样本前也会跳过：

```sh
python validation/fetch_public_fixtures.py
python -m pytest -q tests/test_public_wavecars.py
python -m pip install pymatgen
python validation/compare_pymatgen.py
```

下载样本由固定提交号和 SHA-256 校验，不随软件包分发。桌面验证需要真实图形环境：

```sh
python validation/gui_smoke.py
python validation/gui_acceptance_v02.py
python validation/visual_v02.py
```

材料验证脚本还需要其代码指定路径下的原始计算输出，它们不是自带 DFT 引擎。
重新生成数据时，可使用 [Pt 输入](../validation/pt111/README.md)或
[Pt₃Y 输入](../validation/pt3y111/README.md)，配合自己的 VASP 和合法赝势。

独立 Fortran 核心需要 CMake 和 Fortran 编译器：

```sh
cmake -S vasp-plugin -B build/fortran
cmake --build build/fortran
ctest --test-dir build/fortran --output-on-failure
```

接入 VASP 前应阅读[集成约定](../vasp-plugin/README.md)。MPI 汇总、PAW 接口和特定
版本适配仍需实现及验证，单独编译核心不表示插件已经可用。

## Python API 示例

下列函数可用于脚本。项目仍处于研究版本，构建下游流程时建议固定软件版本。

```python
from fermi_softness.compute import calculate
from fermi_softness.io import write_field_cube

field, channels = calculate("source-run/WAVECAR", "source-run/vasprun.xml", kt=0.4)
field.save("softness.npz")
write_field_cube(field, "softness.cube")
print(field.integral)  # 当前路线的平滑场积分，单位 eV^-1
print(field.metadata["spectral_softness_eV_inverse"])
print(field.sample([[0.0, 0.0, 5.0]]))  # 笛卡尔坐标 Å，周期插值
```

```python
from fermi_softness.demos import load_demo
from fermi_softness.field import Field

field, charge, scene, resource_root = load_demo("pt3y111")
field.save("pt3y-copy.npz")
restored = Field.load("pt3y-copy.npz")
assert abs(restored.integral - field.integral) < 1e-10
```

```python
from fermi_softness.bader import run_bader, select_basins

report = run_bader(
    field,
    ["source-run/AECCAR0", "source-run/AECCAR2"],
    "atomic-softness",
    charge="source-run/CHGCAR",
    surface_atoms=[1, 7, 10, 13],
)
selected = select_basins(field, "atomic-softness/basins.npz", [1, 7, 10, 13])
selected.save("surface-only.npz")
```

最后一个示例要求 field 和参考密度来自同一次计算；不能把内置示例和无关源文件混用。
原生导出自动化可调用相应模块中的 `prepare_parchg`、`calculate_parchg`、
`prepare_frozen` 和 `calculate_frozen`。

## 数据格式与数值约定

原生场是压缩 NumPy 归档，使用 `allow_pickle=False` 即可读取：

| 字段 | 维度与含义 |
|---|---|
| `values` | `(nx, ny, nz)`，单位由元数据记录 |
| `cell` | `(3, 3)`，按行排列晶格矢量，单位 Å |
| `numbers` | `(natoms,)`，原子序数 |
| `positions` | `(natoms, 3)`，笛卡尔位置，单位 Å |
| `origin` | `(3,)`，网格笛卡尔原点，单位 Å |
| `metadata` | JSON 字符串，记录表示、单位、参数与来源 |

网格位置为 `origin + (i/nx, j/ny, k/nz) @ cell`，周期端点不重复。体积元为
`abs(det(cell))/(nx*ny*nz)`。`Field.sample` 对斜晶胞也采用周期三线性插值。
`integrate_regions` 要求非负整数标签与场的形状和几何一致；裸标签数组本身无法验证
几何，调用者必须保证这种一致性。

`basins.npz` 是记录标签与几何的另一种归档，不能当作普通 Field 加载。场景 JSON
保存显示参数与相机，不保存数值场。扩展格式时应维持这些区别。

任何关于自旋简并、k 点权重、PAW 归一化、单位或对称性的修改，都需要同步更新
[方法约定](../research/notes/method-contract.md)，并给出独立数值验证。仅凭图像相似
不能证明计算正确。

## 文档和发布

英文和中文说明应同步更新。CLI 参数表由解析器自动生成：

```sh
python validation/generate_cli_reference.py
python validation/check_docs.py
```

链接检查器检查 Markdown 本地目标，不验证外部网页，也不运行 VASP。发布前应构建
wheel 和源码包，在干净环境安装 wheel，执行文档中的示例与 API 流程，并确认许可证、
引用、文档、Fortran 源码和可分发算例按预期包含在对应归档中。发布资产应记录校验和。

不要包含私人研究档案、出版商 PDF、凭据、外部 Bader 二进制、VASP 源码或 POTCAR。
除文件名外，还应审查 NPZ 内嵌元数据。内置 NPZ 是本项目计算产生的派生数值场，
来源见 `data/*/report.json` 和验证记录；不附带未公开原始档案。单独收录的第三方历史
截图在 THIRD_PARTY.md 中标明来源，并保留原版权。

版本号应在 `pyproject.toml`、`__init__.py`、`CITATION.cff`、更新日志、手册和发布
说明中保持一致。wheel 用于安装，源码包还包含开发与文档材料。其他要求见
[参与开发](../CONTRIBUTING.zh-CN.md)和[第三方声明](../THIRD_PARTY.md)。
