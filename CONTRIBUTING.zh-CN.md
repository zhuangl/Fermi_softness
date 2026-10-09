# 参与开发

[English](CONTRIBUTING.md) · [开发者手册](docs/developer-guide.zh-CN.md)

安装 `.[gui,dev]`，运行 `pytest -q`、`ruff check src tests validation`、
`python validation/generate_cli_reference.py --check` 和 `python validation/check_docs.py`。
数值代码应与 Qt/VTK 分离，以便在计算服务器运行。

新增输入格式必须有独立参考检查，例如直接 Fourier 求和、解析场、系数模方积分或
VASP 自身的逐态密度。不能把外观合理的图片当作数值验证。损坏、截断和不一致输入
也应纳入检查。

提交问题请提供软件版本、系统、Python 版本、命令或 GUI 步骤、报错及可公开的小样本。
不要上传 POTCAR、VASP 源码、凭据或私人研究数据；不能分享真实数据时优先制作合成样本。

修改单位、简并因子、对称性或 PAW 归一化之前，应更新方法说明，并用独立测试证明
新约定。中英文文档、CLI 参数表和已知限制应同步修改。

Pull request 应说明用户可见的变化和验证结果。图片应按实际导出分辨率检查，保留场景
文件以便重现。改进论文复现时，应分别报告数值一致性、物理收敛和与原稿比较的证据。

项目代码采用 BSD-3-Clause；第三方组件保持各自许可证。贡献时请确认新增内容可以
按项目许可证分发。提交渠道为仓库的 Issues 和 Pull requests。
