# Fermi Softness 0.3.1 — Complete CLI reference

[中文](cli-reference.zh-CN.md) · [User guide](user-guide.en.md)

Generated from the actual command parser; names, requirements, choices and defaults stay synchronized.

```sh
fermi-softness --version
fermi-softness --help
fermi-softness compute --help
```

You can replace `fermi-softness` with `python -m fermi_softness`. Every subcommand supports `-h/--help`.

## `compute`

Reconstruct the smooth PAW field.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `--wavecar` | no | `WAVECAR` | Source WAVECAR. |
| `--vasprun` | no | `vasprun.xml` | Matching source vasprun.xml (gzip supported). |
| `--kt` | no | `0.4` | Descriptor kT in eV; independent of SCF SIGMA. |
| `--threshold` | no | `0.001` | Absolute derivative cutoff, eV^-1. |
| `--mu` | no | — | Override Fermi energy, eV; otherwise use source metadata. |
| `--grid` | no | — | Three FFT dimensions NX NY NZ; automatic if omitted. |
| `--gamma-half` | no | `x`; `x`, `z` | Gamma half-storage axis. |
| `--max-memory-gb` | no | `4` | Working-memory estimate budget, GB. |
| `--allow-incomplete` | no | `False` | Permit diagnostic output with insufficient bands. |
| `--allow-reduced` | no | `False` | Permit diagnostic unsymmetrized output. |
| `-o`, `--output` | no | `fermi-results` | Destination file or directory (see workflow below). |

## `prepare-parchg`

Prepare a state-resolved native export.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `--wavecar` | no | `WAVECAR` | Source WAVECAR. |
| `--vasprun` | no | `vasprun.xml` | Matching source vasprun.xml (gzip supported). |
| `--incar` | no | — | Source INCAR; if omitted, look beside vasprun.xml. |
| `--kt` | no | `0.4` | Descriptor kT in eV; independent of SCF SIGMA. |
| `--threshold` | no | `0.001` | Absolute derivative cutoff, eV^-1. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## `compute-parchg`

Combine the prepared native state densities.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `manifest` | yes | — | Generated manifest.json; keep it with the export outputs. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## `prepare-frozen`

Prepare compact nonmagnetic export.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `--wavecar` | no | `WAVECAR` | Source WAVECAR. |
| `--vasprun` | no | `vasprun.xml` | Matching source vasprun.xml (gzip supported). |
| `--incar` | no | — | Source INCAR; if omitted, look beside vasprun.xml. |
| `--kt` | no | `0.4` | Descriptor kT in eV; independent of SCF SIGMA. |
| `--threshold` | no | `0.001` | Absolute derivative cutoff, eV^-1. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## `compute-frozen`

Import the checked fixed-orbital density.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `manifest` | yes | — | Generated manifest.json; keep it with the export outputs. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## `inspect`

Inspect WAVECAR format and FFT dimensions.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `wavecar` | yes | — | Source WAVECAR. |
| `--gamma-half` | no | `x`; `x`, `z` | Gamma half-storage axis. |

## `gui`

Open Fermi Softness Studio.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `field` | no | — | Softness volume, preferably native .npz. |
| `--charge` | no | — | Charge density; use original SCF density for envelopes/populations. |
| `--demo` | no | `False` | Open synthetic teaching data. |
| `--scene` | no | — | Saved scene JSON, including camera and styling. |
| `--example` | no | — | Packaged demo ID from the demos command. |

## `demos`

List the offline demo catalog.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |

## `install-app`

Install the macOS application icon and launcher.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `--directory` | no | — | Applications folder; defaults to /Applications if writable, otherwise ~/Applications. |
| `--open` | no | `False` | Open Studio after installing its macOS application entry. |

## `install-bader`

Install the pinned official Bader executable.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `-o`, `--output` | no | `.tools/bader` | Destination file or directory (see workflow below). |

## `demo`

Write synthetic teaching data.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `-o`, `--output` | no | `fermi-demo` | Destination file or directory (see workflow below). |

## `render`

Render a field as PNG or TIFF.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `field` | yes | — | Softness volume, preferably native .npz. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |
| `--charge` | no | — | Charge density; use original SCF density for envelopes/populations. |
| `--scene` | no | — | Saved scene JSON, including camera and styling. |
| `--mode` | no | —; `softness`, `charge`, `slice` | Display mode; otherwise preserve the scene/default. |
| `--width` | no | `3600` | Image width in pixels. |
| `--height` | no | `2600` | Image height in pixels. |
| `--dpi` | no | `300` | Image DPI metadata. |

## `animate`

Export a rotating view as MP4 or GIF.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `field` | yes | — | Softness volume, preferably native .npz. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |
| `--charge` | no | — | Charge density; use original SCF density for envelopes/populations. |
| `--scene` | no | — | Saved scene JSON, including camera and styling. |
| `--width` | no | `1920` | Image width in pixels. |
| `--height` | no | `1080` | Image height in pixels. |
| `--fps` | no | `30` | Animation frames per second, 1–60. |
| `--seconds` | no | `12` | Animation duration in seconds, 0.25–120. |
| `--turns` | no | `1` | Number of full rotations, 1–10. |
| `--axis` | no | `normal`; `normal`, `view`, `x`, `y`, `z` | Rotation axis: surface normal, initial view-up, or Cartesian x/y/z. |
| `--reverse` | no | `False` | Reverse the rotation direction. |
| `--no-fit` | no | `False` | Keep exact camera framing; default fits the full rotation. |

## `integrate`

Integrate an existing grid-aligned partition.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `field` | yes | — | Softness volume, preferably native .npz. |
| `--labels` | yes | — | Integer .npy labels matching field geometry/grid; 0 may mark vacuum. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## `bader`

Generate charge-defined basins and integrate softness.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `field` | yes | — | Softness volume, preferably native .npz. |
| `--reference` | yes | — | One reference density, or AECCAR0 AECCAR2 (summed). |
| `--charge` | no | — | Charge density; use original SCF density for envelopes/populations. |
| `--executable` | no | — | Bader executable; otherwise use environment/PATH/local install. |
| `--vacuum` | no | `off`; `off`, `auto` | Bader vacuum classification; off assigns the full cell. |
| `--surface-atoms` | no | — | One-based IDs whose basin integrals form the surface sum. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## `select-basins`

Save a field restricted to selected atoms.

| Argument | Required | Default / choices | Meaning |
|---|---|---|---|
| `-h`, `--help` | no | — | Show command help and exit. |
| `field` | yes | — | Softness volume, preferably native .npz. |
| `--basins` | yes | — | basins.npz generated by the Bader workflow. |
| `--atoms` | yes | — | One or more one-based atom IDs. |
| `-o`, `--output` | yes | — | Destination file or directory (see workflow below). |

## Output targets and workflow order

`compute`, `compute-parchg` and `compute-frozen` write result directories; `prepare-*` write VASP run directories. Preparation does not execute VASP.

`demo` writes a demo directory; `install-bader` an executable directory; `bader` an analysis directory. `render` writes PNG/TIFF, `integrate` JSON, and `select-basins` NPZ.

`gui --demo` opens synthetic data. Use `gui --example pt111` or `gui --example pt3y111` for material demos. Do not combine competing data inputs.

`integrate` requires already aligned voxel labels, not just ACF.dat, and does not find boundaries itself. Use `bader` to generate a charge-defined partition.

`--allow-incomplete` and `--allow-reduced` produce explicitly diagnostic results. They do not replace enough empty bands or correct symmetry settings. See the user guide for complete examples and error recovery.
