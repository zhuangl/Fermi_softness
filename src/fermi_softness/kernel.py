"""The Fermi–Dirac derivative, evaluated without exponential overflow."""

import numpy as np


def fermi_weight(energy, mu=0.0, kt=0.4):
    """Return -df/dE in eV^-1 (kt is an energy, not a Kelvin temperature)."""
    if not np.isfinite(kt) or kt <= 0:
        raise ValueError("kT must be a positive finite energy in eV.")
    e = np.asarray(energy, dtype=float)
    if not np.isfinite(mu) or not np.all(np.isfinite(e)):
        raise ValueError("Energies and Fermi level must be finite.")
    q = np.exp(-np.abs((e - mu) / kt))
    return q / (kt * (1.0 + q) ** 2)


def energy_half_width(kt=0.4, threshold=0.001):
    """Window |E-mu| in eV for an absolute kernel threshold in eV^-1."""
    if not np.isfinite(kt) or kt <= 0:
        raise ValueError("kT must be positive and finite.")
    if not np.isfinite(threshold) or not 0 < threshold < 1 / (4 * kt):
        raise ValueError("Threshold must lie strictly between zero and the kernel peak.")
    return float(2 * kt * np.arccosh(1 / np.sqrt(4 * kt * threshold)))
