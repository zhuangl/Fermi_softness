import gzip
import shutil

import numpy as np
import pytest
from ase import Atoms
from ase.calculators.vasp import VaspChargeDensity
from conftest import make_pair

from fermi_softness.kernel import fermi_weight
from fermi_softness.parchg import calculate_parchg, prepare_parchg


def native_fixture(tmp_path, nspin=1):
    energies = np.array([[[-8.0, 0.2, 8.0]], [[-8.0, 0.6, 8.0]]])[:nspin]
    p, x, _, _, _, cell = make_pair(tmp_path / "original", nspin=nspin, energies=energies)
    incar = x.parent / "INCAR"
    incar.write_text("ENCUT=10; KPAR=2 ! comment\nISPIN = %d\n" % nspin)
    out = tmp_path / "native"
    manifest = prepare_parchg(p, x, out, incar=incar)
    shutil.copyfile(p, out / "WAVECAR")
    values = np.ones((5, 5, 5)) / abs(np.linalg.det(cell))
    modulation = 0.3 * np.cos(2 * np.pi * np.arange(5) / 5)[:, None, None]
    up = values * (1 + modulation)
    down = values * (1 - modulation)
    chg = VaspChargeDensity(None)
    chg.atoms = [Atoms("H", positions=[[2, 2, 2]], cell=cell)]
    chg.chg = [2 * up if nspin == 1 else up + down]
    if nspin == 2:
        chg.chgdiff = [up - down]
    chg.write(out / manifest["states"][0]["file"], format="chgcar")
    return out, up, down, manifest


@pytest.mark.parametrize("nspin", [1, 2])
def test_native_density_weights_and_spin(tmp_path, nspin):
    out, up, down, manifest = native_fixture(tmp_path, nspin)
    field, channels = calculate_parchg(out / "manifest.json")
    expected = (
        2 * fermi_weight(0.2) * up
        if nspin == 1
        else fermi_weight(0.2) * up + fermi_weight(0.6) * down
    )
    np.testing.assert_allclose(field.values, expected, atol=1e-10)
    assert field.integral == pytest.approx(manifest["spectral_softness_eV_inverse"])
    assert field.metadata["paw_augmentation_included"]
    if nspin == 2:
        np.testing.assert_allclose(channels["up"].values, fermi_weight(0.2) * up, atol=1e-10)
    assert "KPAR = 1" in (out / "INCAR").read_text()
    assert "KPAR=2" not in (out / "INCAR").read_text()


def test_compressed_parchg_and_source_fingerprint(tmp_path):
    out, _, _, manifest = native_fixture(tmp_path)
    name = out / manifest["states"][0]["file"]
    with gzip.open(str(name) + ".gz", "wb") as stream:
        stream.write(name.read_bytes())
    name.unlink()
    assert calculate_parchg(out / "manifest.json")[0].integral > 0
    (out / "WAVECAR").write_bytes(b"wrong source")
    with pytest.raises(ValueError, match="fingerprint"):
        calculate_parchg(out / "manifest.json")


def test_incorrect_native_norm_rejected(tmp_path):
    out, _, _, manifest = native_fixture(tmp_path)
    name = out / manifest["states"][0]["file"]
    chg = VaspChargeDensity(name)
    chg.chg[0] *= 0.5
    chg.write(name, format="chgcar")
    with pytest.raises(ValueError, match="normalization"):
        calculate_parchg(out / "manifest.json")
