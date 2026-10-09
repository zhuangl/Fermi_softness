# Native PAW density exports

[中文](native-export.zh-CN.md) · [Complete workflows](user-guide.en.md)

Two native-density routes complement direct smooth WAVECAR reconstruction.

| Route | Best use | State/spin support |
|---|---|---|
| `prepare-parchg` / `compute-parchg` | Explicit independent reference; per-state densities | Scalar and collinear spin |
| `prepare-frozen` / `compute-frozen` | One compact weighted-density output | Nonmagnetic scalar; validated on VASP 6.4.2 |

For the compact route, define c=4kT and use occupations c*w(E). They lie in
[0,1]. VASP then constructs the native valence density with those weights
while keeping the orbitals and eigenvalues fixed. Dividing the output by c
gives the local softness, including VASP's charge augmentation.

The deck uses `ALGO=None`, `LDIAG=.FALSE.`, `NELM=1`, `ISMEAR=-2`, and `ICHARG=0`.
It explicitly retains the original band count and k-point ordering. Occupation
weights come from full-precision WAVECAR eigenvalues, since vasprun.xml may
round band energies. The importer checks the source fingerprint, frozen-run
parameters, output energies, recorded occupations, geometry and cell integral.

The temporary NELECT and occupations are mathematical weights for this export.
The postprocessing folder's energies, Fermi energy and CHGCAR do not describe
a new self-consistent physical state. Use the **original** SCF CHGCAR for the
charge envelope and original AECCAR0+AECCAR2 for Bader boundaries.

The scalar Pt(111) check compared all grid points against the independent sum
of 161 separated PARCHG files: RMS difference 2.09e-7 eV^-1 Å^-3; relative L2
difference 3.03e-6. The Pt₃Y native integral matches the spectral sum to 3.19e-9
relative. Full numbers are in `results/pt3y-validation.json`.

Both routes preserve the original WAVECAR (`LWAVE=.FALSE.` in compact exports).
Keep the same POTCAR and a parallel layout that does not change NBANDS. Place
postprocessing in its own directory using the generated RUN.md instructions.

Sources: [VASP FERWE](https://vasp.at/wiki/FERWE),
[VASP ALGO](https://vasp.at/wiki/ALGO), [VASP LPARD](https://vasp.at/wiki/LPARD).
