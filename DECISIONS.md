# Decisions

## 2026-10-08 — implementation route

Use a standalone Python package as the primary deliverable. This allows users
to analyze existing calculations without modifying their licensed VASP build.
Use NumPy/SciPy for computation and PyVista/VTK with Qt for local interactive
rendering. Use a streaming WAVECAR reader so memory does not scale with the
number of selected bands. Provide a Fortran kernel as a separate integration
component, not an unverified version-specific patch.

## Scientific conventions

Use kT in eV, default 0.4. The derivative kernel includes both occupied and
unoccupied states and must not be multiplied by the SCF occupation again.
Preserve WAVECAR coefficients: PAW pseudo-wavefunctions are not generally
unit-normalized under the ordinary inner product. Report smooth-field integral
and spectral softness separately. Fine FFT sampling improves spatial sampling;
it does not recover missing PAW augmentation or missing bands.

Require ISYM=-1 for spinors, or ISYM=-1/0 for scalar collinear calculations.
Do not infer the magnetic space group from geometry alone. General symmetry
reconstruction is deferred until it can be validated against VASP's actual
operations. An explicitly labeled diagnostic override may retain a reduced
set, but its field is not a production result.

## Native PAW charge route

Real VASP validation showed the importance of augmentation in the near-nuclear
region. Add `prepare-parchg` and `compute-parchg` as a second supported path.
VASP constructs per-state densities; the toolkit applies spectral weights and
verifies normalization. Keep its provenance distinct from direct smooth
WAVECAR reconstruction. The additional VASP pass needs KPAR=1 and explicit
band/k separation. A plain energy-window PARCHG cannot substitute for it.

## 2026-10-09 — first GitHub archive

Publish the current research release with complete English and Chinese
documentation. Keep quantitative reproduction limits visible on both landing
pages and in the release notes. Include derived demonstration fields and
redistributable input structures; exclude private source archives, licensed
calculation files and machine-specific operation records. Generate the CLI
reference from the parser so documentation stays synchronized with the commands.
