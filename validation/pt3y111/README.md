# Pt3Y(111) acceptance fixture

[中文](README.zh-CN.md)

This reconstruction starts from a Pt12Y4 four-layer geometry recovered from
the author's archived Pt3Y charge Cube. It retains the original lattice and
vacuum, translates the slab away from the periodic boundary, fixes the bottom
two layers, and relaxes the top two. The source Cube's full 3x3 cell contains
1476 valence electrons, i.e. 164 per base cell, consistent with Y_sv/Pt here.

Settings follow the paper where recorded: PW91, 408 eV, 6x6x1 Monkhorst-Pack,
SCF Fermi smearing 0.1 eV, force threshold 0.05 eV/Å. VASP 6.4.2 PAW replaces
DACAPO ultrasoft potentials. Use authorized Y_sv then Pt POTCAR datasets in
that order. POTCAR is not distributed.

Run `INCAR.relax` with `POSCAR.initial` and `KPOINTS`. After relaxation, copy
CONTCAR to a separate static directory and use NSW=0, IBRION=-1, EDIFF=1e-8,
ISTART=1, ICHARG=1, LAECHG=.TRUE., and the matching WAVECAR/CHGCAR.

Then reconstruct at kT=0.4 eV using the standalone or compact native route,
and apply the original static AECCAR0+AECCAR2 Bader reference. The top-layer
atom IDs in this fixed ordering are 1, 7, 10 and 13.

The actual native result shows Pt/Y outer-surface softness contrast of about
7.02 on the 95% charge envelope. Its spatial integral and spectral sum agree
to 3.19e-9 relative. This passes the qualitative contrast and software
consistency gates. The strict original-result gate remains **NOT PASSED**:
absolute values differ, and the final DACAPO softness grid and generation
script have not been recovered. See `results/pt3y-validation.json`.
