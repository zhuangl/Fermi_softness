"""Deterministic illustration data, explicitly not a DFT prediction."""

import numpy as np

from .field import Field


def demo_fields(shape=(72, 72, 96)):
    cell = np.diag([8.4, 7.3, 13.0])
    xy = [
        (1.4, 1.4),
        (4.2, 1.4),
        (7, 1.4),
        (2.8, 3.83),
        (5.6, 3.83),
        (0, 3.83),
        (1.4, 6.26),
        (4.2, 6.26),
        (7, 6.26),
    ]
    positions = np.array([[x, y, z] for z in (4.3, 6.6) for x, y in xy])
    numbers = np.array([78] * len(positions))
    numbers[-5] = 39
    xyz = np.stack(np.meshgrid(*[np.arange(n) / n for n in shape], indexing="ij"), axis=-1) @ cell
    density = np.zeros(shape)
    softness = np.zeros(shape)
    for i, atom in enumerate(positions):
        dr = xyz - atom
        dr -= np.rint(dr / np.diag(cell)) * np.diag(cell)
        r2 = np.sum(dr**2, axis=-1)
        density += 0.9 * np.exp(-r2 / 0.82)
        softness += (0.034 if numbers[i] == 78 else 0.008) * np.exp(-r2 / 1.25)
        softness += 0.06 * (dr[..., 2] ** 2) * np.exp(-r2 / 0.86) * (1 if numbers[i] == 78 else 0.2)
    md = {
        "units": "eV^-1 Angstrom^-3",
        "synthetic": True,
        "description": "Illustration only: analytic Pt/Y-like slab, not a DFT prediction.",
        "kt_eV": 0.4,
        "reference": "10.1002/anie.201601824",
    }
    return (
        Field(softness, cell, numbers, positions, md),
        Field(density, cell, numbers, positions, {"units": "Angstrom^-3", "synthetic": True}),
    )
