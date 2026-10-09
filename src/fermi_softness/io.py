"""Cube and VASP density interchange; scalar units are never implicit."""

from pathlib import Path

import numpy as np
from ase.io import read
from ase.io.cube import read_cube
from ase.units import Bohr

from .field import Field


def write_field_cube(field, path):
    """Cube coordinates use Bohr; scalars retain metadata['units']."""
    comment = "Fermi Softness | values: " + field.metadata.get("units", "eV^-1 Angstrom^-3")
    if field.metadata.get("synthetic"):
        comment += " | SYNTHETIC DEMO"
    elif field.metadata.get("diagnostic_only"):
        comment += " | DIAGNOSTIC ONLY"
    with Path(path).open("w") as stream:
        stream.write(comment + "\nCoordinates in Bohr; scalar units as stated above.\n")
        stream.write(
            f"{len(field.numbers):5d} " + " ".join(f"{x:.12e}" for x in field.origin / Bohr) + "\n"
        )
        for n, vector in zip(field.values.shape, field.cell):
            stream.write(f"{n:5d} " + " ".join(f"{x:.12e}" for x in vector / n / Bohr) + "\n")
        for number, position in zip(field.numbers, field.positions):
            stream.write(
                f"{number:5d} 0.0 " + " ".join(f"{x:.12e}" for x in position / Bohr) + "\n"
            )
        # Cube runs z fastest, unlike the x-fastest VASP volumetric format.
        flat = field.values.ravel(order="C")
        stop = len(flat) // 6 * 6
        np.savetxt(stream, flat[:stop].reshape(-1, 6), fmt="%.12e")
        if stop < len(flat):
            stream.write(" ".join(f"{x:.12e}" for x in flat[stop:]) + "\n")


def read_field(path, *, density=False):
    path = Path(path)
    if path.suffix.lower() in (".npz", ".fsz"):
        return Field.load(path)
    if path.suffix.lower() in (".cube", ".cub"):
        with path.open() as stream:
            comment = stream.readline()
            stream.seek(0)
            result = read_cube(stream)
        atoms = result["atoms"]
        units = "Angstrom^-3" if density else "eV^-1 Angstrom^-3"
        if comment.startswith("Fermi Softness | values:"):
            units = comment.split("values:", 1)[1].split("|", 1)[0].strip()
        return Field(
            result["data"],
            atoms.cell.array,
            atoms.numbers,
            atoms.positions,
            {
                "units": units,
                "source": str(path.resolve()),
                "cube_comment": comment.strip(),
                "synthetic": "SYNTHETIC DEMO" in comment,
                "diagnostic_only": "DIAGNOSTIC ONLY" in comment,
                "note": "Cube scalar units taken as specified by this import mode.",
            },
            result["origin"],
        )
    if not density:
        raise ValueError("Load a .npz/.fsz field or a .cube file.")
    # ASE handles POSCAR dialects and CHGCAR normalization (stored data / cell volume).
    from ase.calculators.vasp import VaspChargeDensity

    charge = VaspChargeDensity(str(path))
    if not charge.chg:
        raise ValueError("No charge-density grid found.")
    atoms = charge.atoms[-1]
    return Field(
        charge.chg[-1],
        atoms.cell.array,
        atoms.numbers,
        atoms.positions,
        {
            "units": "Angstrom^-3",
            "source": str(path.resolve()),
            "representation": "VASP charge-density grid, first scalar channel",
        },
    )


def read_structure(path):
    return read(path, format="vasp")
