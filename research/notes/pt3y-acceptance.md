# Pt3Y(111) acceptance record

The revised acceptance target is the Pt-bright / Y-low spatial contrast of
Figure 3A, its 95%-charge envelope and 1–28 keV^-1 Angstrom^-3 color scale.
Do not equate a matching palette with numerical reproduction.

On 2026-10-08 the author's local `Frontier Electronic Band` archive was found.
It contains the actual SI (8 pages), an earlier detailed computational-methods
document, original figures, an early Pt3Y charge Cube and finite-difference
Fukui Cube, and MoS2 softness Cubes. This supersedes the earlier note that the
supporting material was unavailable.

The Pt3Y finite-difference file is NOT used as Fermi softness. Its companion
charge Cube provides a 3x3 repeated four-layer L12 slab. The first 16 atoms and
one-third of each in-plane vector recover a Pt12Y4 unit cell, with inferred
cubic lattice constant 4.16919691 Angstrom. The raw header is old, so it is an
archival geometry source, not proof of the final DACAPO geometry.

The reconstruction uses the paper's PW91, 408 eV, 6x6x1 Monkhorst-Pack mesh,
0.1 eV SCF Fermi smearing, four layers with the bottom two fixed and a 0.05
eV/Angstrom force threshold. It retains the archived lattice and vacuum.
VASP PAW Y_sv/Pt datasets replace the original DACAPO ultrasoft datasets; that
difference and the absence of the final Pt3Y Fermi-softness grid preclude an
unqualified assertion of numerical or pixel-for-pixel identity.

Bader volumes must be constructed from an explicitly recorded reference
density and then used to integrate s_F(r). For VASP, AECCAR0+AECCAR2 is the
recommended reference. The legacy manuscript's exact reference-file choice
is not recorded in the located final paper/SI; preserve that uncertainty in
the original-versus-reconstruction comparison.
