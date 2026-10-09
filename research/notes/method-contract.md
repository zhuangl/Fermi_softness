# Method and source record

Primary source: B. Huang, L. Xiao, J. Lu, L. Zhuang, *Spatially Resolved
Quantification of the Surface Reactivity of Solid Catalysts*, Angew. Chem. Int.
Ed. **55**, 6239–6243 (2016), https://doi.org/10.1002/anie.201601824.
The supplied local PDF was read in full; equations and figure captions were
checked against the PDF. Its text extraction is private and excluded from Git.

For t = kT > 0, use

    w(E; mu, t) = exp(-abs((E-mu)/t)) / (t * (1+exp(-abs((E-mu)/t)))**2
    s(r) = sum_spin,k,band g_spin * w_k * w(E_nk; mu,t) * |psi_nk(r)|**2

The stable expression equals -df/dE. k-point weights sum to one. A scalar
non-spin-polarized state has degeneracy two; each collinear spin channel and
each spinor state has degeneracy one. Spinor density sums both components.
SCF occupations do not enter this expression.

The paper uses t=0.4 eV as a useful parameter and truncates when the derivative
falls below 0.001. We implement the literal absolute threshold 0.001 eV^-1;
this is not silently replaced by 0.1% of the peak. The paper's accompanying
percentage wording can alternatively motivate a relative cutoff, which must
be explicitly recorded if used. Energies in the entire window are required.

Output s(r) units: eV^-1 Angstrom^-3. Multiply by 1000 for the paper's
keV^-1 Angstrom^-3 display. Whole-cell spectral S units: eV^-1.
The source's surface descriptor integrates s(r) over Bader basins belonging
to the first surface layer. A whole-cell integral or a geometric slab integral
is not automatically that descriptor.

Figure 2 maps s(r) onto a charge-density isosurface enclosing 95% of charge.
Figure 4 additionally uses a direct s(r) isosurface and planar sections.
The methods section mentions Cube export and Mayavi. VMD is also a useful
Cube consumer, as requested by the user.

## VASP representation and numerical rules

With row-wise lattice A and volume V, reconstruct

    u_nk(r) = sum_G c_nk(G) exp(2*pi*i*G.fractional_r) / sqrt(V).

The Bloch phase cancels in the density. Preserve c; the smooth PAW density
does not include on-site augmentation. Its cell integral equals sum |c|^2,
not necessarily one. The full spectral S = sum weights and the smooth
integral therefore legitimately differ. Report this difference explicitly.

Zero-padding coefficients samples the same plane-wave function more finely.
To represent squared amplitudes without aliasing, each FFT dimension must
exceed twice the span of the included G indices on that axis. Enforce this
before rendering or exporting numerical data.

WAVECAR has no reliable k-point integration weights. Read those from matching
vasprun.xml. A sum over an irreducible set needs space-group reconstruction
for local fields, even though the spectral sum is valid. Initially accept
ISYM=-1/0 scalar data and ISYM=-1 spinors only; reject ordinary ISYM=2 data
unless explicitly requesting a diagnostic incomplete result.

Authoritative references checked 2026-10-08:

- https://vasp.at/wiki/WAVECAR (static vs extrapolated MD wavefunctions)
- https://vasp.at/wiki/ISYM (density symmetry, time reversal)
- https://vasp.at/wiki/CHGCAR (data ordering and density = stored value / V)
- https://vasp.at/wiki/LPARD (partial-density workflow and spinor limitation)
- https://www.andrew.cmu.edu/user/feenstra/wavetrans/ (WAVECAR layout)
- https://github.com/QijingZheng/VaspBandUnfolding (independent format reference)

Supporting information link discovered:
https://onlinelibrary.wiley.com/doi/suppl/10.1002/anie.201601824/supinfo/anie201601824-sup-0001-misc_information.pdf
The initial publisher download returned HTTP 403. The local archive later
supplied the supplement, as recorded below.

Update, 2026-10-08: the local manuscript archive supplied the eight-page
`SI_Fermi Softness.pdf`; it has now been read. It contains Figures S1–S5 and
Tables S1–S2. The main paper contains the calculation and Bader instructions.
An earlier computational-methods draft also specifies a 1632 eV density cutoff
and cites the Henkelman program. The exact historical Bader reference filename
remains unrecorded.

## Native-density route, verified during implementation

A VASP 6.4.2 Pt(111) test confirmed that separated PARCHG scalar grids include
VASP's augmentation treatment even though PARCHG does not contain the restart
augmentation-occupancy section. A read-only inspection of the user's licensed
VASP 6.3.2 `pardens.F` confirmed that the selected band occupations and k-point
weight are set to one, followed by the ordinary soft-charge and augmentation
construction. No VASP source is distributed with this repository.

The tool now includes a native-density backend. For scalar ISPIN=1, each
PARCHG contains the degeneracy factor two; multiply only by the original
k-point weight and derivative kernel. For ISPIN=2, split total and magnetization
into up/down densities and use each spin energy separately. Each PARCHG and
the final field must pass an integral check. This route preserves VASP's
augmented charge representation; it is not an all-electron orbital reconstruction.
