# Fermi Softness 0.3.0 — 命令行完整参考

[English](cli-reference.en.md) · [使用手册](user-guide.zh-CN.md)

本页由实际命令解析器生成，参数名、必填项、选项和默认值与程序同步。

```sh
fermi-softness --version
fermi-softness --help
fermi-softness compute --help
```

也可用 `python -m fermi_softness` 替代 `fermi-softness`。每个子命令都支持 `-h/--help`。

## `compute`

重建 PAW 平滑赝波函数软度场。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `--wavecar` | 否 | `WAVECAR` | 源 WAVECAR 文件。 |
| `--vasprun` | 否 | `vasprun.xml` | 匹配的源 vasprun.xml，支持 gzip。 |
| `--kt` | 否 | `0.4` | 描述符 kT，单位 eV；独立于 SCF SIGMA。 |
| `--threshold` | 否 | `0.001` | 费米函数导数的绝对截断阈值，单位 eV⁻¹。 |
| `--mu` | 否 | — | 覆盖费米能，单位 eV；省略时使用源元数据。 |
| `--grid` | 否 | — | FFT 三个维度 NX NY NZ；省略时自动选择。 |
| `--gamma-half` | 否 | `x`; `x`, `z` | Gamma 半空间存储方向。 |
| `--max-memory-gb` | 否 | `4` | 工作内存估算预算，单位 GB。 |
| `--allow-incomplete` | 否 | `False` | 允许空带不足的诊断输出。 |
| `--allow-reduced` | 否 | `False` | 允许未经对称性展开的诊断输出。 |
| `-o`, `--output` | 否 | `fermi-results` | 输出文件或目录，见下方说明。 |

## `prepare-parchg`

准备逐态原生密度导出。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `--wavecar` | 否 | `WAVECAR` | 源 WAVECAR 文件。 |
| `--vasprun` | 否 | `vasprun.xml` | 匹配的源 vasprun.xml，支持 gzip。 |
| `--incar` | 否 | — | 源 INCAR；省略时在 vasprun.xml 所在目录查找。 |
| `--kt` | 否 | `0.4` | 描述符 kT，单位 eV；独立于 SCF SIGMA。 |
| `--threshold` | 否 | `0.001` | 费米函数导数的绝对截断阈值，单位 eV⁻¹。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## `compute-parchg`

合成已准备的逐态原生密度。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `manifest` | 是 | — | 生成的 manifest.json，应与导出结果放在一起。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## `prepare-frozen`

准备非磁体系的紧凑导出。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `--wavecar` | 否 | `WAVECAR` | 源 WAVECAR 文件。 |
| `--vasprun` | 否 | `vasprun.xml` | 匹配的源 vasprun.xml，支持 gzip。 |
| `--incar` | 否 | — | 源 INCAR；省略时在 vasprun.xml 所在目录查找。 |
| `--kt` | 否 | `0.4` | 描述符 kT，单位 eV；独立于 SCF SIGMA。 |
| `--threshold` | 否 | `0.001` | 费米函数导数的绝对截断阈值，单位 eV⁻¹。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## `compute-frozen`

导入通过检查的固定轨道密度。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `manifest` | 是 | — | 生成的 manifest.json，应与导出结果放在一起。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## `inspect`

检查 WAVECAR 格式及 FFT 网格。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `wavecar` | 是 | — | 源 WAVECAR 文件。 |
| `--gamma-half` | 否 | `x`; `x`, `z` | Gamma 半空间存储方向。 |

## `gui`

打开 Fermi Softness Studio。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `field` | 否 | — | 软度体数据，推荐原生 .npz。 |
| `--charge` | 否 | — | 电荷密度；包络面和电子数使用原始 SCF 密度。 |
| `--demo` | 否 | `False` | 打开合成教学数据。 |
| `--scene` | 否 | — | 保存的场景 JSON，包含相机和样式。 |
| `--example` | 否 | — | demos 命令列出的内置示例 ID。 |

## `demos`

列出离线示例目录。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |

## `install-app`

安装 macOS 应用程序图标和启动入口。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `--directory` | 否 | — | 应用程序目录；默认优先使用可写的 /Applications，否则使用 ~/Applications。 |
| `--open` | 否 | `False` | 安装 macOS 应用入口后立即打开 Studio。 |

## `install-bader`

安装固定版本的官方 Bader 程序。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `-o`, `--output` | 否 | `.tools/bader` | 输出文件或目录，见下方说明。 |

