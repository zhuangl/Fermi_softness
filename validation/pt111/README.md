# Pt(111) software integration fixture

[中文](README.zh-CN.md)

Three Pt atoms in a three-layer 1x1 fcc(111) slab, a=3.92 Å, 10 Å vacuum on
each side. This fixture checks the software's path through a real VASP result;
it is not a converged adsorption study or reproduction of the 2016 paper.

PBE Pt POTCAR must be supplied by an authorized VASP user. It is intentionally
not distributed. The validation used VASP 6.4.2, ENCUT=400 eV, a full 4x4x1
k mesh, 48 bands, Fermi–Dirac SCF smearing 0.1 eV, ISYM=-1 and EDIFF=1e-8 eV.
The final SCF required 27 steps.

After the static run:

```sh
fermi-softness compute --wavecar WAVECAR --vasprun vasprun.xml -o smooth
fermi-softness prepare-parchg --wavecar WAVECAR --vasprun vasprun.xml \
  --incar INCAR -o native-deck
```

Run the prepared LPARD deck with the same WAVECAR and POTCAR. KPAR=1 is
required for this VASP postprocessing step. Then:

```sh
fermi-softness compute-parchg native-deck/manifest.json -o native
```

The kT=0.4 eV, 0.001 eV^-1 kernel selects 161 states. Numerical results and
the precise acceptance scope are recorded in `results/pt111-validation.json`.
