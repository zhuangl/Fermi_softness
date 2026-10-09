# Numerical conventions

[中文](science.zh-CN.md) · [User guide](user-guide.en.md)

For t = kT > 0, the Fermi–Dirac derivative kernel is

$$
w(E)=\frac{1}{4t}\operatorname{sech}^2\left(\frac{E-\mu}{2t}\right).
$$

The local field is

$$
s_F(\mathbf r)=\sum_{\sigma n\mathbf k}g_\sigma w_\mathbf k
w(\epsilon_{n\mathbf k\sigma})|\widetilde\psi_{n\mathbf k\sigma}(\mathbf r)|^2.
$$

Weights sum to one over k points. Degeneracy is two for scalar ISPIN=1, one
per collinear spin channel, and one per spinor state. Spinor density sums both
components. Occupied and unoccupied states enter on equal terms through w(E).
No extra occupation factor belongs in this expression.

The kernel is evaluated as q/[t(1+q)^2], q=exp(-|E-mu|/t), avoiding overflow.
Its integral over energy is one. The default absolute cutoff is 0.001 eV⁻¹,
following the literal inequality in the 2016 methods section. The prose also
calls this a percentage; this implementation does not silently interpret it
as a percentage of the kernel peak. All metadata record the absolute value.

For a cutoff c, the energy half-width is
`2*t*acosh(1/sqrt(4*t*c))`. `NBANDS` must cover the upper edge at every
contributing k-point and spin. The implementation also checks the lower edge.
Known excluded states are reported separately from uncomputed missing bands.
Neither their small individual kernel weights nor an energy-tail integral
guarantees a bound on an arbitrary material's missing DOS.

## Wavefunctions, PAW and units

The cell lattice vectors are rows of A, the volume is |det A|, and
u(r) = sum_G c(G) exp(2πi G·fractional_r)/sqrt(V).
The Bloch phase disappears in |psi|². FFT scaling is checked against a direct
coefficient-norm sum. No artificial unit normalization is performed.

In PAW, the smooth wavefunction has a generalized normalization. Its ordinary
norm need not equal one. Therefore this package reports both
`smooth_integral_eV_inverse` and `spectral_softness_eV_inverse`.
An all-electron local field requires extra PAW projector and augmentation
information; WAVECAR alone does not supply that reconstruction.

The second backend uses VASP LPARD with LSEPB=LSEPK=true. VASP sets the selected
band occupation and k-point weight to one, then runs its ordinary soft-charge
and augmentation construction. An ISPIN=1 PARCHG therefore already contains
the factor of two. For ISPIN=2, reconstruct up/down from (total ± magnetization)/2
and apply the derivative at each spin's own eigenvalue. The software verifies
each single-state integral (two or one, respectively), then the final weighted
integral. This is VASP's augmented valence charge representation, not an
all-electron orbital reconstruction. PARCHG's lack of an augmentation-occupancy
section does not mean its scalar grid lacks charge augmentation.

The field uses eV⁻¹ Å⁻³. Cube coordinate records use Bohr, while its scalar
values retain the units in the comment line. Native archives are recommended
for quantitative interchange because Cube has no universal scalar-units field.
Density Cubes imported for display must already contain values in Å⁻³.
VASP CHGCAR grids are converted from stored values by dividing by cell volume.

## Spatial sampling

Reciprocal vectors obey the plane-wave kinetic energy cutoff with x varying
fastest in VASP's serialization. Enumeration bounds use the direct lattice
vector lengths, which remains valid for skew cells.

Each FFT dimension exceeds twice the corresponding G-index span, so the
squared amplitude is represented without density aliasing. Larger grids are
Fourier interpolation of the same basis. They do not improve ENCUT convergence.
Visualization can use a separate display stride without changing archived data.

Gamma half-storage is expanded with conjugate symmetry and the VASP sqrt(2)
factor removed for nonzero G. Modern x-half and explicitly selected legacy
z-half storage are supported. Integer grid axes and Cartesian geometry remain
distinct throughout, including periodic interpolation and supercell rendering.

## Symmetry and convergence

Irreducible-zone integration weights alone are sufficient for a spectral sum,
but generally insufficient for a spatial map. ISYM=-1 is accepted universally;
ISYM=0 is also accepted for scalar time-reversal-reduced densities.
Geometry-only symmetry detection would be unsafe for magnetic states, so this
release does not guess the VASP magnetic space group.

Use a converged static run. The reader rejects extrapolated MD states, a final
cycle reaching NELM, inconsistent eigenvalues/lattices/k-points, unsupported
or truncated records, and insufficient numerical grids. These checks do not
replace convergence studies of ENCUT, k mesh, smearing or slab thickness.

## Surface integration and visualization

Whole-cell S, a selected-layer integral, and an atom's Bader-basin integral
are different results. The paper used the first surface layer's Bader basins.
External basin labels must match the numerical field's cell, origin, shape,
and voxel ordering. The integration API does not resample integer partitions.

For charge-envelope plots, grid points are sorted by density and the threshold
is chosen at the requested cumulative charge fraction. This is a discrete-grid
criterion, and isosurface interpolation introduces a small geometric difference.
Charge and softness grids may have different shapes but must share geometry.
The colored surface samples softness periodically in fractional coordinates.

Small negative vacuum ringing is tolerated for the enclosed-charge visualization
quantile only when its integrated magnitude is below 1e-6 of positive density.
Stored and integrated field values are unchanged. A periodic display-origin
shift changes the viewed cell cut, with atoms and volume sampling shifted
consistently; it does not change the underlying material.

## Sources

- [Original paper](https://doi.org/10.1002/anie.201601824)
- [VASP WAVECAR](https://vasp.at/wiki/WAVECAR)
- [VASP symmetry](https://vasp.at/wiki/ISYM)
- [VASP CHGCAR](https://vasp.at/wiki/CHGCAR)
- [VASP partial densities](https://vasp.at/wiki/LPARD)
- [WaveTrans format description](https://www.andrew.cmu.edu/user/feenstra/wavetrans/)
- [pymatgen reference reader](https://pymatgen.org/pymatgen.io.vasp.html)

Detailed source-access notes are in `research/notes/method-contract.md`.
