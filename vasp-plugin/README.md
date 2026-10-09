# In-VASP integration component

[中文](README.zh-CN.md)

This directory contains a portable, independently compilable accumulation
kernel. **It is not yet a version-specific working VASP plugin.** The standalone
Python program is the usable VASP postprocessor in this release.

```sh
cmake -S vasp-plugin -B build/fortran
cmake --build build/fortran
ctest --test-dir build/fortran --output-on-failure
```

To integrate with a licensed VASP checkout, add the module before its caller in
the version's build order and call `accumulate_softness` with one band's
real-space density. The caller must implement and verify these contracts:

1. Use converged eigenvalues and the final Fermi energy. Sum both occupied and
   unoccupied bands selected by the derivative cutoff. Do not reuse SCF
   occupation factors in the new weights.
2. Convert the density to Angstrom^-3. Retain the original PAW norm. For
   all-electron or augmented output, apply the same derivative weight to the
   corresponding on-site augmentation contribution.
3. Include each state's k-point weight exactly once. Apply degeneracy two for
   scalar ISPIN=1, one per collinear channel, and one per spinor (whose two
   component densities must be summed).
4. Respect VASP's actual symmetry operations and its distributed real-space
   grid. Avoid double counting replicated band/k-point communicators. Each
   spatial voxel's final reduction must count every state once.
5. Export an independent scalar field; do not overwrite the SCF density,
   occupations, or Hamiltonian. Add units, kT, cutoff, representation and
   integrated-weight diagnostics to the result.
6. Compare scalar, magnetic, spinor and MPI runs against the standalone
   smooth-field implementation, then separately validate augmentation.

An adapter cannot be certified from this generic kernel alone. The exact VASP
version and licensed source are required to choose density, PAW and MPI hooks.
No VASP source or POTCAR may be included in the public distribution.
