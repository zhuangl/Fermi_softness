# Validation record — 2026-10-08

[中文](validation.zh-CN.md) · [User guide](user-guide.en.md)

Version 0.2.0 was exercised locally on macOS arm64 / Python 3.11, and against
VASP 6.4.2 output generated on Linux. The checks below have actually run.
Hosted Python/platform and Fortran checks are tracked in the repository's
[GitHub Actions runs](https://github.com/zhuangl/Fermi_softness/actions).
The matrix configuration alone is not evidence of a passing run.

| Area | Evidence | Scope |
|---|---|---|
| Scientific unit/integration tests | 51 tests pass | Kernel, normalization, spin, Gamma, skew cells, units, Bader boundaries, compact export, demos and periodic display origin |
| Public VASP fixtures | 6 valid real-file cases | Standard, collinear, Gamma, spinor, fractional ENCUT |
| Independent reader | All bands compared to pymatgen | Standard/spinor coefficient differences zero; Gamma maximum 2.93e-8 |
| Pt(111) static run | VASP 6.4.2, 27 SCF steps | 3 atoms, 400 eV, full 4x4x1 mesh, 48 bands |
| Pt(111) direct reconstruction | 161 selected states | Four points agree with independent pymatgen sums to 1.87e-9 eV^-1 Å^-3 |
| Pt(111) native density route | 161 VASP-separated PARCHG grids | Augmented-field integral and spectral sum agree to 5.60e-8 relative |
| Desktop rendering | Actual Qt/VTK execution | Rotation, three display modes, saved camera, PNG/TIFF, transparency, pixel sizes and DPI |
| Fortran kernel | gfortran 12.3, runtime checks | Compiled standalone accumulation kernel and numeric driver pass |

## Retina export correction in 0.3.1

The original GUI export checks covered file dimensions, frame counts and camera
restoration, but missed partial framebuffer capture on Retina displays. Version
0.3.1 adds `validation/gui_export_pixels.py`, which decodes actual GUI-exported
MP4/GIF frames and compares their content with independent full-frame references.
The check covers 640×480 and 1920×1080 video plus transparent PNG, and rejects the
old cropped GUI output. The interactive camera and viewport remain untouched.
[Pixel comparison results](../results/retina-export-validation.json).

## Pt₃Y and Bader in 0.2

The four-layer Pt12Y4 reconstruction completed PW91 relaxation and a static
VASP 6.4.2 calculation. The maximum force on free atoms is 0.02908 eV/Å,
below the paper's 0.05 threshold. On the 95% charge envelope, the sampled Pt
sites average 43.15 keV^-1 Å^-3 and the Y site is 6.145, a ratio of 7.02.
The qualitative Pt-high/Y-low contrast is reproduced. The final DACAPO
numerical grid/generation script has not been recovered; the numerical
comparison therefore uses the available publication and archived materials.

The native field integral is 12.7772506167 eV^-1 versus a spectral sum of
12.7772506575 eV^-1 (3.19e-9 relative difference). Bader labels are checked
against ACF.dat integrals, and their softness sum conserves the whole field.
An unequal-Gaussian test verifies a density-defined boundary rather than a
nearest-atom partition. Reference/grid sensitivity reports are recorded in
`results/pt3y-bader-reference-check.json` and `results/pt3y-bader-gridcheck.json`.
Conservation is an implementation check, not proof of physical convergence.

## Real Pt(111) numbers

- Spectral softness: **3.495596548626371 eV⁻¹**.
- Direct smooth-field integral: **1.981707525481817 eV⁻¹**.
- Native VASP density integral: **3.4955963530178686 eV⁻¹**.
- Maximum individual native-state normalization error: **1.28e-6 electrons**.

The difference between the smooth integral and the spectral result is not
removed by arbitrary normalization. The native route includes VASP's charge
augmentation. The independent point evaluator uses complex64 phases, which
accounts for the small pointwise reference difference.

The integration benchmark is intentionally small. It validates the software
pipeline, not k-point convergence, adsorption-energy correlations, or the
original DACAPO results. `results/pt111-validation.json` contains the numerical
report and `validation/pt111` contains redistributable input geometry/settings.
POTCAR and VASP source are not distributed.

## Public fixture provenance

`validation/public-fixtures.json` pins the upstream Git revision and every
SHA-256 checksum. `fetch_public_fixtures.py` verifies them before writing files.
The actual binary fixtures remain outside the source distribution.

The public file named `WAVECAR.N2.45210` has a record size too small for the
declared double-precision coefficients; our reader rejects it. It is not used
as evidence for real double-precision compatibility. Double precision,
big-endian data, legacy Gamma z-half storage and multi-record headers are
tested with independent generated fixtures. The public malformed-tag file is
also intentionally rejected.

## Checks still needed for a broader release

- Original paper case reproduction: Pt3Y, MoS2 edge and the metal series.
- Real collinear-spin **native PARCHG** campaign; its weighting/splitting is
  currently validated with generated inputs, while the real native benchmark
  is non-spin-polarized Pt.
- More VASP versions, operating systems, and vendor/compiler combinations.
- Full all-electron reconstruction and version-specific in-VASP integration.
- General magnetic space-group reconstruction and native HDF5 wavefunction input.

The article's methods and figures were checked. The public SI URL returned
HTTP 403, but the author's local eight-page `SI_Fermi Softness.pdf` was later
found and inspected, along with an earlier computational-methods draft.
The final SI contains supplemental figures and data tables; Bader integration
is already specified in the main Experimental Section. The located Pt₃Y
volume is an early finite-difference Fukui field, not a substitute for the
final Fermi-softness reference.

## Operational record

The first Slurm job completed the static calculation and the Fortran tests,
then its LPARD stage failed because KPAR>1 is unsupported by VASP 6.4.2. The
static output was preserved. The LPARD stage was rerun with KPAR=1 and completed.
A subsequent native-density campaign completed all 161 selected states.
All compute workdirs were on node-local scratch. Results went directly to the
login node's `/home` archive, with only inputs and lightweight logs on `/store`.

Final Pt3Y refinement from 80×80×320 to 160×160×640 changes atomic softness by at most 0.4352%, and the selected surface-layer sum by 0.0147%. The packaged Bader basins use the refined reference.
