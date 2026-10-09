"""Independent miniature binary and XML fixtures, generated without VASP code."""

import itertools
import math
from pathlib import Path

import numpy as np
import pytest


def reference_vectors(cell, encut, k):
    recip = 2 * np.pi * np.linalg.inv(cell).T
    candidates = [
        v
        for v in itertools.product(range(-6, 7), repeat=3)
        if 3.80998212 * np.sum(((np.array(v) + k) @ recip) ** 2) < encut
    ]

    # positive frequencies, followed by negative frequencies, x fastest
    def frequency(i):
        return i if i >= 0 else 100 + i

    return np.array(sorted(candidates, key=lambda v: tuple(frequency(i) for i in v[::-1])))


def make_pair(
    directory,
    *,
    nspin=1,
    kind="standard",
    kpoints=None,
    weights=None,
    isym=-1,
    energies=None,
    rtag=45200,
    endian="<",
    gamma_half="x",
    recl=None,
):
    directory = Path(directory)
    directory.mkdir(exist_ok=True, parents=True)
    cell = np.diag([4.0, 4.0, 4.0])
    encut = 10.0
    kpoints = np.array([[0.0, 0.0, 0.0]] if kpoints is None else kpoints)
    nk = len(kpoints)
    weights = np.ones(nk) / nk if weights is None else np.asarray(weights)
    energies = np.array([-8.0, 0.0, 8.0] if energies is None else energies)
    if energies.ndim == 1:
        energies = np.tile(energies, (nspin, nk, 1))
    nb = energies.shape[-1]
    vectors = [reference_vectors(cell, encut, k) for k in kpoints]
    coeffs, packed = {}, {}
    for s, k, b in itertools.product(range(nspin), range(nk), range(nb)):
        g = vectors[k]
        c = np.zeros((2 if kind == "spinor" else 1, len(g)), dtype=complex)
        c[0, np.where(np.all(g == 0, axis=1))[0][0]] = 0.7
        for sign in (-1, 1):
            idx = np.where(np.all(g == [sign, 0, 0], axis=1))[0]
            if len(idx):
                c[0, idx[0]] = 0.2 * (s + 1) + sign * 0.1j
        if kind == "spinor":
            c[1] = 0.3 * c[0] * 1j
        coeffs[s, k, b] = c
        if kind == "gamma":
            a, bb, cc = (0, 1, 2) if gamma_half == "x" else (2, 1, 0)
            keep = [
                (v[a] > 0 or (v[a] == 0 and v[bb] > 0) or (v[a] == 0 and v[bb] == 0 and v[cc] >= 0))
                for v in g
            ]
            p = c[0, keep].copy()
            p[np.any(g[keep] != 0, axis=1)] *= math.sqrt(2)
        else:
            p = c.ravel()
        packed[s, k, b] = p
    precision = "c8" if rtag in (45200, 53300) else "c16"
    recl = recl or max(
        104, max(len(p) for p in packed.values()) * np.dtype(precision).itemsize, (4 + 3 * nb) * 8
    )
    meta_records = math.ceil((4 + 3 * nb) * 8 / recl)
    total_records = 2 + nspin * nk * (nb + meta_records)
    data = bytearray(total_records * recl)

    def put(record, values, dtype="f8"):
        raw = np.asarray(values, dtype=endian + dtype).tobytes()
        data[record * recl : record * recl + len(raw)] = raw

    put(0, [recl, nspin, rtag])
    put(1, [nk, nb, encut, *cell.ravel(), 0.0])
    for s, k in itertools.product(range(nspin), range(nk)):
        record = 2 + (s * nk + k) * (nb + meta_records)
        triplets = [[e, 0.0, float(e < 0)] for e in energies[s, k]]
        put(record, [len(packed[s, k, 0]), *kpoints[k], *np.array(triplets).ravel()])
        for b in range(nb):
            put(record + meta_records + b, packed[s, k, b], precision)
    (directory / "WAVECAR").write_bytes(data)

    def rows(values):
        return "".join("<v>" + " ".join(map(str, r)) + "</v>" for r in values)

    ev = "<eigenvalues><array><set>"
    for s in range(nspin):
        ev += "<set>"
        for k in range(nk):
            ev += "<set>" + "".join(f"<r>{e} {int(e < 0)}</r>" for e in energies[s, k]) + "</set>"
        ev += "</set>"
    ev += "</set></array></eigenvalues>"
    structure = (
        "<structure name='finalpos'><crystal><varray name='basis'>"
        + rows(cell)
        + "</varray></crystal><varray name='positions'><v>.5 .5 .5</v></varray></structure>"
    )
    xml = (
        f"<modeling><parameters><i name='ISYM' type='int'>{isym}</i>"
        f"<i name='LNONCOLLINEAR' type='logical'>{'T' if kind == 'spinor' else 'F'}</i>"
        "<i name='NELM' type='int'>60</i><i name='IBRION' type='int'>-1</i></parameters>"
        "<atominfo><array name='atoms'><set><rc><c>H</c><c>1</c></rc></set></array></atominfo>"
        "<kpoints><varray name='kpointlist'>"
        + rows(kpoints)
        + "</varray><varray name='weights'>"
        + rows(weights[:, None])
        + "</varray></kpoints><calculation><scstep/>"
        + ev
        + "<dos><i name='efermi'>0</i></dos></calculation>"
        + structure
        + "</modeling>"
    )
    (directory / "vasprun.xml").write_text(xml)
    return directory / "WAVECAR", directory / "vasprun.xml", coeffs, vectors, energies, cell


@pytest.fixture
def pair(tmp_path):
    return make_pair(tmp_path)
