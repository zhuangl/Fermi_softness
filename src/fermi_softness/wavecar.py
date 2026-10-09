"""Original streaming reader for the documented direct-access WAVECAR format.

Only one band's coefficients and FFT are resident at a time. No PAW norm
renormalization is performed. All public indices are zero based.
"""

from pathlib import Path

import numpy as np
from scipy.fft import ifftn, next_fast_len

# VASP/WaveTrans kinetic-energy conversion (eV Angstrom^2), kept compatible
# with the binary writer when enumerating vectors on the cutoff boundary.
HSQDTM = 3.80998212


def g_vectors(cell, encut, kpoint):
    """Enumerate allowed reciprocal indices in VASP x-fastest order."""
    cell = np.asarray(cell, dtype=float)
    k = np.asarray(kpoint, dtype=float)
    bounds = np.ceil(
        np.linalg.norm(cell, axis=1) * np.sqrt(encut / HSQDTM) / (2 * np.pi) + np.abs(k)
    ).astype(int)
    # Cauchy bounds work for skew and left-handed cells as well as orthogonal cells.
    axes = [np.r_[np.arange(m + 1), np.arange(-m, 0)] for m in bounds]
    reciprocal = 2 * np.pi * np.linalg.inv(cell).T
    result = []
    # Slab enumeration avoids constructing a potentially huge 3D candidate box.
    y, x = np.meshgrid(axes[1], axes[0], indexing="ij")
    xy = np.column_stack((x.ravel(), y.ravel()))
    for z in axes[2]:
        block = np.column_stack((xy, np.full(len(xy), z)))
        q = (block + k) @ reciprocal
        keep = HSQDTM * np.einsum("ij,ij->i", q, q) < encut
        result.append(block[keep])
    return np.concatenate(result).astype(int)


def gamma_mask(g, axis="x"):
    if axis not in ("x", "z"):
        raise ValueError("Gamma half storage must be x or z.")
    a, b, c = (0, 1, 2) if axis == "x" else (2, 1, 0)
    return (
        (g[:, a] > 0)
        | ((g[:, a] == 0) & (g[:, b] > 0))
        | ((g[:, a] == 0) & (g[:, b] == 0) & (g[:, c] >= 0))
    )


def density_from_coefficients(g, coeff, cell, shape):
    """Smooth density in Angstrom^-3, preserving the input coefficient norm."""
    shape = np.asarray(shape, dtype=int)
    minimum = 2 * np.ptp(g, axis=0) + 1
    if shape.shape != (3,) or np.any(shape < minimum):
        raise ValueError(f"FFT grid must be at least {tuple(minimum)} to avoid density aliasing.")
    coeff = np.asarray(coeff, dtype=complex).reshape(-1, len(g))
    if not np.all(np.isfinite(coeff)):
        raise ValueError("Wavefunction coefficients contain non-finite values.")
    volume = abs(np.linalg.det(cell))
    result = np.zeros(tuple(shape))
    mesh = np.zeros(tuple(shape), dtype=complex)
    idx = tuple((g % shape).T)
    for component in coeff:
        mesh.fill(0)
        mesh[idx] = component
        psi = ifftn(mesh, norm="forward") / np.sqrt(volume)
        result += psi.real**2 + psi.imag**2
    return result


