# Atomic softness with Bader volumes

[中文](bader.zh-CN.md) · [User guide](user-guide.en.md)

The 2016 paper's Experimental Section explicitly uses Bader volumes for
surface atoms and integrates local Fermi softness inside them. Bader partitioning
and the colored 3D surface are separate operations:

$$
S_A=\int_{\Omega_A}s_F(\mathbf r)\,d^3r
=\sum_{nk\sigma}g_\sigma w_k w(E_{nk\sigma})
\int_{\Omega_A}|\psi_{nk\sigma}(\mathbf r)|^2\,d^3r.
$$

The same atomic volume can therefore be used for charge, an individual state's
density, and the weighted softness field. It defines the spatial attribution;
wavefunction accuracy still comes from the electronic calculation and FFT grid.

## What the program does

The toolkit invokes the official **Henkelman Bader near-grid algorithm**, the
Tang–Sanville–Henkelman 2009 method cited by the paper. It builds zero-flux
surfaces from an explicitly selected reference density, imports atom-index
labels, checks them against Bader's own ACF.dat integrals, and integrates
the softness field over those volumes. Labels are not constructed from nearest-
atom distances or atom-centered spheres.

For VASP, the recommended reference is `AECCAR0 + AECCAR2`, generated with
`LAECHG=.TRUE.` in a converged static calculation. A single explicitly chosen
charge-density reference is also accepted. Reference filenames and checksums
are saved, so a later run can use exactly the same partition definition.

The reference density determines boundaries. Per-atom electron populations
are obtained from the optional valence `CHGCAR`. The raw sampled core-density
integral is diagnostic and should not be interpreted as an atomic charge:
near-nuclear core peaks can be poorly integrated on otherwise useful boundary
grids. Test basin-integrated softness on increasingly fine grids.

## Command line

```sh
# Fetch the pinned official executable into this project (macOS arm64/Linux x86_64).
fermi-softness install-bader
fermi-softness bader softness.npz \
  --reference AECCAR0 AECCAR2 --charge CHGCAR \
  --surface-atoms 1 7 10 13 -o bader-results
```

Atom IDs are one based, in the original structure order. The example IDs must
be replaced with your actual surface atoms. Without `--surface-atoms`, all
atomic results are reported without assuming which layer is the surface.

Outputs:

- `atoms.csv`: atom coordinates, volume, softness, optional valence population.
- `report.json`: provenance, numerical checks, selected-layer sum.
- `basins.npz`: integer atom labels with complete grid geometry.
- `softness-on-bader-grid.npz`: field on the integration grid.
- `ACF.dat`, `AtIndex.dat`, `bader.log`: original engine evidence.

If a softness grid is coarser than the reference grid, it is interpolated
periodically by Fourier resampling, preserving its integral. This adds samples
of the existing field. It does not add electronic-structure information.
Downsampling the Bader reference is not performed implicitly.

```sh
fermi-softness select-basins softness.npz --basins bader-results/basins.npz \
  --atoms 1 7 -o selected-atoms.npz
```

The selected field is zero outside those basins and is explicitly labeled as
a Bader selection. It retains the original structure for orientation.

## Desktop workflow

Open a field, then use the **Bader** tab to select references, optionally CHGCAR,
and an output parent folder. Results are written to its new `bader-result`
subdirectory. The table supports selecting atoms and viewing their basin-
restricted softness. **Restore full field** returns to the complete result.
The **Export** tab can save the selected numerical field and its image.

Use an existing Bader executable via the GUI selector, `--executable`, or the
`FERMI_SOFTNESS_BADER` environment variable. Other platforms can compile the
official source. Bader is an external dependency; its binary/source is not
silently bundled under this package's BSD license.

## Relation to the original result

The author's local SI has been recovered and checked. The final paper specifies
Bader integration, but does not give the exact historical reference filename
or Bader command. The current charge-reference choice is fully recorded rather
than treated as proof that the historical partition was identical.

Sources: [original paper](https://doi.org/10.1002/anie.201601824),
[Henkelman Bader documentation](https://github.com/henkelmangroup/bader),
[Tang et al. 2009](https://doi.org/10.1088/0953-8984/21/8/084204).
