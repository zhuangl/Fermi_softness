# Fermi Softness 0.2.2 — desktop application 2026-10-09

The macOS installer creates Fermi Softness Studio.app with the transparent Pt3Y
icon, registers it with LaunchServices and uses the existing Python environment.
The installed application was opened through macOS and its 0.2.2 window and Pt3Y
example were observed. There are 54 passing local tests, including environment
path preservation, safe app updates and refusal to overwrite unrelated apps.
See docs/desktop-app.md for installation and everyday launch instructions.

Implemented: four style presets, five colorbar layouts, display units/fonts,
offline Pt(111)/Pt3Y/Bader/tutorial demos, genuine Henkelman near-grid Bader
partitioning, atomic tables and selection, and compact native VASP density export.

51 scientific tests pass locally. GUI checks cover styles, unit invariance,
all packaged demos, Bader surface selection/restore, and native background workers.

Pt3Y benchmark: PW91, 408 eV, four-layer Pt12Y4, 6x6x1, 144 bands. Free-atom
forces reach 0.02908 eV/Angstrom. Native softness integral matches the spectral
sum to 3.19e-9 relative. Pt/Y outer-surface contrast is 7.02 (qualitative PASS).
Detailed parameters and comparisons with the original calculation are retained
in the scientific validation records.

Refined Bader reference: 160x160x640. Compared with 80x80x320, maximum atomic
softness change is 0.4352%; surface-layer sum changes 0.0147%. Refined surface
sum: 3.5368470781 eV^-1. Its basin sum conserves total softness to 3.55e-14.
Reference choice and grid checks are separate from numerical conservation.

The local eight-page SI_Fermi Softness.pdf was found and read. Bader is already
specified in the main Experimental Section. The archived Pt3Y Cube is an early
finite-difference Fukui result and is not substituted for Fermi softness.

Important artifacts:
- docs/index.md: paired English/Chinese user, CLI, science, Bader and developer documentation
- results/pt3y-validation.json, results/pt3y-bader-refinement.json
- src/fermi_softness/data/: portable offline examples and refined basin labels
- docs/images/pt3y-reconstruction.png: VASP reconstruction with the original color scale
- results/local/gui-v02/: actual GUI/export acceptance evidence
- dist/v0.2.2/: desktop installer release archives

All validation calculations are complete. Operational details and raw outputs
are maintained outside the public source archive. Git/GitHub archiving of this
release was authorized on 2026-10-09; release verification is recorded separately.

The final 0.2.0 wheel was installed with GUI dependencies in a clean environment; all 51 tests pass there. Release archives include portable demos and exclude raw research files, VASP source, POTCAR, WAVECAR and external Bader binaries.

0.2.1 updates the Pt3Y presentation text, desktop screenshot and release documentation. Numerical datasets and calculation routines are unchanged.
