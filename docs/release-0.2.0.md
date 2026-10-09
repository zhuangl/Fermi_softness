# Fermi Softness 0.2.0

Research release · 研究版本

**Research use must cite Huang et al., Angew. Chem. Int. Ed. 2016, 55, 6239–6243,
[DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824).**
**使用本软件开展研究时，应引用上述原始论文。**
[Full citation / 完整引用与 BibTeX](../CITING.md).

## English

This release provides a standalone VASP Fermi-softness engine, command line,
Python API and interactive desktop viewer. It includes direct WAVECAR,
state-resolved PARCHG and compact fixed-orbital native-density workflows;
Henkelman Bader integration and atomic selection; four display presets and
five colorbar layouts; offline Pt(111), Pt₃Y(111), Bader-selection and synthetic
demos; saved views; Cube, PNG and TIFF export.

Complete English and Chinese documentation covers installation, route selection,
VASP input preparation, Bader analysis, GUI controls, high-resolution export,
all CLI arguments, numerical conventions, troubleshooting, Python use and
development. CLI parameter tables are generated from the actual parser.

The Pt₃Y reconstruction demonstrates Pt-high/Y-low contrast and internal
numerical consistency. The Pt demo is a small software fixture.
The Fortran component is an independently tested kernel, not a certified VASP
source patch. See the [validation record](validation.md) for full evidence.

Install a downloaded wheel with
`python -m pip install "./fermi_softness-0.2.0-py3-none-any.whl[gui]"`, or follow
the [complete user guide](user-guide.en.md). Source archives include documentation,
tests and the Fortran component. The wheel includes portable offline numerical
demos. VASP, POTCAR, original publisher/manuscript files and external Bader
binaries are excluded. Release asset hashes are supplied in `SHA256SUMS.txt`.

## 中文

本版提供独立的 VASP 费米软度计算引擎、命令行、Python API 和交互式桌面界面，
支持直接 WAVECAR、逐态 PARCHG 和固定轨道紧凑原生密度三条路线；接入 Henkelman
Bader 分析及原子选区；提供四套显示风格、五种颜色棒布局；附带 Pt(111)、Pt₃Y(111)、
Bader 选区及合成教学示例；支持保存视角和 Cube、PNG、TIFF 导出。

完整中英文文档覆盖安装、路线选择、VASP 准备、Bader、GUI、高清导出、全部 CLI
参数、科学约定、故障排查、Python 接口和开发。命令参数表直接由程序解析器生成。

Pt₃Y 展示了 Pt 高/Y 低的空间反差，并通过内部数值一致性检查。
Pt demo 是小型软件验证体系。
Fortran 部分是独立验证的核心，并非已完成认证的 VASP 源码补丁。详见
[验证记录](validation.zh-CN.md)。

下载 wheel 后可用
`python -m pip install "./fermi_softness-0.2.0-py3-none-any.whl[gui]"` 安装，
也可按[完整使用手册](user-guide.zh-CN.md)从源码安装。源码包包含文档、测试和 Fortran
部分；wheel 附带可离线查看的数值示例。不包含 VASP、POTCAR、原论文/手稿文件和
外部 Bader 二进制。发布资产校验和位于 `SHA256SUMS.txt`。

## Citation / 引用

B. Huang, L. Xiao, J. Lu, L. Zhuang, *Spatially Resolved Quantification of the
Surface Reactivity of Solid Catalysts*, **Angew. Chem. Int. Ed. 55** (2016),
6239–6243. [DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824).

Please also identify the software version/commit and calculation conventions.
使用时请同时注明软件版本或提交号及计算约定。

License / 许可证：[BSD-3-Clause](../LICENSE).