class Wavecar:
    def __init__(self, path, *, gamma_half="x"):
        self.path = Path(path)
        self.gamma_half = gamma_half
        if gamma_half not in ("x", "z"):
            raise ValueError("Gamma half storage must be x or z.")
        self._stream = self.path.open("rb")
        try:
            self._read_header()
        except Exception:
            self.close()
            raise

    def _record(self, index, count, dtype=None, *, span=False):
        dtype = np.dtype(dtype or self.endian + "f8")
        if count * dtype.itemsize > self.recl and not span:
            raise ValueError("WAVECAR record exceeds declared record length.")
        self._stream.seek(index * self.recl)
        values = np.fromfile(self._stream, dtype=dtype, count=count)
        if len(values) != count:
            raise ValueError(f"Truncated WAVECAR at record {index}.")
        return values

    def _read_header(self):
        raw = self._stream.read(24)
        if len(raw) != 24:
            raise ValueError("WAVECAR header is truncated.")
        for endian in ("<", ">"):
            first = np.frombuffer(raw, dtype=endian + "f8")
            if first[2] in (45200, 45210, 53300, 53310):
                self.endian = endian
                break
        else:
            raise ValueError("Unrecognized WAVECAR format or precision tag.")
        self.recl, self.nspin, self.rtag = map(int, first)
        if self.recl < 104 or self.nspin not in (1, 2):
            raise ValueError("Invalid WAVECAR record length or spin count.")
        self.coeff_dtype = np.dtype(self.endian + ("c8" if self.rtag in (45200, 53300) else "c16"))
        h = self._record(1, 13)
        if not np.all(np.isfinite(h)):
            raise ValueError("Non-finite WAVECAR header.")
        self.nk, self.nb = int(h[0]), int(h[1])
        self.encut, self.efermi = float(h[2]), float(h[12])
        self.cell = h[3:12].reshape(3, 3)
        if self.nk < 1 or self.nb < 1 or self.encut <= 0 or abs(np.linalg.det(self.cell)) < 1e-10:
            raise ValueError("Invalid WAVECAR dimensions, cutoff or lattice.")
        # Small plane-wave bases can span several records for band metadata.
        self.metadata_records = int(np.ceil((4 + 3 * self.nb) * 8 / self.recl))
        records = 2 + self.nspin * self.nk * (self.nb + self.metadata_records)
        if self.path.stat().st_size < records * self.recl:
            raise ValueError("WAVECAR is truncated: declared band records are missing.")
        self.energies = np.empty((self.nspin, self.nk, self.nb))
        self.kpoints = np.empty((self.nk, 3))
        self.ncoeff = np.empty(self.nk, dtype=int)
        for s in range(self.nspin):
            for k in range(self.nk):
                d = self._record(
                    self.band_record(s, k, 0) - self.metadata_records, 4 + 3 * self.nb, span=True
                )
                if not np.all(np.isfinite(d)):
                    raise ValueError("Non-finite WAVECAR band metadata.")
                if s == 0:
                    self.kpoints[k], self.ncoeff[k] = d[1:4], int(d[0])
                elif int(d[0]) != self.ncoeff[k] or not np.allclose(d[1:4], self.kpoints[k]):
                    raise ValueError("Spin channels have inconsistent k-point metadata.")
                self.energies[s, k] = d[4:].reshape(self.nb, 3)[:, 0]
        self._g = {}
        full = self.vectors(0)
        if self.ncoeff[0] == len(full):
            self.kind = "standard"
        elif self.ncoeff[0] == 2 * len(full) and self.nspin == 1:
            self.kind = "spinor"
        elif self.ncoeff[0] == (len(full) + 1) // 2 and np.allclose(self.kpoints, 0):
            self.kind = "gamma"
        else:
            raise ValueError("Plane-wave count does not match standard, Gamma or spinor storage.")
        for k in range(self.nk):
            n = len(self.vectors(k))
            expected = (
                2 * n if self.kind == "spinor" else (n + 1) // 2 if self.kind == "gamma" else n
            )
            if self.ncoeff[k] != expected:
                raise ValueError(f"Inconsistent plane-wave count at k-point {k + 1}.")

    @property
    def degeneracy(self):
        return 2 if self.nspin == 1 and self.kind != "spinor" else 1

    def band_record(self, spin, kpoint, band):
        return (
            2
            + (spin * self.nk + kpoint) * (self.nb + self.metadata_records)
            + self.metadata_records
            + band
        )

    def vectors(self, kpoint):
        if kpoint not in self._g:
            self._g[kpoint] = g_vectors(self.cell, self.encut, self.kpoints[kpoint])
        return self._g[kpoint]

    def recommended_grid(self):
        minima = np.max([2 * np.ptp(self.vectors(k), axis=0) + 1 for k in range(self.nk)], axis=0)
        return tuple(next_fast_len(max(int(n), 2)) for n in minima)

    def coefficients(self, spin, kpoint, band):
        if not (0 <= spin < self.nspin and 0 <= kpoint < self.nk and 0 <= band < self.nb):
            raise IndexError("Spin, k-point or band index out of range.")
        packed = self._record(
            self.band_record(spin, kpoint, band), int(self.ncoeff[kpoint]), self.coeff_dtype
        ).astype(complex)
        g = self.vectors(kpoint)
        if self.kind == "gamma":
            kept = gamma_mask(g, self.gamma_half)
            half = g[kept]
            nonzero = np.any(half != 0, axis=1)
            packed[nonzero] /= np.sqrt(2)
            lookup = {tuple(v): i for i, v in enumerate(g)}
            coeff = np.zeros(len(g), dtype=complex)
            coeff[kept] = packed
            for v, c in zip(half[nonzero], packed[nonzero]):
                coeff[lookup[tuple(-v)]] = c.conjugate()
            return coeff[None, :]
        return packed.reshape(-1, len(g))

    def density(self, spin, kpoint, band, shape):
        return density_from_coefficients(
            self.vectors(kpoint), self.coefficients(spin, kpoint, band), self.cell, shape
        )

    def close(self):
        self._stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
