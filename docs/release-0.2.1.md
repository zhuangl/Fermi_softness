# Fermi Softness 0.2.1

Research release · 研究版本

**Research use must cite Huang et al., Angew. Chem. Int. Ed. 2016, 55, 6239–6243,
[DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824).**
**使用本软件开展研究时，应引用上述原始论文。**
[Full citation / 完整引用与 BibTeX](../CITING.md).

## English

This update simplifies the Pt₃Y descriptions in the home page, guides and
desktop demo catalog. The scientific calculation, numerical datasets and
Bader analysis are unchanged. Installation instructions and the desktop
screenshot are refreshed for this version.

Install the GUI from the downloaded wheel:

```sh
python -m pip install "./fermi_softness-0.2.1-py3-none-any.whl[gui]"
fermi-softness gui --example pt3y111
```

See the [complete user guide](user-guide.en.md) and
[documentation index](index.md). The source archive includes both language
versions of the documentation. `SHA256SUMS.txt` verifies the downloadable assets.

## 中文

本次更新精简了首页、使用手册和桌面示例中的 Pt₃Y 说明文字，并更新安装指令和界面
截图。科学计算、数值数据及 Bader 分析保持不变。

下载 wheel 后安装并启动：

```sh
python -m pip install "./fermi_softness-0.2.1-py3-none-any.whl[gui]"
fermi-softness gui --example pt3y111
```

详见[完整使用手册](user-guide.zh-CN.md)及[文档目录](index.md)。源码包包含完整中英文
文档，下载资产可通过 `SHA256SUMS.txt` 核验。
