# Third-party dependencies and reference material

The package uses NumPy, SciPy, ASE and defusedxml, with optional PyVista/VTK,
PyVistaQt, PySide6 and Pillow for the viewer. Their licenses remain applicable
to their own distributions. No dependency's source is vendored here.

Optional Bader analysis uses the Henkelman group's official executable,
downloaded separately with pinned release checksums. It is not redistributed
under this project's BSD license. Runtime and numerical integration checks
are performed locally.

The WAVECAR implementation was written for this project using the public binary
format description and mathematical plane-wave conventions. Independent format
references and validation include:

- WaveTrans, R. M. Feenstra and M. Widom:
  https://www.andrew.cmu.edu/user/feenstra/wavetrans/
- VaspBandUnfolding, Qijing Zheng:
  https://github.com/QijingZheng/VaspBandUnfolding
- pymatgen / pymatgen-core, Materials Project (MIT):
  https://github.com/materialsproject/pymatgen

Downloaded reference code, publisher PDFs, VASP source, POTCARs, and heavy
calculation outputs are excluded from public distributions. Public test
fixtures are fetched separately from pinned upstream URLs and are used only
for optional validation. See `validation/public-fixtures.json` for checksums.

The bundled Pt/Pt3Y NPZ fields, basin labels and rendered figures were produced
for this project. Their provenance is recorded in the dataset reports and
validation records. They are included as project demonstration data under the
project license; the original article figures and private source Cubes are not
included. This does not grant a license to VASP or its potential datasets.

## 中文说明

NumPy、SciPy、ASE、defusedxml 及可选的 PyVista/VTK、PyVistaQt、PySide6、Pillow
分别遵循自身许可证，本仓库没有把这些依赖的源码合并分发。Henkelman Bader 程序由
用户单独安装，不重新按本项目 BSD 许可证分发。

内置 Pt/Pt₃Y 数值场、Bader 标签和程序生成图像是本项目产生的演示数据，随项目按
项目许可证提供，来源见相应报告。它们不包含原论文图像、私人源 Cube、出版商 PDF、
VASP 源码、POTCAR 或外部 Bader 二进制，也不授予这些外部软件或赝势的使用许可。
公开参考测试文件通过固定版本和校验和另行下载，见 `validation/public-fixtures.json`。
