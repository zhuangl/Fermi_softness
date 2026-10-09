"""Validated VASP-to-field workflow."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import __version__
from .field import Field
from .kernel import energy_half_width, fermi_weight
from .vasprun import read_vasprun
from .wavecar import Wavecar


def _check_pair(wave, run):
    if not np.allclose(wave.cell, run.cell, atol=2e-5, rtol=2e-6):
        raise ValueError("WAVECAR and vasprun.xml have different lattices.")
    if wave.kpoints.shape != run.kpoints.shape or not np.allclose(
        wave.kpoints, run.kpoints, atol=2e-6, rtol=0
    ):
        raise ValueError("WAVECAR and vasprun.xml have different k-point lists/order.")
    if wave.energies.shape != run.eigenvalues.shape or not np.allclose(
        wave.energies, run.eigenvalues, atol=2e-4, rtol=0
    ):
        raise ValueError("WAVECAR and vasprun.xml eigenvalues do not match the same final step.")
    spinor = bool(
        run.parameters.get("LNONCOLLINEAR", False) or run.parameters.get("LSORBIT", False)
    )
    if spinor != (wave.kind == "spinor"):
        raise ValueError("Spinor settings in vasprun.xml disagree with WAVECAR storage.")
    if int(run.parameters.get("IBRION", -1)) == 0:
        raise ValueError("MD WAVECAR may contain extrapolated states. Perform a final static run.")
    if run.electronic_steps >= int(run.parameters.get("NELM", 60)):
        raise ValueError("The final electronic cycle reached NELM. Check convergence and rerun.")


def calculate(
    wavecar,
    vasprun,
    *,
    kt=0.4,
    threshold=0.001,
    mu=None,
    grid=None,
    gamma_half="x",
    allow_incomplete=False,
    allow_reduced=False,
    max_memory_gb=4.0,
    progress=None,
    cancelled=None,
):
    """Return total and spin-resolved fields. All weights are in eV^-1."""
    half_width = energy_half_width(kt, threshold)
    run = read_vasprun(vasprun)
    mu = run.efermi if mu is None else float(mu)
    warnings = []
    with Wavecar(wavecar, gamma_half=gamma_half) as wave:
        _check_pair(wave, run)
        isym = run.parameters.get("ISYM")
        permitted = (-1,) if wave.kind == "spinor" else (-1, 0)
        if isym not in permitted:
            msg = (
                "Spatial symmetry reduction is enabled or unknown. Local maps require "
                "ISYM=-1 (or ISYM=0 for scalar states). Rerun a static calculation; "
                "irreducible k-point weights alone cannot restore a local field."
            )
            if not allow_reduced:
                raise ValueError(msg)
            warnings.append(msg + " Diagnostic unsymmetrized output requested.")
        active_k = run.weights > 0
        low = wave.energies[:, active_k, :].min(axis=-1)
        high = wave.energies[:, active_k, :].max(axis=-1)
        missing = bool(np.any(low > mu - half_width) or np.any(high < mu + half_width))
        if missing:
            msg = (
                f"Bands do not cover [{mu - half_width:.4f}, {mu + half_width:.4f}] eV "
                "at every contributing k-point/spin. Increase NBANDS for missing upper "
                "states, or explicitly allow an incomplete diagnostic calculation."
            )
            if not allow_incomplete:
                raise ValueError(msg)
            warnings.append(msg)
        recommended = wave.recommended_grid()
        if grid is None:
            shape = recommended
        else:
            raw = np.asarray(grid)
            if (
                raw.shape != (3,)
                or not np.all(np.isfinite(raw))
                or not np.all(raw == raw.astype(int))
            ):
                raise ValueError("Grid must contain three positive integer dimensions.")
            shape = tuple(int(x) for x in raw)
            minimum = np.max(
                [2 * np.ptp(wave.vectors(k), axis=0) + 1 for k in range(wave.nk)], axis=0
            )
            if np.any(np.asarray(shape) < np.maximum(minimum, 2)):
                raise ValueError(
                    f"Grid too coarse; choose at least {tuple(np.maximum(minimum, 2))}."
                )
        estimated_gb = int(np.prod(shape)) * (64 + 8 * wave.nspin) / 1e9
        if not np.isfinite(max_memory_gb) or max_memory_gb <= 0 or estimated_gb > max_memory_gb:
            raise ValueError(
                f"Estimated working arrays need {estimated_gb:.2f} GB; "
                "raise the memory limit or use a smaller valid grid."
            )
        weights = fermi_weight(wave.energies, mu, kt) * run.weights[None, :, None] * wave.degeneracy
        chosen = (np.abs(wave.energies - mu) <= half_width) & active_k[None, :, None]
        states = np.argwhere(chosen)
        if not len(states):
            raise ValueError("No states lie inside the selected energy window.")
        values = np.zeros((wave.nspin, *shape))
        norm_sum = 0.0
        norm_min, norm_max = np.inf, -np.inf
        from .wavecar import density_from_coefficients

        for index, (s, k, b) in enumerate(states):
            if cancelled and cancelled():
                raise InterruptedError("Calculation cancelled; no partial result saved.")
            c = wave.coefficients(int(s), int(k), int(b))
            norm = float(np.sum(np.abs(c) ** 2))
            norm_min, norm_max = min(norm_min, norm), max(norm_max, norm)
            density = density_from_coefficients(wave.vectors(int(k)), c, wave.cell, shape)
            values[s] += weights[s, k, b] * density
            norm_sum += weights[s, k, b] * norm
            if progress:
                progress(index + 1, len(states))
        spectral = float(weights[chosen].sum())
        smooth = float(values.sum() * abs(np.linalg.det(wave.cell)) / np.prod(shape))
        if not np.isclose(smooth, norm_sum, rtol=2e-10, atol=1e-11):
            raise RuntimeError("FFT integral failed the independent coefficient-norm check.")
        metadata = {
            "software": "fermi-softness",
            "version": __version__,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "units": "eV^-1 Angstrom^-3",
            "representation": "PAW smooth pseudo-wavefunction",
            "paw_augmentation_included": False,
            "kt_eV": kt,
            "mu_eV": mu,
            "scf_efermi_eV": run.efermi,
            "kernel_cutoff_eV_inverse": threshold,
            "energy_window_eV": [mu - half_width, mu + half_width],
            "wavecar_kind": wave.kind,
            "gamma_half": gamma_half if wave.kind == "gamma" else None,
            "grid": list(shape),
            "recommended_grid": list(recommended),
            "nspin": wave.nspin,
            "spin_degeneracy": wave.degeneracy,
            "nkpoints": wave.nk,
            "nbands": wave.nb,
            "states_used": len(states),
            "kpoint_weights": run.weights.tolist(),
            "ISYM": isym,
            "spectral_softness_eV_inverse": spectral,
            "smooth_integral_eV_inverse": smooth,
            "coefficient_norm_integral_eV_inverse": float(norm_sum),
            "coefficient_norm_range": [float(norm_min), float(norm_max)],
            "known_excluded_spectral_weight_eV_inverse": float(weights[~chosen].sum()),
            "energy_window_covered": not missing,
            "diagnostic_only": bool(warnings),
            "warnings": warnings,
            "estimated_working_memory_gb": estimated_gb,
            "sources": [
                {
                    "name": Path(p).name,
                    "bytes": Path(p).stat().st_size,
                    "mtime_ns": Path(p).stat().st_mtime_ns,
                }
                for p in (wavecar, vasprun)
            ],
            "reference": "10.1002/anie.201601824",
        }
        total = Field(values.sum(axis=0), wave.cell, run.numbers, run.positions, metadata)
        channels = {}
        if wave.nspin == 2:
            for s, name in enumerate(("up", "down")):
                md = dict(metadata, spin_channel=name)
                md["smooth_integral_eV_inverse"] = float(values[s].sum() * total.voxel_volume)
                md["spectral_softness_eV_inverse"] = float(weights[s][chosen[s]].sum())
                channels[name] = Field(values[s], wave.cell, run.numbers, run.positions, md)
        return total, channels
