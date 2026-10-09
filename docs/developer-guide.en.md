# Developer guide

[中文](developer-guide.zh-CN.md) · [Documentation index](index.md)

## Source layout

| Path | Responsibility |
|---|---|
| `src/fermi_softness/kernel.py` | Stable Fermi derivative and energy window |
| `wavecar.py`, `vasprun.py` | Binary states and secure XML metadata parsing |
| `compute.py` | Streaming smooth-field reconstruction |
| `parchg.py`, `frozen.py` | VASP native export preparation and checked import |
| `field.py`, `io.py` | Geometry, periodic sampling, integrals, NPZ/Cube/density I/O |
| `bader.py`, `install_bader.py` | Reference-defined basins, integration and optional executable installation |
| `render.py`, `gui.py` | Scene model, PyVista rendering, Qt interface |
| `demos.py`, `data/` | Portable offline datasets and provenance |
| `cli.py` | Public command line |
| `tests/` | Numerical and input-integrity regression checks |
| `validation/` | Optional real-file, GUI and release checks; redistributable VASP inputs |
| `vasp-plugin/` | Original Fortran kernel and independent driver |

The filenames without a directory prefix in the table belong to
`src/fermi_softness/`. Computational modules should not require a graphics context.

## Development environment and checks

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[gui,dev]"
python -m pytest -q
ruff check src tests validation
python validation/generate_cli_reference.py --check
python validation/check_docs.py
python -m build
```

Use the Windows activation command from the user guide when appropriate. The
`dev` extra includes pytest, Ruff and build. GUI dependencies are optional for
the numerical suite; rendering-dependent tests skip when they are absent.
Public-file tests skip until fixtures have been fetched:

```sh
python validation/fetch_public_fixtures.py
python -m pytest -q tests/test_public_wavecars.py
python -m pip install pymatgen
python validation/compare_pymatgen.py
```

Fixture downloads are pinned by revision and SHA-256. They remain outside the
distributed package. Desktop checks require a working display:

```sh
python validation/gui_smoke.py
python validation/gui_animation.py
python validation/gui_export_pixels.py
python validation/gui_acceptance_v02.py
python validation/visual_v02.py
```

The material validators additionally require the original calculation outputs
under the local paths described by their code; they are not self-contained DFT
engines. Run the redistributable [Pt](../validation/pt111/README.md) or
[Pt₃Y](../validation/pt3y111/README.md) inputs with your own licensed VASP and
potentials when regenerating those results.

For the independent Fortran kernel, install CMake and a Fortran compiler:

```sh
cmake -S vasp-plugin -B build/fortran
cmake --build build/fortran
ctest --test-dir build/fortran --output-on-failure
```

See the [integration contract](../vasp-plugin/README.md) before attempting to
connect it to VASP. MPI reductions, PAW hooks and version-specific interfaces
still need implementation and validation.

## Python API examples

These functions are usable in scripts. The project is at an early research
release; pin the version when building downstream workflows.

```python
from fermi_softness.compute import calculate
from fermi_softness.io import write_field_cube

field, channels = calculate("source-run/WAVECAR", "source-run/vasprun.xml", kt=0.4)
field.save("softness.npz")
write_field_cube(field, "softness.cube")
print(field.integral)  # eV^-1, smooth-field integral for this route
print(field.metadata["spectral_softness_eV_inverse"])
print(field.sample([[0.0, 0.0, 5.0]]))  # Cartesian Angstrom; periodic interpolation
```

```python
from fermi_softness.demos import load_demo
from fermi_softness.field import Field

field, charge, scene, resource_root = load_demo("pt3y111")
field.save("pt3y-copy.npz")
restored = Field.load("pt3y-copy.npz")
assert abs(restored.integral - field.integral) < 1e-10
```

```python
from fermi_softness.bader import run_bader, select_basins

report = run_bader(
    field,
    ["source-run/AECCAR0", "source-run/AECCAR2"],
    "atomic-softness",
    charge="source-run/CHGCAR",
    surface_atoms=[1, 7, 10, 13],
)
selected = select_basins(field, "atomic-softness/basins.npz", [1, 7, 10, 13])
selected.save("surface-only.npz")
```

The last example requires `field` and source densities from the same calculation;
do not combine the demo with unrelated source files. See `prepare_parchg`,
`calculate_parchg`, `prepare_frozen` and `calculate_frozen` in their corresponding
modules for native-density automation.

## Field format and numerical contracts

A native field is a compressed NumPy archive readable with `allow_pickle=False`:

| Key | Shape / interpretation |
|---|---|
| `values` | `(nx, ny, nz)`, scalar field in the recorded units |
| `cell` | `(3, 3)`, lattice vectors as rows, Å |
| `numbers` | `(natoms,)`, atomic numbers |
| `positions` | `(natoms, 3)`, Cartesian Å |
| `origin` | `(3,)`, Cartesian grid origin, Å |
| `metadata` | JSON string with representation, units, parameters and provenance |

Grid nodes are `origin + (i/nx, j/ny, k/nz) @ cell` with no duplicated periodic
endpoint. The volume element is `abs(det(cell))/(nx*ny*nz)`. `Field.sample` uses
periodic trilinear interpolation, including skew cells. `integrate_regions`
requires nonnegative integer labels with identical array shape and geometry;
the bare label array cannot validate geometry by itself, so the caller must.

Basins are a different archive with recorded geometry and labels; do not load
`basins.npz` as an ordinary `Field`. Scene JSON contains display settings and a
camera, not numerical data. Preserve these distinctions in future formats.

Changes to spin degeneracy, k weights, PAW norms, units or symmetry must update
the [method contract](../research/notes/method-contract.md) and include independent
numerical evidence. A matching image is not a sufficient correctness check.

## Documentation and releases

Update the English and Chinese guides together. CLI tables are generated by:

```sh
python validation/generate_cli_reference.py
python validation/check_docs.py
```

The link checker checks local Markdown targets. It does not validate external
websites or run VASP. Before a release, build a wheel and source archive, install
the wheel in a clean environment and exercise the documented demo/API flows.
Check that LICENSE, citation, docs, Fortran source and redistributable input
fixtures are included where intended. Record hashes for release assets.

Do not include raw private archives, publisher PDFs, credentials, external Bader
binaries, VASP source or POTCAR. Review embedded NPZ metadata as well as filenames.
The bundled NPZ examples are derived numerical fields produced for this project;
their provenance is in `data/*/report.json` and the validation reports. The
unpublished source archives are not bundled. Historical third-party screenshots
are credited separately in THIRD_PARTY.md and retain their original copyright.

Keep a release's version consistent across `pyproject.toml`, `__init__.py`,
`CITATION.cff`, changelog, manuals and release notes. Source archives and wheels
have different roles: the wheel is for installation; the source archive includes
the development and documentation material. See [contributing](../CONTRIBUTING.md)
and [third-party notices](../THIRD_PARTY.md).
