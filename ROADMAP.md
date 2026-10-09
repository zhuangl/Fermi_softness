# Fermi Softness — delivery and acceptance plan

Started 2026-10-08. The objective is an installable, open-source-ready tool that
turns VASP results into quantitative local Fermi-softness fields and publication
images. Repository files are the durable record of work and acceptance.

## 1. Method contract

- Verify the 2016 paper, obtain its supporting information, record equations,
  units, cutoff convention, spin/k-point factors, and surface integration.
- Distinguish a finely sampled smooth PAW field from an all-electron field.
- Keep source documents and licensed calculation files out of release archives.

## 2. Standalone calculation

- Stream standard complex WAVECAR coefficients; handle collinear spin, Gamma
  half-storage and spinors with explicit format checks.
- Cross-check structure, energies and k-points against vasprun.xml.
- Refuse silent use of spatially reduced k-point sets, missing unoccupied bands,
  undersampled FFT grids, incompatible files, and unsupported formats.
- Provide numerical metadata, spectral and real-space integrals, Cube and
  native archive export, region integration, and a reproducible command line.

## 3. Integrated visualization

- Desktop GUI: file selection, calculation progress, rotatable 3D view, soft-
  ness isosurface, charge-density surface colored by softness, plane slices,
  supercells, atoms, adjustable ranges, orthographic camera, saved scene.
- PNG/TIFF export with explicit pixel size and DPI; retain a VMD-compatible
  Cube interchange route.
- Synthetic demonstration data must be clearly identified; real datasets must
  state their calculation provenance and validation scope.

## 4. Verification

- Analytic plane waves and interference, independent real-space Fourier sum,
  spin and k-point factors, PAW coefficient norms, gamma packing, skew cells,
  periodic grid ordering, malformed inputs and unit conversion.
- Real public VASP fixtures with provenance; compare against an independent
  reader and reference charge data where available.
- Inspect actual rendered images and GUI; build and install release artifacts.
- Real surface production benchmark and original DACAPO reproduction are
  separate acceptance gates, not implied by synthetic or file-reader tests.

## 5. In-VASP route

- Supply an original, portable Fortran accumulation kernel and a precise
  integration contract. Never ship VASP source or POTCAR.
- A version-specific in-VASP adapter requires the selected licensed source,
  PAW density hooks, MPI/grid mapping, and a compiled regression run. Do not
  describe an unintegrated kernel as a working VASP plugin.

## 6. Release

- English and Chinese quick starts, scientific conventions, tutorials,
  reference citations, contribution guide, license and CI.
- GitHub publication and Git archiving authorized on 2026-10-09, with complete
  English and Chinese usage and software documentation.

Progress and exact acceptance evidence: `results/LATEST.md`.

## Acceptance update — 2026-10-08

The standalone 0.1.0 package, desktop GUI, direct WAVECAR backend, native VASP
LPARD backend, documentation, local Git repository and installation artifacts
are complete. Scientific tests, public-reference comparison, actual VASP
Pt(111) execution, GUI/export tests and a clean-environment wheel installation
have passed. See the detailed validation matrix for the tested formats.

At the initial 0.1.0 stage, publisher URLs did not provide the supporting PDF;
the local copy was subsequently recovered for 0.2.0. Reproducing the 2016 material series, shipping a version-specific compiled
VASP plugin and broadening platform/version qualification are the next release
milestones; they are not represented as completed by this initial release.

## v0.2 acceptance update — 2026-10-08

Colorbar styling, offline demos, integrated Henkelman Bader analysis, basin
selection, and compact native export are implemented and tested. Pt3Y(111)
is now a mandatory benchmark: qualitative contrast and numerical consistency
pass; strict agreement with the original DACAPO values remains NOT PASSED.
The local SI has been recovered and read. Final original Pt3Y softness data
and its generation script are still needed to resolve the absolute-value gap.
See results/pt3y-validation.json and docs/validation.md for separate gates.
