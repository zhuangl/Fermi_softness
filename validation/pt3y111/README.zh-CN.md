# Pt₃Y(111) 验收算例

[English](README.md) · [验证记录](../../docs/validation.zh-CN.md)

从作者历史 Pt₃Y 电荷 Cube 恢复 Pt12Y4 四层结构，保留晶格和真空，将表面平移离开
周期边界，固定底部两层并弛豫顶部两层。源 Cube 的 3×3 重复胞包含 1476 个价电子，
即每个基础胞 164 个，与此处的 Y_sv/Pt 选择一致。

按原文已知设置使用 PW91、408 eV、6×6×1 Monkhorst–Pack、SCF Fermi 展宽 0.1 eV、
受力阈值 0.05 eV/Å。电子结构程序改为 VASP 6.4.2 PAW，区别于原稿 DACAPO 超软赝势。
自行合法准备 Y_sv、Pt，按这一元素顺序拼接 POTCAR；仓库不提供 POTCAR。

将 `INCAR.relax`、`POSCAR.initial` 分别复制为运行目录中的 INCAR、POSCAR，配合
KPOINTS 完成弛豫。之后在独立静态目录把 CONTCAR 作为 POSCAR，设置 NSW=0、
IBRION=-1、EDIFF=1e-8、ISTART=1、ICHARG=1、LAECHG=.TRUE.，并使用匹配的
WAVECAR/CHGCAR 继续静态计算。

使用独立程序或紧凑原生路线在 kT=0.4 eV 重建，再以原始静态 AECCAR0+AECCAR2
做 Bader 分区。当前原子顺序中的顶部原子为 1、7、10、13。

原生结果在 95% 电荷包络面的 Pt/Y 软度反差约为 7.02，场积分与谱求和相对差异
3.19×10⁻⁹。通过定性反差和软件一致性检查；严格原稿复现**尚未通过**，绝对值不同，
最终 DACAPO 软度场和生成脚本尚未恢复。详见[报告](../../results/pt3y-validation.json)。
