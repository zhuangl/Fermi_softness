import shutil
import xml.etree.ElementTree as ET

import numpy as np
import pytest
from ase import Atoms
from ase.calculators.vasp import VaspChargeDensity
from conftest import make_pair

from fermi_softness.frozen import calculate_frozen, prepare_frozen


def fixture(tmp_path):
    wave, xml, _, _, _, cell = make_pair(tmp_path / "source")
    (xml.parent / "INCAR").write_text("ENCUT=10\nALGO=Normal\nLDIPOL=.TRUE.\n")
    out = tmp_path / "native"
    manifest = prepare_frozen(wave, xml, out)
    shutil.copyfile(wave, out / "WAVECAR")
    tree = ET.parse(xml)
    params = tree.find("parameters")
    for name, value in {
        "IALGO": 2,
        "ISMEAR": -2,
        "LDIAG": "F",
        "ICHARG": 0,
        "NELM": 1,
        "NSW": 0,
    }.items():
        old = params.find(f"i[@name='{name}']")
        if old is not None:
            params.remove(old)
        node = ET.SubElement(params, "i", name=name, type="logical" if name == "LDIAG" else "int")
        node.text = str(value)
    rows = tree.findall("calculation/eigenvalues/array/set/set/set/r")
    for row, occ in zip(rows, np.asarray(manifest["occupations"]).ravel()):
        row.text = row.text.split()[0] + f" {occ:.4f}"
    tree.write(out / "vasprun.xml")
    charge = VaspChargeDensity(None)
    charge.atoms = [Atoms("H", positions=[[2, 2, 2]], cell=cell)]
    charge.chg = [np.ones((8, 8, 8)) * manifest["weighted_nelect"] / abs(np.linalg.det(cell))]
    charge.write(out / "CHGCAR", format="chgcar")
    return out, manifest


def test_frozen_export_scale_and_import(tmp_path):
    out, manifest = fixture(tmp_path)
    occ = np.array(manifest["occupations"])
    assert occ.min() >= 0 and occ.max() <= 1
    field, _ = calculate_frozen(out / "manifest.json")
    assert field.integral == pytest.approx(manifest["spectral_softness_eV_inverse"])
    assert "ALGO = None" in (out / "INCAR").read_text()
    assert "LDIPOL = .FALSE." in (out / "INCAR").read_text()


def test_frozen_rejects_reoptimized_orbitals(tmp_path):
    out, _ = fixture(tmp_path)
    p = out / "vasprun.xml"
    p.write_text(p.read_text().replace('name="IALGO" type="int">2', 'name="IALGO" type="int">38'))
    with pytest.raises(ValueError, match="frozen-orbital"):
        calculate_frozen(out / "manifest.json")


def test_frozen_rejects_wrong_occupations(tmp_path):
    out, _ = fixture(tmp_path)
    p = out / "vasprun.xml"
    tree = ET.parse(p)
    rows = tree.findall("calculation/eigenvalues/array/set/set/set/r")
    rows[1].text = "0.0 0.8"
    tree.write(p)
    with pytest.raises(ValueError, match="occupations"):
        calculate_frozen(out / "manifest.json")
