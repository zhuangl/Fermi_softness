# Fermi Softness 0.3.0

Research release · 研究版本

Research use must cite Huang et al., *Angew. Chem. Int. Ed.* **2016**, *55*,
6239–6243, [DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824).
使用本软件开展研究时，应引用上述原始论文。详见[引用要求](../CITING.md)。

## English

Studio adds **Auto rotate / Pause rotation** next to Top / Side / Oblique,
with selectable rotation axes and preview speed. **Export → Rotation animation**
saves MP4 or looping GIF movies with adjustable resolution, duration, frame rate,
turn count and direction. Progress and cancellation are included; the original
view is restored afterward. Colors stay on a common scale throughout each movie.

This release also includes the author's saved Pt₃Y startup view, automatic color
limits and properly typeset superscript units. The macOS application entry and
Pt₃Y icon remain available through `fermi-softness install-app`.

```sh
python -m pip install "./fermi_softness-0.3.0-py3-none-any.whl[gui]"
fermi-softness install-app --open
```

## 中文

Top / Side / Oblique 旁新增 **Auto rotate / Pause rotation**，支持选择旋转轴和预览
速度。**Export → Rotation animation** 可导出 MP4 或循环 GIF，调整分辨率、时长、
帧率、圈数和方向。导出支持进度与取消，结束后恢复原视角；整段动画保持相同色标。

本版也包含作者保存的 Pt₃Y 默认视角、自动色标和上标单位显示。macOS 用户可继续通过
`fermi-softness install-app` 创建带 Pt₃Y 图标的应用入口。

详见 [Animation / 动画说明](animation.md) 和 [完整中英文文档](index.md)。
