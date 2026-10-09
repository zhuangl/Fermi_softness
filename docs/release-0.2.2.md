# Fermi Softness 0.2.2

Research release · 研究版本

Research use must cite Huang et al., *Angew. Chem. Int. Ed.* **2016**, *55*,
6239–6243, [DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824).
使用本软件开展研究时，应引用上述原始论文。详见[引用要求](../CITING.md)。

## Desktop launch / 桌面启动

Studio now has a macOS application entry with a transparent Pt₃Y icon. Install
the GUI, then run `fermi-softness install-app --open`. The source distribution
also includes a one-click `Install Fermi Softness Studio.command` installer.

本版提供带透明 Pt₃Y 图标的 macOS 应用入口。安装 GUI 后运行
`fermi-softness install-app --open`，以后即可从“应用程序”或 Spotlight 启动。
源码包还提供可双击运行的一键安装脚本。

```sh
python -m pip install "./fermi_softness-0.2.2-py3-none-any.whl[gui]"
fermi-softness install-app --open
```

The application entry uses your installed Python environment and opens the
Pt₃Y demo. The installer registers it with macOS, preserves unrelated apps,
and logs startup messages in the user's Library/Logs directory.

应用入口使用已有 Python 环境，启动后展示 Pt₃Y 示例。安装器向 macOS 注册应用、
保护同名的其他应用，并将启动信息记录到用户的 Library/Logs 目录。

See [desktop setup / 桌面安装说明](desktop-app.md) and the
[complete bilingual documentation / 完整中英文文档](index.md).
