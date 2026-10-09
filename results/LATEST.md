# Fermi Softness 0.2.0 — release preparation 2026-10-09

Implemented: four style presets, five colorbar layouts, display units/fonts,
offline Pt(111)/Pt3Y/Bader/tutorial demos, genuine Henkelman near-grid Bader
partitioning, atomic tables and selection, and compact native VASP density export.

51 scientific tests pass locally. GUI checks cover styles, unit invariance,
all packaged demos, Bader surface selection/restore, and native background workers.

Pt3Y benchmark: PW91, 408 eV, four-layer Pt12Y4, 6x6x1, 144 bands. Free-atom
forces reach 0.02908 eV/Angstrom. Native softness integral matches the spectral
sum to 3.19e-9 relative. Pt/Y outer-surface contrast is 7.02 (qualitative PASS).
Strict original DACAPO reproduction is NOT PASSED: absolute values differ and
no final original softness grid or generation script has been recovered.

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
- docs/images/pt3y-reconstruction.png: original-scale reconstruction, not strict reproduction
- results/local/gui-v02/: actual GUI/export acceptance evidence
- dist/: 0.2.0 install/source archives after final build

All validation calculations are complete. Operational details and raw outputs
are maintained outside the public source archive. Git/GitHub archiving of this
release was authorized on 2026-10-09; release verification is recorded separately.

The final 0.2.0 wheel was installed with GUI dependencies in a clean environment; all 51 tests pass there. Release archives include portable demos and exclude raw research files, VASP source, POTCAR, WAVECAR and external Bader binaries.
