"""Extract only the metadata needed for softness, without retaining DOS/PDOS."""

import gzip
from dataclasses import dataclass

import numpy as np
from ase.data import atomic_numbers
from defusedxml.ElementTree import iterparse


@dataclass
class RunInfo:
    cell: np.ndarray
    numbers: np.ndarray
    positions: np.ndarray
    kpoints: np.ndarray
    weights: np.ndarray
    eigenvalues: np.ndarray
    efermi: float
    parameters: dict
    electronic_steps: int = 0
    occupations: np.ndarray | None = None


def _rows(node, path):
    return np.array([[float(x) for x in row.text.split()] for row in node.findall(path)])


def read_vasprun(path):
    params, symbols, structs = {}, [], {}
    kpoints = weights = eigenvalues = efermi = occupations = None
    stack = []
    electronic_steps = last_steps = 0
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rb") as stream:
        for event, node in iterparse(stream, events=("start", "end")):
            if event == "start":
                stack.append(node.tag)
                continue
            parent = stack[-2] if len(stack) > 1 else None
            if node.tag in ("parameters", "incar"):
                for item in node.iter("i"):
                    text = (item.text or "").strip()
                    name = item.get("name")
                    if name:
                        if item.get("type") == "logical":
                            value = text.upper() in ("T", ".TRUE.", "TRUE")
                        else:
                            try:
                                value = float(text)
                            except ValueError:
                                value = text
                        params[name] = value
                node.clear()
            elif node.tag == "atominfo":
                symbols = [
                    row.find("c").text.strip()
                    for row in node.findall("array[@name='atoms']/set/rc")
                ]
                node.clear()
            elif node.tag == "kpoints":
                kpoints = _rows(node, "varray[@name='kpointlist']/v")
                weights = _rows(node, "varray[@name='weights']/v").ravel()
                node.clear()
            elif node.tag == "structure":
                cell = _rows(node, "crystal/varray[@name='basis']/v")
                frac = _rows(node, "varray[@name='positions']/v")
                if cell.shape == (3, 3) and frac.ndim == 2:
                    structs[node.get("name", "last")] = (cell, frac)
                node.clear()
            elif node.tag == "eigenvalues" and parent == "calculation":
                spins = node.findall("array/set/set")
                band_rows = np.array([[_rows(k, "r") for k in s.findall("set")] for s in spins])
                eigenvalues = band_rows[..., 0]
                occupations = band_rows[..., 1]
                node.clear()
            elif node.tag == "i" and node.get("name") == "efermi":
                efermi = float(node.text)
            elif node.tag == "scstep":
                electronic_steps += 1
                node.clear()
            elif node.tag == "calculation":
                last_steps, electronic_steps = electronic_steps, 0
                node.clear()
            elif node.tag in ("projected", "dos", "dielectricfunction", "dynmat"):
                node.clear()
            stack.pop()
    if any(x is None for x in (kpoints, weights, eigenvalues, efermi)) or not symbols:
        raise ValueError(
            "vasprun.xml lacks final eigenvalues, Fermi energy, atoms or k-point weights."
        )
    geometry = structs.get("finalpos", structs.get("last", structs.get("initialpos")))
    if geometry is None:
        raise ValueError("vasprun.xml has no usable structure.")
    cell, frac = geometry
    if len(symbols) != len(frac):
        raise ValueError("Atom count does not match the final structure.")
    if (
        not np.all(np.isfinite(weights))
        or np.any(weights < 0)
        or not np.isclose(weights.sum(), 1, atol=2e-4)
    ):
        raise ValueError("Integration k-point weights must be nonnegative and sum to one.")
    if kpoints.shape != (len(weights), 3) or eigenvalues.ndim != 3:
        raise ValueError("Invalid k-point or eigenvalue dimensions in vasprun.xml.")
    numbers = np.array([atomic_numbers[s] for s in symbols])
    return RunInfo(
        cell,
        numbers,
        frac @ cell,
        kpoints,
        weights / weights.sum(),
        eigenvalues,
        float(efermi),
        params,
        last_steps,
        occupations,
    )
