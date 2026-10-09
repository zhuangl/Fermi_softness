"""Density-defined Bader basins using the Henkelman near-grid executable.

The partition is built from a recorded reference density, never from atom
distances. Softness and (optionally) valence density are integrated over it.
"""

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from ase.data import chemical_symbols
from scipy.signal import resample

from . import __version__
from .field import Field
from .io import read_field
from .parchg import _sha256


def resolve_executable(executable=None):
    candidates = [
        executable,
        os.environ.get("FERMI_SOFTNESS_BADER"),
        shutil.which("bader"),
        Path.cwd() / ".tools/bader/bader",
    ]
    for candidate in candidates:
        if candidate:
            path = Path(candidate).expanduser()
            if path.is_file() and os.access(path, os.X_OK):
                return path.resolve()
    raise ValueError(
        "Bader executable not found. Install the Henkelman Bader program and "
        "set FERMI_SOFTNESS_BADER or choose its executable in the Bader tab."
    )


def runtime_environment():
    env = os.environ.copy()
    if sys.platform == "darwin":
        # The official ARM binary expects gfortran's runtime. SciPy wheels carry
        # compatible libraries; no system installation or global loader change.
        import scipy

        lib = Path(scipy.__file__).parent / ".dylibs"
        if (lib / "libgfortran.5.dylib").is_file():
            env["DYLD_LIBRARY_PATH"] = str(lib) + os.pathsep + env.get("DYLD_LIBRARY_PATH", "")
    return env


def _same_geometry(a, b):
    if not np.allclose(a.cell, b.cell, atol=2e-5, rtol=1e-6):
        raise ValueError("Bader input lattices differ.")
    if (
        not np.array_equal(a.numbers, b.numbers)
        or not np.allclose(a.positions, b.positions, atol=2e-4, rtol=0)
        or not np.allclose(a.origin, b.origin, atol=1e-8, rtol=0)
    ):
        raise ValueError("Bader input atoms, atom order or grid origins differ.")


def on_reference_grid(field, reference):
    """Fourier-interpolate a sampled periodic field; never downsample Bader input."""
    _same_geometry(field, reference)
    if field.values.shape == reference.values.shape:
        return field
    if np.any(np.array(field.values.shape) > reference.values.shape):
        raise ValueError("The Bader reference must have an equal or finer grid on every axis.")
    values = field.values
    for axis, size in enumerate(reference.values.shape):
        if values.shape[axis] != size:
            values = resample(values, size, axis=axis)
    result = Field(
        values,
        field.cell,
        field.numbers,
        field.positions,
        dict(
            field.metadata,
            bader_interpolation={
                "method": "periodic Fourier",
                "source_shape": list(field.values.shape),
                "target_shape": list(reference.values.shape),
            },
        ),
        field.origin,
    )
    if not np.isclose(result.integral, field.integral, atol=1e-10, rtol=1e-11):
        raise RuntimeError("Grid interpolation did not preserve the field integral.")
    return result


def _write_density(field, path):
    if not np.allclose(field.origin, 0):
        raise ValueError("VASP-format Bader analysis requires a zero grid origin.")
    # Henkelman 1.05 reads lattice vectors as 3F13.6 and positions as 3F10.6.
    # ASE's modern 21-character columns cannot be passed to that fixed-width reader.
    from itertools import groupby

    groups = [(number, len(list(values))) for number, values in groupby(field.numbers)]
    with Path(path).open("w") as stream:
        stream.write("Fermi Softness Bader reference\n1.0000000000000000\n")
        for vector in field.cell:
            stream.write("".join(f"{v:13.6f}" for v in vector) + "\n")
        stream.write(" " + " ".join(chemical_symbols[n] for n, count in groups) + "\n")
        stream.write(" ".join(str(count) for n, count in groups) + "\nDirect\n")
        for position in field.positions @ np.linalg.inv(field.cell):
            stream.write("".join(f"{v:10.6f}" for v in position) + "\n")
        stream.write("\n" + " ".join(map(str, field.values.shape)) + "\n")
        flat = (field.values * field.volume).ravel(order="F")
        stop = len(flat) // 5 * 5
        np.savetxt(stream, flat[:stop].reshape(-1, 5), fmt="%19.11E")
        if stop < len(flat):
            stream.write(" ".join(f"{v:19.11E}" for v in flat[stop:]) + "\n")


