# Third-party dependencies and reference material

The package uses NumPy, SciPy, ASE and defusedxml, with optional PyVista/VTK,
PyVistaQt, PySide6 and Pillow for the viewer. Their licenses remain applicable
to their own distributions. No dependency's source is vendored here.

Animation export uses [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
and its FFmpeg executable, installed as dependencies rather than vendored in this
repository. FFmpeg and the codecs in the chosen distribution retain their own
licenses; see the dependency's bundled notices and [FFmpeg licensing](https://ffmpeg.org/legal.html).

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

The bundled Pt/Pt3Y NPZ fields, basin labels and software-rendered figures were produced
for this project. Their provenance is recorded in the dataset reports and
validation records. They are included as project demonstration data under the
project license. Private source Cubes are not included. The separately credited
historical screenshot below retains its original copyright. This project does
not grant a license to VASP or its potential datasets.

## Historical ChemistryViews screenshot

[`docs/images/chemistryviews-2016.jpg`](docs/images/chemistryviews-2016.jpg)
is the historical webpage screenshot supplied by Lin Zhuang for the introduction
to Fermi softness. It is preserved byte for byte, including the visible title,
publication date, source and copyright notice.

- Feature: *Frontier Orbital Theory for Solid Catalysts*.
- Publication: ChemistryViews, **9 June 2016**.
- Author/source credited on the page: Angewandte Chemie International Edition / Wiley-VCH.
- Copyright as displayed: **Wiley-VCH Verlag GmbH & Co. KGaA, Weinheim**.
- Research article: Huang, Xiao, Lu and Zhuang,
  [Angew. Chem. Int. Ed. 2016, 55, 6239–6243](https://doi.org/10.1002/anie.201601824).

This third-party historical material is separate from the project's
BSD-3-Clause software license. Its source record and SHA-256 checksum are in
[`chemistryviews-2016.source.json`](docs/images/chemistryviews-2016.source.json).

## 中文说明

NumPy、SciPy、ASE、defusedxml 及可选的 PyVista/VTK、PyVistaQt、PySide6、Pillow
分别遵循自身许可证，本仓库没有把这些依赖的源码合并分发。Henkelman Bader 程序由
用户单独安装，不重新按本项目 BSD 许可证分发。

动画导出使用单独安装的 imageio-ffmpeg 及其 FFmpeg 程序。FFmpeg 和相应编解码器
保持各自许可证，相关声明随依赖分发，不改用本项目的 BSD 许可证。

内置 Pt/Pt₃Y 数值场、Bader 标签和程序生成图像是本项目产生的演示数据，随项目按
项目许可证提供，来源见相应报告。它们不包含私人源 Cube、出版商 PDF、
VASP 源码、POTCAR 或外部 Bader 二进制，也不授予这些外部软件或赝势的使用许可。
公开参考测试文件通过固定版本和校验和另行下载，见 `validation/public-fixtures.json`。

## 历史 ChemistryViews 报道截图

[`chemistryviews-2016.jpg`](docs/images/chemistryviews-2016.jpg) 是庄林提供的历史网页
截图，用于介绍费米软度的来历。图片按原文件保存，保留标题、日期、来源和版权标记。
报道题为 *Frontier Orbital Theory for Solid Catalysts*，刊于 ChemistryViews，
日期为 **2016 年 6 月 9 日**；页面署名及来源为 Angewandte Chemie International
Edition / Wiley-VCH，标注版权为 **Wiley-VCH Verlag GmbH & Co. KGaA, Weinheim**。

这张第三方历史截图不属于本项目 BSD-3-Clause 软件许可证的授权范围。
[来源记录](docs/images/chemistryviews-2016.source.json)保存了书目信息和文件校验和。
使用费米软度方法开展研究时，请按 [CITING.md](CITING.md) 引用原始论文。