## `demo`

生成合成教学数据。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `-o`, `--output` | 否 | `fermi-demo` | 输出文件或目录，见下方说明。 |

## `render`

将数值场绘制为 PNG 或 TIFF。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `field` | 是 | — | 软度体数据，推荐原生 .npz。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |
| `--charge` | 否 | — | 电荷密度；包络面和电子数使用原始 SCF 密度。 |
| `--scene` | 否 | — | 保存的场景 JSON，包含相机和样式。 |
| `--mode` | 否 | —; `softness`, `charge`, `slice` | 显示方式；省略时保留场景或默认设置。 |
| `--width` | 否 | `3600` | 图片宽度，单位像素。 |
| `--height` | 否 | `2600` | 图片高度，单位像素。 |
| `--dpi` | 否 | `300` | 图片 DPI 元数据。 |

## `animate`

将旋转视图导出为 MP4 或 GIF。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `field` | 是 | — | 软度体数据，推荐原生 .npz。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |
| `--charge` | 否 | — | 电荷密度；包络面和电子数使用原始 SCF 密度。 |
| `--scene` | 否 | — | 保存的场景 JSON，包含相机和样式。 |
| `--width` | 否 | `1920` | 图片宽度，单位像素。 |
| `--height` | 否 | `1080` | 图片高度，单位像素。 |
| `--fps` | 否 | `30` | 动画帧率，1–60 帧/秒。 |
| `--seconds` | 否 | `12` | 动画总时长，0.25–120 秒。 |
| `--turns` | 否 | `1` | 完整旋转圈数，1–10。 |
| `--axis` | 否 | `normal`; `normal`, `view`, `x`, `y`, `z` | 旋转轴：表面法线、初始视图上方向，或笛卡尔 x/y/z。 |
| `--reverse` | 否 | `False` | 反转旋转方向。 |
| `--no-fit` | 否 | `False` | 保持精确构图；默认自动取景以容纳完整旋转。 |

## `integrate`

对已经与网格对齐的外部分区积分。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `field` | 是 | — | 软度体数据，推荐原生 .npz。 |
| `--labels` | 是 | — | 与场几何及网格一致的整数 .npy 标签，0 可表示真空。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## `bader`

根据电荷生成 Bader 分区并积分软度。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `field` | 是 | — | 软度体数据，推荐原生 .npz。 |
| `--reference` | 是 | — | 一个参考密度文件，或相加使用的 AECCAR0 AECCAR2。 |
| `--charge` | 否 | — | 电荷密度；包络面和电子数使用原始 SCF 密度。 |
| `--executable` | 否 | — | Bader 可执行文件；省略时查找环境变量、PATH 或本地安装。 |
| `--vacuum` | 否 | `off`; `off`, `auto` | Bader 真空分类；off 将整个晶胞分配给原子。 |
| `--surface-atoms` | 否 | — | 用于表面层求和的原子编号，从 1 开始。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## `select-basins`

保存仅包含所选原子区域的软度场。

| 参数 | 必填 | 默认值 / 可选值 | 含义 |
|---|---|---|---|
| `-h`, `--help` | 否 | — | 显示命令帮助并退出。 |
| `field` | 是 | — | 软度体数据，推荐原生 .npz。 |
| `--basins` | 是 | — | Bader 流程生成的 basins.npz。 |
| `--atoms` | 是 | — | 一个或多个原子编号，从 1 开始。 |
| `-o`, `--output` | 是 | — | 输出文件或目录，见下方说明。 |

## 输出目标与运行顺序

`compute`、`compute-parchg` 和 `compute-frozen` 的输出是结果目录；`prepare-*` 的输出是供 VASP 运行的目录。准备命令不会自动运行 VASP。

`demo` 输出示例目录；`install-bader` 输出程序安装目录；`bader` 输出分析目录。`render` 输出 PNG/TIFF 文件；`integrate` 输出 JSON；`select-basins` 输出 NPZ。

`gui --demo` 打开合成示例；实际材料用 `gui --example pt111` 或 `gui --example pt3y111`。不要同时给出互相竞争的数据入口。

外部标签积分不自动寻找 Bader 边界：`integrate` 需要已经对齐的体素标签；只给 ACF.dat 不够。需要生成分区时使用 `bader`。

`--allow-incomplete` 与 `--allow-reduced` 生成明确标记的诊断结果，不能用于替代足够空带和正确对称性设置。完整实例和错误处理见使用手册。
