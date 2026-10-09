"""Native VASP partial-density route, retaining VASP's augmentation treatment."""

import gzip
import hashlib
import json
import re
import tempfile
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.calculators.vasp import VaspChargeDensity
from ase.io import write

from . import __version__
from .compute import _check_pair
from .field import Field
from .kernel import energy_half_width, fermi_weight
from .vasprun import read_vasprun
from .wavecar import Wavecar


def _sha256(path, cancelled=None):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            if cancelled and cancelled():
                raise InterruptedError("Source verification cancelled.")
            digest.update(block)
    return digest.hexdigest()


def prepare_parchg(
    wavecar, vasprun, output, *, incar=None, kt=0.4, threshold=0.001, cancelled=None
):
    """Write a reproducible LPARD deck and a manifest; do not invoke VASP."""
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose an empty directory for the VASP partial-density deck.")
    incar = Path(incar) if incar else Path(vasprun).parent / "INCAR"
    if not incar.is_file():
        raise ValueError("The original INCAR is required to preserve the calculation settings.")
    run = read_vasprun(vasprun)
    half = energy_half_width(kt, threshold)
    with Wavecar(wavecar) as wave:
        _check_pair(wave, run)
        if wave.kind == "spinor":
            raise ValueError("VASP LPARD does not support noncollinear/spinor calculations.")
        if run.parameters.get("ISYM") not in (-1, 0):
            raise ValueError("Prepare this route from scalar ISYM=-1 or ISYM=0 static data.")
        active = run.weights > 0
        if np.any(wave.energies[:, active, :].min(axis=-1) > run.efermi - half) or np.any(
            wave.energies[:, active, :].max(axis=-1) < run.efermi + half
        ):
            raise ValueError("Bands do not cover the requested window. Increase NBANDS first.")
        selected = (np.abs(wave.energies - run.efermi) <= half) & active[None, :, None]
        states = []
        for k, b in np.argwhere(np.any(selected, axis=0)):
            state_weights = [
                float(run.weights[k] * fermi_weight(wave.energies[s, k, b], run.efermi, kt))
                if selected[s, k, b]
                else 0.0
                for s in range(wave.nspin)
            ]
            states.append(
                {
                    "file": f"PARCHG.{b + 1:04d}.{k + 1:04d}",
                    "band": int(b + 1),
                    "kpoint": int(k + 1),
                    "weights_eV_inverse": state_weights,
                    "energies_eV": wave.energies[:, k, b].tolist(),
                }
            )
        if not states:
            raise ValueError("No contributing states in the requested window.")
        spectral = sum(sum(s["weights_eV_inverse"]) for s in states) * wave.degeneracy
        manifest = {
            "schema": "fermi-softness-parchg-1",
            "software_version": __version__,
            "kt_eV": kt,
            "mu_eV": run.efermi,
            "kernel_cutoff_eV_inverse": threshold,
            "energy_window_eV": [run.efermi - half, run.efermi + half],
            "nspin": wave.nspin,
            "spin_degeneracy": wave.degeneracy,
            "cell": run.cell.tolist(),
            "numbers": run.numbers.tolist(),
            "positions": run.positions.tolist(),
            "states": states,
            "spectral_softness_eV_inverse": spectral,
            "source_wavecar_sha256": _sha256(wavecar, cancelled),
            "original_incar_sha256": _sha256(incar),
        }
    controlled = {
        "LPARD",
        "LPARDH5",
        "NBMOD",
        "IBAND",
        "EINT",
        "KPUSE",
        "LSEPB",
        "LSEPK",
        "KPAR",
        "NSW",
        "IBRION",
        "LWAVE",
        "LCHARG",
        "ISYM",
        "ISTART",
    }
    retained = []
    for line in incar.read_text().splitlines():
        for assignment in re.split(";", re.split(r"[!#]", line, maxsplit=1)[0]):
            key = assignment.split("=", 1)[0].strip().upper()
            if assignment.strip() and key not in controlled:
                retained.append(assignment.strip())
    retained += [
        "LPARD = .TRUE.",
        "LPARDH5 = .FALSE.",
        "NBMOD = -2",
        f"EINT = {run.efermi - half:.14g} {run.efermi + half:.14g}",
        "LSEPB = .TRUE.",
        "LSEPK = .TRUE.",
        "KPAR = 1",
        "ISYM = -1",
        "NSW = 0",
        "IBRION = -1",
        "LWAVE = .FALSE.",
        "LCHARG = .FALSE.",
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "INCAR").write_text("\n".join(retained) + "\n")
    atoms = Atoms(numbers=run.numbers, positions=run.positions, cell=run.cell)
    write(output / "POSCAR", atoms, format="vasp", direct=True, vasp5=True)
    lines = ["Explicit original k-point order", str(len(run.weights)), "Reciprocal"]
    lines += [" ".join(f"{v:.14g}" for v in [*k, w]) for k, w in zip(run.kpoints, run.weights)]
    (output / "KPOINTS").write_text("\n".join(lines) + "\n")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "RUN.md").write_text(
        "# Native VASP density preparation\n\n"
        "Copy or link the original WAVECAR and the matching licensed POTCAR into this directory.\n"
        "Run your VASP standard or Gamma executable under your normal scheduler. KPAR must be 1.\n"
        "Then run `fermi-softness compute-parchg manifest.json -o ../native-softness`.\n"
        "The manifest binds the source WAVECAR by SHA-256. Keep it here for verification.\n"
        "Gzip-compressed PARCHG files are accepted. Do not substitute band-window totals.\n"
    )
    return manifest