def read_atom_indices(path, reference):
    index_field = read_field(path, density=True)
    _same_geometry(index_field, reference)
    if index_field.values.shape != reference.values.shape:
        raise ValueError("Bader atom-index grid dimensions differ from the reference.")
    # AtIndex.dat stores plain integers in CHGCAR's data block, not a density.
    raw = index_field.values * index_field.volume
    if not np.allclose(raw, np.rint(raw), atol=2e-5, rtol=0):
        raise ValueError("Bader atom-index data are not integers.")
    labels = np.rint(raw).astype(np.int32)
    natoms = len(reference.numbers)
    if labels.min() < 1 or labels.max() > natoms + 1:
        raise ValueError("Bader atom-index labels are outside the valid atom/vacuum range.")
    labels[labels == natoms + 1] = 0  # stable public convention: zero is vacuum
    return labels


def run_bader(
    field,
    references,
    output,
    *,
    charge=None,
    executable=None,
    vacuum="off",
    surface_atoms=None,
    cancelled=None,
    progress=None,
    timeout=900,
):
    """Generate basins and atomic softness. ``references`` has one or two paths."""
    program = resolve_executable(executable)
    if len(references) not in (1, 2):
        raise ValueError("Provide one reference density, or AECCAR0 and AECCAR2.")
    if vacuum not in ("off", "auto"):
        raise ValueError("Vacuum policy must be off or auto.")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose an empty Bader output directory.")
    reference = read_field(references[0], density=True)
    if "eV" in reference.metadata.get("units", ""):
        raise ValueError("Bader reference must be an electron density, not a softness field.")
    sources = [{"file": Path(references[0]).name, "sha256": _sha256(references[0])}]
    if len(references) == 2:
        other = read_field(references[1], density=True)
        if "eV" in other.metadata.get("units", ""):
            raise ValueError("Bader reference must be an electron density, not a softness field.")
        _same_geometry(reference, other)
        if reference.values.shape != other.values.shape:
            raise ValueError("AECCAR0 and AECCAR2 grids must match exactly.")
        reference.values = reference.values + other.values
        sources.append({"file": Path(references[1]).name, "sha256": _sha256(references[1])})
    if reference.integral <= 0:
        raise ValueError("Bader reference density must have a positive integral.")
    aligned = on_reference_grid(field, reference)
    valence = on_reference_grid(read_field(charge, density=True), reference) if charge else None
    natoms = len(field.numbers)
    selected = sorted(set(int(i) for i in (surface_atoms or [])))
    if any(i < 1 or i > natoms for i in selected):
        raise ValueError("Surface atom IDs are one based and must refer to existing atoms.")
    output.mkdir(parents=True, exist_ok=True)
    _write_density(reference, output / "REFERENCE.vasp")
    command = [
        str(program),
        "REFERENCE.vasp",
        "-b",
        "neargrid",
        "-r",
        "-1",
        "-p",
        "atom_index",
        "-vac",
        vacuum,
    ]
    if progress:
        progress(0, 3)
    start = time.monotonic()
    with (output / "bader.log").open("w") as log:
        process = subprocess.Popen(
            command, cwd=output, env=runtime_environment(), stdout=log, stderr=subprocess.STDOUT
        )
        try:
            while process.poll() is None:
                if cancelled and cancelled():
                    raise InterruptedError("Bader calculation cancelled.")
                if time.monotonic() - start > timeout:
                    raise TimeoutError("Bader exceeded its time limit; inspect bader.log.")
                time.sleep(0.1)
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise
    if process.returncode != 0 or not (output / "AtIndex.dat").is_file():
        raise ValueError(
            f"Bader failed (exit {process.returncode}). Inspect {output / 'bader.log'}."
        )
    labels = read_atom_indices(output / "AtIndex.dat", reference)
    if progress:
        progress(1, 3)
    softness = aligned.integrate_regions(labels)
    electrons = reference.integrate_regions(labels)
    valence_sums = valence.integrate_regions(labels) if valence else {}
    rows = []
    counts = np.bincount(labels.ravel(), minlength=natoms + 1)
    for i, (number, position) in enumerate(zip(field.numbers, field.positions), 1):
        row = {
            "atom": i,
            "element": chemical_symbols[number],
            "x_A": float(position[0]),
            "y_A": float(position[1]),
            "z_A": float(position[2]),
            "volume_A3": float(counts[i] * reference.voxel_volume),
            "softness_eV_inverse": softness.get(i, 0.0),
            "reference_grid_integral": electrons.get(i, 0.0),
        }
        if valence:
            row["valence_electrons"] = valence_sums.get(i, 0.0)
        rows.append(row)
    residual = sum(softness.values()) - aligned.integral
    if not np.isclose(sum(softness.values()), aligned.integral, atol=1e-9, rtol=1e-10):
        raise RuntimeError("Bader basin sum failed the global softness conservation check.")
    acf = {}
    for line in (output / "ACF.dat").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 7 and parts[0].isdigit() and 1 <= int(parts[0]) <= natoms:
            acf[int(parts[0])] = float(parts[4])
    if len(acf) != natoms:
        raise ValueError("Bader ACF.dat does not contain every atom.")
    acf_error = max(abs(electrons.get(i, 0.0) - acf[i]) for i in range(1, natoms + 1))
    if acf_error > 5e-4:
        raise ValueError("Imported atom labels disagree with Bader's own charge integration.")
    version = re.search(r"Version ([^)]+)", (output / "bader.log").read_text())
    report = {
        "software_version": __version__,
        "bader_version": version.group(1) if version else "unreported",
        "method": "Henkelman Bader neargrid (Tang et al., 2009)",
        "reference_sources": sources,
        "vacuum_policy": vacuum,
        "field_representation": field.metadata.get("representation", "imported field"),
        "grid": list(labels.shape),
        "interpolation": aligned.metadata.get("bader_interpolation"),
        "atoms": rows,
        "field_integral_eV_inverse": aligned.integral,
        "atomic_sum_eV_inverse": sum(r["softness_eV_inverse"] for r in rows),
        "vacuum_softness_eV_inverse": softness.get(0, 0.0),
        "conservation_error_eV_inverse": residual,
        "surface_atom_ids": selected,
        "surface_softness_eV_inverse": sum(softness.get(i, 0.0) for i in selected)
        if selected
        else None,
        "reference_density_integral": reference.integral,
        "reference_vs_acf_max_abs_error": acf_error,
        "reference_usage": "Defines basin boundaries only. Sampled core-density integrals are not atomic charges; use the valence_electrons column for populations.",
        "elapsed_seconds": time.monotonic() - start,
        "definition": "Integrate the unchanged softness field over charge-density Bader basins.",
    }
    np.savez_compressed(
        output / "basins.npz",
        labels=labels,
        cell=reference.cell,
        numbers=reference.numbers,
        positions=reference.positions,
        origin=reference.origin,
        metadata=json.dumps(report),
    )
    aligned.save(output / "softness-on-bader-grid.npz")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    with (output / "atoms.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if progress:
        progress(3, 3)
    return report


def select_basins(field, basin_path, atom_ids):
    with np.load(basin_path, allow_pickle=False) as data:
        reference = Field(
            np.zeros(data["labels"].shape),
            data["cell"],
            data["numbers"],
            data["positions"],
            {},
            data["origin"],
        )
        aligned = on_reference_grid(field, reference)
        selected = sorted(set(int(i) for i in atom_ids))
        if not selected or any(i < 1 or i > len(field.numbers) for i in selected):
            raise ValueError("Select valid, one-based Bader atom IDs.")
        mask = np.isin(data["labels"], selected)
        return Field(
            np.where(mask, aligned.values, 0),
            field.cell,
            field.numbers,
            field.positions,
            dict(
                aligned.metadata,
                bader_atom_ids=selected,
                description="Softness restricted to selected charge-density Bader basins.",
            ),
            field.origin,
        )
