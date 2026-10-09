"""A periodic scalar field, with explicit geometry, units and provenance."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates


@dataclass
class Field:
    values: np.ndarray
    cell: np.ndarray
    numbers: np.ndarray
    positions: np.ndarray
    metadata: dict = field(default_factory=dict)
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self):
        self.values = np.asarray(self.values, dtype=float)
        self.cell = np.asarray(self.cell, dtype=float)
        self.numbers = np.asarray(self.numbers, dtype=int)
        self.positions = np.asarray(self.positions, dtype=float).reshape(-1, 3)
        self.origin = np.asarray(self.origin, dtype=float)
        if self.values.ndim != 3 or min(self.values.shape) < 2:
            raise ValueError(
                "A field needs a three-dimensional grid with at least 2 points per axis."
            )
        if self.cell.shape != (3, 3) or abs(np.linalg.det(self.cell)) < 1e-10:
            raise ValueError("The cell must be a nonsingular 3 by 3 matrix in Angstrom.")
        if len(self.numbers) != len(self.positions) or self.origin.shape != (3,):
            raise ValueError("Invalid atom or origin dimensions.")
        if any(
            not np.all(np.isfinite(x))
            for x in (self.values, self.cell, self.positions, self.origin)
        ):
            raise ValueError("Field and geometry must contain finite numbers.")

    @property
    def volume(self):
        return float(abs(np.linalg.det(self.cell)))

    @property
    def voxel_volume(self):
        return self.volume / self.values.size

    @property
    def integral(self):
        return float(self.values.sum() * self.voxel_volume)

    def sample(self, points):
        """Periodic trilinear sampling at Cartesian points, including skew cells."""
        frac = (np.asarray(points) - self.origin) @ np.linalg.inv(self.cell)
        coords = (frac % 1.0) * np.asarray(self.values.shape)
        return map_coordinates(self.values, coords.T, order=1, mode="grid-wrap")

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            np.savez_compressed(
                stream,
                values=self.values,
                cell=self.cell,
                numbers=self.numbers,
                positions=self.positions,
                origin=self.origin,
                metadata=json.dumps(self.metadata),
            )

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            return cls(
                data["values"],
                data["cell"],
                data["numbers"],
                data["positions"],
                json.loads(str(data["metadata"])),
                data["origin"],
            )

    def integrate_regions(self, labels):
        """Integrate an externally supplied, grid-aligned integer basin partition."""
        labels = np.asarray(labels)
        if labels.shape != self.values.shape or not np.issubdtype(labels.dtype, np.integer):
            raise ValueError("Basin labels must be an integer array matching the field grid.")
        if np.any(labels < 0):
            raise ValueError("Basin labels must be nonnegative; 0 can label vacuum/unassigned.")
        ids, inverse = np.unique(labels, return_inverse=True)
        sums = np.bincount(inverse.ravel(), weights=self.values.ravel()) * self.voxel_volume
        return {int(i): float(s) for i, s in zip(ids, sums)}


def enclosing_isovalue(density, fraction=0.95):
    """Threshold enclosing a specified fraction of a nonnegative grid density."""
    if not 0 < fraction < 1:
        raise ValueError("The enclosed charge fraction must be between 0 and 1.")
    v = np.asarray(density, dtype=float).ravel()
    if not np.all(np.isfinite(v)):
        raise ValueError("The enclosing-charge criterion requires finite density.")
    positive_mass = v[v > 0].sum()
    negative_mass = -v[v < 0].sum()
    # VASP Fourier grids can have tiny negative vacuum ringing. Clip only
    # for this visualization quantile, never in the saved/integrated field.
    if negative_mass > max(1e-12, positive_mass * 1e-6):
        raise ValueError("The density has significant negative charge; check its grid or units.")
    v = np.sort(np.maximum(v, 0))[::-1]
    if not len(v) or v.sum() <= 0:
        raise ValueError("The density has no positive charge.")
    return float(v[min(np.searchsorted(np.cumsum(v), fraction * v.sum()), len(v) - 1)])