def _read_charge(path):
    if path.suffix == ".gz":
        with tempfile.NamedTemporaryFile(suffix=".vasp") as tmp:
            with gzip.open(path, "rb") as source:
                import shutil

                shutil.copyfileobj(source, tmp)
            tmp.flush()
            return VaspChargeDensity(tmp.name)
    return VaspChargeDensity(str(path))


def calculate_parchg(manifest_path, *, progress=None, cancelled=None):
    """Sum VASP-separated band/k densities with spin-correct derivative weights."""
    path = Path(manifest_path)
    manifest = json.loads(path.read_text())
    if manifest.get("schema") != "fermi-softness-parchg-1":
        raise ValueError("Unsupported PARCHG manifest schema.")
    source = path.parent / "WAVECAR"
    if not source.is_file() or _sha256(source, cancelled) != manifest["source_wavecar_sha256"]:
        raise ValueError(
            "The original WAVECAR is missing or differs from the manifest fingerprint."
        )
    nspin = manifest["nspin"]
    if nspin not in (1, 2) or not manifest["states"]:
        raise ValueError("Invalid PARCHG spin/state specification.")
    total = None
    channels = None
    norm_errors = []
    for index, state in enumerate(manifest["states"]):
        if cancelled and cancelled():
            raise InterruptedError("Native density calculation cancelled.")
        name = state["file"]
        if not re.fullmatch(r"PARCHG\.\d{4,}\.\d{4,}", name):
            raise ValueError("Invalid per-state PARCHG filename.")
        filename = path.parent / name
        if not filename.is_file():
            filename = filename.with_name(name + ".gz")
        if not filename.is_file():
            raise ValueError(f"Missing {name}. Run the prepared VASP LPARD job first.")
        data = _read_charge(filename)
        if len(data.chg) != 1:
            raise ValueError(f"Expected one state density in {name}.")
        atoms, rho = data.atoms[0], data.chg[0]
        if (
            not np.allclose(atoms.cell.array, manifest["cell"], atol=2e-5)
            or not np.array_equal(atoms.numbers, manifest["numbers"])
            or not np.allclose(atoms.positions, manifest["positions"], atol=2e-4)
        ):
            raise ValueError(f"Structure mismatch in {name}.")
        if not np.all(np.isfinite(rho)):
            raise ValueError(f"Non-finite density in {name}.")
        if total is None:
            total = np.zeros_like(rho)
            channels = np.zeros((nspin, *rho.shape))
        elif rho.shape != total.shape:
            raise ValueError("All PARCHG files must share the same fine grid.")
        if nspin == 1:
            densities = [rho]  # ISPIN=1 PARCHG already contains the factor of two.
        else:
            if len(data.chgdiff) != 1 or data.chgdiff[0].shape != rho.shape:
                raise ValueError(f"Spin magnetization channel is missing in {name}.")
            densities = [(rho + data.chgdiff[0]) / 2, (rho - data.chgdiff[0]) / 2]
        weights = np.asarray(state["weights_eV_inverse"], dtype=float)
        if weights.shape != (nspin,) or np.any(weights < 0) or not np.all(np.isfinite(weights)):
            raise ValueError("Invalid per-state derivative weights.")
        for s, density in enumerate(densities):
            norm = density.mean() * abs(np.linalg.det(atoms.cell.array))
            norm_errors.append(float(abs(norm - (2 if nspin == 1 else 1))))
            if not np.isfinite(norm) or norm_errors[-1] > 0.005:
                raise ValueError(
                    f"State normalization in {name} is inconsistent with native LPARD."
                )
            channels[s] += weights[s] * density
        if progress:
            progress(index + 1, len(manifest["states"]))
    total = channels.sum(axis=0)
    metadata = {
        "software": "fermi-softness",
        "version": __version__,
        "units": "eV^-1 Angstrom^-3",
        "representation": "VASP native LPARD charge density",
        "paw_augmentation_included": True,
        "all_electron_reconstruction": False,
        "kt_eV": manifest["kt_eV"],
        "mu_eV": manifest["mu_eV"],
        "kernel_cutoff_eV_inverse": manifest["kernel_cutoff_eV_inverse"],
        "energy_window_eV": manifest["energy_window_eV"],
        "spectral_softness_eV_inverse": manifest["spectral_softness_eV_inverse"],
        "states_files": len(manifest["states"]),
        "nspin": nspin,
        "source_wavecar_sha256": manifest["source_wavecar_sha256"],
        "max_state_norm_error": max(norm_errors),
        "diagnostic_only": False,
        "warnings": [],
        "reference": "10.1002/anie.201601824",
    }
    field = Field(total, manifest["cell"], manifest["numbers"], manifest["positions"], metadata)
    metadata["native_integral_eV_inverse"] = field.integral
    if not np.isclose(
        field.integral, manifest["spectral_softness_eV_inverse"], rtol=0.003, atol=1e-8
    ):
        raise ValueError("Native density integral is inconsistent with the spectral sum.")
    spin_fields = {}
    if nspin == 2:
        for s, name in enumerate(("up", "down")):
            md = dict(metadata, spin_channel=name)
            spin_fields[name] = Field(channels[s], field.cell, field.numbers, field.positions, md)
            md["native_integral_eV_inverse"] = spin_fields[name].integral
    return field, spin_fields
