import numpy as np
import pytest
from ase import Atoms
from ase.calculators.vasp import VaspChargeDensity

from fermi_softness.cli import main
from fermi_softness.field import Field, enclosing_isovalue
from fermi_softness.io import read_field, write_field_cube


def sample_field():
    values = np.arange(3 * 4 * 5).reshape(3, 4, 5) / 20
    cell = np.array([[3.0, 0, 0], [0.6, 4, 0], [0.4, 0.5, 5]])
    return Field(values, cell, [6, 8], [[1, 1, 1], [2, 2, 2]], {"units": "eV^-1 Angstrom^-3"})


def test_native_and_cube_roundtrip(tmp_path):
    field = sample_field()
    for suffix in ("npz", "cube"):
        p = tmp_path / f"field.{suffix}"
        field.save(p) if suffix == "npz" else write_field_cube(field, p)
        other = read_field(p)
        np.testing.assert_allclose(other.values, field.values, atol=2e-6)
        np.testing.assert_allclose(other.cell, field.cell, atol=3e-6)
        np.testing.assert_allclose(other.positions, field.positions, atol=3e-6)
        assert other.integral == pytest.approx(field.integral, rel=3e-6)


def test_periodic_sampling_and_regions():
    f = sample_field()
    point = np.array([[1 / 3, 2 / 4, 3 / 5]]) @ f.cell
    assert f.sample(point)[0] == pytest.approx(f.values[1, 2, 3])
    assert f.sample(point + f.cell[1])[0] == pytest.approx(f.values[1, 2, 3])
    labels = np.zeros(f.values.shape, dtype=int)
    labels[1:] = 2
    assert sum(f.integrate_regions(labels).values()) == pytest.approx(f.integral)
    with pytest.raises(ValueError):
        f.integrate_regions(np.zeros((2, 2, 2)))


def test_charge_enclosure():
    density = np.array([9.0, 4.0, 2.0, 1.0, 0.0])
    assert enclosing_isovalue(density, 0.75) == 4
    assert enclosing_isovalue(np.array([-1e-8, 1.0, 2.0]), 0.6) == 2.0
    with pytest.raises(ValueError):
        enclosing_isovalue([-1, 2])


def test_chgcar_density_units_and_order(tmp_path):
    f = sample_field()
    chg = VaspChargeDensity(None)
    chg.atoms = [Atoms(numbers=f.numbers, positions=f.positions, cell=f.cell)]
    chg.chg = [f.values]
    p = tmp_path / "CHGCAR"
    chg.write(p, format="chgcar")
    other = read_field(p, density=True)
    np.testing.assert_allclose(other.values, f.values, rtol=1e-8, atol=1e-9)


def test_cli_end_to_end_and_no_overwrite(pair, tmp_path):
    p, x, *_ = pair
    dest = tmp_path / "results"
    args = ["compute", "--wavecar", str(p), "--vasprun", str(x), "-o", str(dest)]
    assert main(args) == 0
    f = Field.load(dest / "softness.npz")
    assert f.integral > 0
    assert (dest / "softness.cube").is_file()
    assert main(args) == 2
