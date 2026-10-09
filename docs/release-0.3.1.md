# Fermi Softness 0.3.1

Research release · 研究版本

Research use must cite Huang et al., *Angew. Chem. Int. Ed.* **2016**, *55*,
6239–6243, [DOI: 10.1002/anie.201601824](https://doi.org/10.1002/anie.201601824).
使用本软件开展研究时，应引用上述原始论文。详见[引用要求](../CITING.md)。

## GUI export fix

On macOS Retina displays, GUI animation export could capture only part of the
interactive framebuffer even though the encoded video had the requested pixel
dimensions. This release renders MP4/GIF frames independently at the output
resolution, preserving the selected view and numerical color scale. GUI
PNG/TIFF export uses the same independent-renderer approach, including transparency.

The GUI regression now compares decoded movie pixels against independent full-frame
reference images, rather than checking dimensions and frame counts alone.
Checks cover 640×480 and 1920×1080 MP4, GIF and transparent PNG, and confirm that
the live window and camera remain unchanged.

Restart Studio after updating, then export again. Existing cropped videos need
to be regenerated from their source fields.

## GUI 导出修复

macOS Retina 显示环境中，原 GUI 动画导出可能只截取交互窗口的一部分，虽然视频文件
仍具有设定的像素尺寸。本版改为按输出分辨率独立渲染 MP4/GIF 的完整画面，保留所选
视角及数值色标；PNG/TIFF 导出也采用独立渲染，并保留透明背景选项。

新的 GUI 回归检查会把解码后的画面与完整参考图进行像素对照，覆盖 640×480 和
1920×1080 MP4、GIF 及透明 PNG，同时确认导出不改变当前窗口和相机。

更新后请完全退出并重新打开 Studio，再次导出。已经被裁切的视频需要从源数据重新生成。
