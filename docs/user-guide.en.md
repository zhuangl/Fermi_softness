# Fermi Softness 0.2.0 — complete user guide

[中文](user-guide.zh-CN.md) · [Documentation index](index.md) · [CLI reference](cli-reference.en.md)

## 1. What the software does

Fermi Softness converts VASP electronic states into a spatially resolved surface
reactivity descriptor. It provides a command line, a Python API and a desktop GUI,
**Fermi Softness Studio**. The method is from Huang, Xiao, Lu and Zhuang,
[Angew. Chem. Int. Ed. 55, 6239–6243 (2016)](https://doi.org/10.1002/anie.201601824).

You can calculate three-dimensional fields, inspect periodic surfaces, integrate
atomic Bader basins, and export numerical volumes and publication figures. This
release is a standalone VASP postprocessor. The Fortran directory contains an
integration kernel, not a ready-to-compile patch for a particular VASP version.

## 2. Installation

Python **3.10 or newer** is required. Python 3.11 on macOS arm64 is the locally
validated desktop environment. VASP 6.4.2 on Linux supplied the native-density
benchmarks. Other Python/platform combinations are covered by the repository CI
configuration; see its actual run status before treating them as tested.

Clone the repository or unpack the source archive, then enter its directory:

```sh
git clone https://github.com/zhuangl/Fermi_softness.git
cd Fermi_softness
python -m venv .venv
```

Activate the environment using your shell:

```sh
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```sh
python -m pip install --upgrade pip
python -m pip install ".[gui]"
fermi-softness --version
fermi-softness gui --example pt3y111
```

For a server without graphics, install with `python -m pip install .`. To install
a downloaded wheel, use `python -m pip install "./fermi_softness-0.2.0-py3-none-any.whl[gui]"`.
Dependencies may be downloaded during installation. No PyPI publication is
assumed. After installation, the bundled demos need no network or VASP.

On macOS, the repository's `Fermi Softness Studio.command` launcher uses the
`.venv` in that repository. Other installations should use `fermi-softness gui`
or `python -m fermi_softness gui`. On Windows, calling
`.venv\Scripts\python.exe -m fermi_softness gui` also avoids shell activation.

The GUI and image renderer need a working graphics context. On Linux, use a
desktop session or a configured X/EGL/OSMesa environment. A plain SSH terminal
is sufficient for calculation, but not necessarily for rendering.

## 3. Explore the offline demos

```sh
fermi-softness demos
fermi-softness gui --example pt111
fermi-softness gui --example pt3y111
fermi-softness gui --example pt111-bader
fermi-softness gui --example analytic
```

In the GUI, select a dataset in **Data** and click **Open selected demo**.

| ID | Contents | Scientific status |
|---|---|---|
| `pt111` | Native VASP Pt(111) field and charge envelope | Small software benchmark: PBE, three layers, 1×1 cell, 400 eV, 4×4×1 k mesh; not the paper's Pt model |
| `pt3y111` | Four-layer PW91 Pt₃Y(111), charge and refined Bader basins | Paper reconstruction; Pt-high/Y-low contrast reproduced, strict absolute-value agreement not passed |
| `pt111-bader` | One surface atom selected from the Pt demo | A basin-restricted view of the same Pt dataset |
| `analytic` | Analytic Pt/Y-like illustration | Synthetic teaching data, not DFT |

The Pt₃Y view uses the original 1–28 keV⁻¹ Å⁻³ color scale. Sampled Pt values
reach about 43 keV⁻¹ Å⁻³, so that scale saturates. Changing the palette or limits
does not establish agreement with the original calculation.

## 4. Choose a calculation route

| Route | Input and extra calculation | Representation / supported systems |
|---|---|---|
| `compute` | Matching WAVECAR + vasprun.xml; no additional VASP job | Smooth PAW pseudo-wavefunction field; scalar, collinear and spinor inputs |
| `prepare-parchg` → VASP → `compute-parchg` | Prepared state-resolved density export; potentially many files | VASP native augmented valence density; scalar and collinear spin |
| `prepare-frozen` → VASP → `compute-frozen` | One compact weighted-density export | Same native density construction; nonmagnetic scalar only, validated on VASP 6.4.2 |

Use the direct route to inspect existing wavefunctions. For native augmented
densities in a nonmagnetic system, the compact route avoids thousands of PARCHG
files. The separated PARCHG route also provides a useful independent check.
Neither native route is a full all-electron orbital reconstruction. Comparisons
between materials should use the same representation and converged DFT settings.

## 5. Prepare the source VASP calculation

Start from a relaxed geometry and run a converged static calculation. Choose
the functional, potentials, plane-wave cutoff, slab thickness, vacuum and k mesh
for the physical problem. The following are relevant settings, not a complete
universal INCAR:

```text
NSW    = 0
IBRION = -1
LWAVE  = .TRUE.
LCHARG = .TRUE.
ISYM   = -1
PREC   = Accurate
LREAL  = .FALSE.
# For Bader reference densities:
LAECHG = .TRUE.
# Set NBANDS to cover the full softness window.
```

Keep `WAVECAR`, `vasprun.xml`, `INCAR`, `POTCAR`, `CHGCAR` and, if requested,
`AECCAR0`/`AECCAR2` from that source calculation together. Do not mix files from
different geometries or calculations. Retain the source KPOINTS and OUTCAR for
your own reproducibility record. POTCAR remains local to your licensed setup.

Scalar calculations can also use `ISYM=0`; spinor calculations require `ISYM=-1`
in this release. General space-group expansion of irreducible k points is not
implemented. A conventional `ISYM=2` result must be recalculated with suitable
symmetry settings for a quantitative local map.

The default descriptor parameter is **kT = 0.4 eV**, independently of the SCF
smearing `SIGMA`. The default absolute kernel cutoff is **0.001 eV⁻¹**, giving
an energy window of approximately **EF ± 3.1293 eV**. Include enough empty bands
at every k point and spin. The software checks both ends of this window; if the
upper edge is missing, increase NBANDS and rerun the static calculation.

## 6. Direct WAVECAR workflow

The examples below use `source-run/` for the original VASP directory:

```sh
fermi-softness inspect source-run/WAVECAR
fermi-softness compute --wavecar source-run/WAVECAR \
  --vasprun source-run/vasprun.xml --kt 0.4 --threshold 0.001 \
  -o smooth-softness
fermi-softness gui smooth-softness/softness.npz --charge source-run/CHGCAR
```

`inspect` reports the file format and recommended FFT grid. Allow automatic
grid selection initially. A user-supplied `--grid NX NY NZ` must pass the density
aliasing check. Increasing the grid samples the existing plane-wave expansion
more finely; it does not increase ENCUT or restore PAW augmentation.

The direct engine streams states. `--max-memory-gb` controls its working-memory
estimate (default 4 GB), not the operating system's total process memory. Legacy
Gamma files using z-half storage need `--gamma-half z`. The default is x-half.

GUI equivalent: choose the two source files in **Data**, set **kT**, **Cutoff**
and optionally **FFT grid**, then click **Calculate softness**. This button uses
the direct smooth-wavefunction route. Progress is shown below; cancellation takes
effect after the current processing unit. Save the completed field in **Export**.

## 7. Native VASP density workflows

Keep native export jobs in separate directories. Always read the generated
`RUN.md`; run VASP using your normal licensed executable and scheduler.

### Compact nonmagnetic export

```sh
fermi-softness prepare-frozen --wavecar source-run/WAVECAR \
  --vasprun source-run/vasprun.xml --incar source-run/INCAR \
  --kt 0.4 -o compact-deck
cp source-run/WAVECAR source-run/POTCAR compact-deck/
# Run VASP in compact-deck, following compact-deck/RUN.md.
fermi-softness compute-frozen compact-deck/manifest.json -o native-softness
fermi-softness gui native-softness/softness.npz --charge source-run/CHGCAR
```

Preparation creates the geometry, explicit k points, controlled INCAR, manifest
and run instructions. The source INCAR preserves relevant settings such as the
functional. Do not replace the generated deck with a generic SCF INCAR.
Use a parallel layout that preserves NBANDS. The fixed-orbital tags and temporary
occupations are necessary for this export; they are checked during import.

The export's CHGCAR contains a mathematical weighted density. It is **not the
ground-state charge density**. Use the original `source-run/CHGCAR` for the 95%
envelope, and original AECCAR files for Bader boundaries. Do not use the export's
energy, Fermi level or electron count as a new physical SCF result.

### State-resolved PARCHG export

```sh
fermi-softness prepare-parchg --wavecar source-run/WAVECAR \
  --vasprun source-run/vasprun.xml --incar source-run/INCAR \
  --kt 0.4 -o parchg-deck
cp source-run/WAVECAR source-run/POTCAR parchg-deck/
# Run VASP in parchg-deck, following parchg-deck/RUN.md.
fermi-softness compute-parchg parchg-deck/manifest.json -o parchg-softness
```

The deck uses LPARD, LSEPB, LSEPK and KPAR=1. Keep the separate band/k-point
files and manifest together. One PARCHG summed over an energy window cannot
replace these files. Gzipped individual PARCHG files are accepted.

In the GUI, select **Native: state-resolved PARCHG** or **Native: compact fixed
orbitals (nonmagnetic)**, click **Prepare native VASP densities…**, run the job
externally, then use **Combine native densities…**. The GUI does not submit jobs
to your cluster. See [native export details](native-export.md).

## 8. Bader atomic and surface softness

The Bader boundary is defined by a reference charge density. Softness is then
integrated inside each atomic volume. The recommended VASP reference is the sum
of the original `AECCAR0` and `AECCAR2`. Supply the original CHGCAR separately
when you want valence electron populations.

```sh
fermi-softness install-bader
fermi-softness bader native-softness/softness.npz \
  --reference source-run/AECCAR0 source-run/AECCAR2 \
  --charge source-run/CHGCAR --surface-atoms 1 7 10 13 \
  -o atomic-softness
```

Automatic installation downloads the checksum-verified Henkelman Bader 1.05
binary for macOS arm64 or Linux x86_64. Elsewhere, compile the official program
and pass `--executable /path/to/bader`, or set `FERMI_SOFTNESS_BADER`. The default
installer directory is `.tools/bader` relative to the current working directory;
an explicit path is useful if you launch the GUI elsewhere.

Atom IDs are **one based**, in the field's stored structure order. The IDs above
are the bundled Pt₃Y top layer, not a general surface selector. Omit
`--surface-atoms` to get atomic values without a surface sum. The program does
not silently divide the selected sum by area or atom count.

The default `--vacuum off` assigns all grid points to atomic basins. `--vacuum
auto` allows Bader's vacuum classification and reports its softness separately.
Reference and field cells, origins and atomic structures must agree. A finer
reference grid is supported by periodic Fourier interpolation of the softness
field; the reference is not silently coarsened. Repeat with a finer reference
to check atomic-value convergence.

The output includes `atoms.csv`, `report.json`, `basins.npz`,
`softness-on-bader-grid.npz`, and the original Bader `ACF.dat`, `AtIndex.dat` and
log. The field integral is checked against atomic plus vacuum contributions.
Valence electron populations are not automatically net atomic charges.

```sh
fermi-softness select-basins native-softness/softness.npz \
  --basins atomic-softness/basins.npz --atoms 1 7 10 13 \
  -o surface-only.npz
fermi-softness gui surface-only.npz --charge source-run/CHGCAR
```

In **Bader**, choose reference files, executable and **Output parent**; output
is written to its `bader-result` subdirectory. Click **Calculate atomic softness**.
Select table rows and use **View selected atom basins**, **View recorded surface
layer** or **Restore full field**. A selected field is zero outside the chosen
basins and is labeled accordingly. The export buttons save the current field.
See the [Bader reference](bader.md) for boundary and normalization details.

## 9. Build a figure in Studio

![Studio showing the Pt3Y reconstruction](images/studio-pt3y.png)

Actual desktop view of the packaged Pt₃Y reconstruction. The tabs separate data,
scene, style, atomic analysis and export controls.

1. In **Data**, open `softness.npz` and load the original charge density if needed.
2. In **Scene**, select a display mode and click **Apply view**.
3. Rotate by dragging, pan with Shift-drag, and zoom with the wheel. Use the
   orientation buttons or orthographic projection to compose the view.
4. In **Style**, choose a palette, colorbar layout, range, units and background.
5. Save the scene with **Save view…**, then export the figure in **Export**.

| Control | Meaning |
|---|---|
| Softness isosurface / Softness level | Constant local softness; level uses the selected eV or keV display units |
| Charge surface · softness colors | Charge isosurface colored by local softness |
| Enclosed charge | Default 0.95; a cumulative density threshold enclosing 95% of the charge |
| Charge level | Optional explicit isovalue in Å⁻³; overrides the enclosed-charge threshold |
| Planar section / Plane normal / Plane fraction | Plane along the selected a/b/c direction at a fractional position |
| Supercell a b c | Periodic display repeats, not a new electronic calculation |
| Cell view origin | Fractional periodic shift of the displayed cell cut |
| Display stride | Coarser display sampling for interactivity; use 1 for final figures |
| Fit color range to visible surface | Automatic range; disable for material-to-material comparisons |
| Orthographic projection | Parallel projection without perspective foreshortening |

**Style** offers Scientific light, Paper 2016, Presentation dark and Grayscale
print presets. Colorbars can be horizontal, vertical, compact, endpoint-only or
hidden. Fonts, tick counts, numeric formats and palette reversal are adjustable.
The Paper 2016 preset changes style; it does not transform a dataset into the
paper's result or automatically establish its numerical color limits.

Local softness is stored in eV⁻¹ Å⁻³. Switching to keV⁻¹ Å⁻³ multiplies displayed
values by 1000, without changing the saved field. A softness isosurface level
and color limits follow that display conversion; charge levels remain in Å⁻³.

For comparable figures, hold the field representation, kT, envelope definition,
color scale and units fixed. State those choices in the figure caption.

## 10. Export figures and numerical data

In **Export**, set pixel width/height, DPI and optional transparency, then use
**Export PNG or TIFF…**. For example, 4800×3600 pixels at 600 DPI corresponds to
8×6 inches. DPI metadata alone does not add detail; the actual pixels determine
image resolution. The numerical grid separately determines spatial sampling.

The current camera and display settings are saved beside the image as
`figure.png.scene.json` (or the equivalent TIFF name). A scene contains display
settings, not the field itself. Preserve the field and any charge input as well.

```sh
fermi-softness render native-softness/softness.npz \
  --charge source-run/CHGCAR --scene view.json \
  --width 4800 --height 3600 --dpi 600 -o figure.png
```

`view.json` is produced by **Save view…**; an exported image's scene sidecar also
works. Without a scene, the renderer uses its defaults. The CLI provides size,
DPI and mode overrides; additional style/camera settings are carried by the scene.

**Save field (.npz)…** preserves geometry, units and metadata. **Export Cube for
VMD / VESTA…** writes a volume usable by external viewers. Cube coordinates are
in Bohr, and scalar units are stated in the comment. Check units when importing
third-party Cubes: a Cube file does not have a universally enforced scalar-unit
convention. Native NPZ is preferable for quantitative interchange.

## 11. Understand and preserve the results

| File / quantity | Meaning |
|---|---|
| `softness.npz` | Field, cell, positions, species, origin and JSON metadata |
| `softness.cube` | Numerical volume for interchange |
| `metadata.json` | Calculation settings, representation, checks and provenance |
| `softness_up.npz`, `softness_down.npz` | Separate collinear-spin contributions where provided |
| Field integral | Whole-cell real-space softness, eV⁻¹ |
| Spectral softness | Weighted eigenstate sum, eV⁻¹ |
| Atomic / selected-layer softness | Integral within recorded Bader volumes, eV⁻¹ |

The direct smooth-field integral may differ from the spectral sum because PAW
augmentation is absent. Do not force agreement by renormalizing wavefunctions.
The native routes check the appropriate integral agreement, but this check does
not prove k-point, slab or cutoff convergence. Native PAW charge augmentation
can also give local core-region values that should not be interpreted as a
fully reconstructed all-electron probability density.

Keep the package version, source VASP inputs and outputs, manifests, numerical
fields, Bader reports and scene JSON together in your research archive. Public
sharing should omit VASP source and POTCAR; this project distributes neither.
Result-writing commands protect existing target results; choose a new directory
for reruns. GUI save/export dialogs can overwrite a file when you confirm it.

## 12. Troubleshooting

| Symptom | Action |
|---|---|
| `fermi-softness` not found | Activate the environment or run `python -m fermi_softness`; verify installation with that same Python |
| Qt/VTK import failure | Install the `gui` extra in the active environment |
| Blank view / graphics-context error | Use a working desktop or graphics backend; verify an offline demo before investigating the data |
| No surface visible | Choose an isovalue within the data range, load charge for charge mode, and restore a useful camera |
| Upper energy window not covered | Increase NBANDS and rerun the source static calculation |
| Reduced k-point set rejected | Recalculate with ISYM=-1 (or supported scalar ISYM=0) |
| Unconverged or inconsistent files | Use matching outputs from one converged static run; do not use an extrapolated MD WAVECAR |
| Requested grid rejected | Use the recommended grid or larger dimensions; do not bypass the aliasing check |
| Native export failed / NBANDS changed | Follow RUN.md, retain source INCAR settings and use a parallel layout preserving the band count; PARCHG uses KPAR=1 |
| Native integral mismatch | Check the original WAVECAR fingerprint and matching potentials, state files and manifest; do not rescale to conceal the mismatch |
| Bader program not found | Install it or give an explicit executable path; check compiler runtime availability |
| Bader geometry/grid mismatch | Use original same-structure reference densities on a sufficiently fine grid |
| Image changes after switching datasets | Disable automatic color scaling and use a shared range and envelope definition |
| High memory use | Reduce display repeats/preview sampling first; keep final numerical precision and plotting resolution distinct |

`--allow-incomplete` and `--allow-reduced` are diagnostic options, not repairs
for missing bands or missing symmetry operations. Their output is marked as
diagnostic. Report problems using the [contribution guide](../CONTRIBUTING.md).

## 13. Validation and citation

Read [validation](validation.md) before interpreting a demo as a reproduction.
The current Pt₃Y case passes qualitative contrast and internal consistency;
strict original DACAPO agreement remains open. The full original material series,
MoS₂ edges and adsorption-energy correlations have not been reproduced here.

Research use of this software or method must cite the
[2016 method](https://doi.org/10.1002/anie.201601824); see the
[citation requirement and BibTeX](../CITING.md). Also identify the
software version or Git commit. For your calculation, report kT, absolute kernel
cutoff, DFT settings, density representation, Bader reference/grid and figure
scale. [CITATION.cff](../CITATION.cff) contains bibliographic metadata; the
[scientific conventions](science.md) explain the implementation in detail.
