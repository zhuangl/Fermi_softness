import numpy as np
import pytest
from scipy.optimize import brentq

from fermi_softness.bader import on_reference_grid, resolve_executable, run_bader, select_basins
from fermi_softness.field import Field


def fields(n=80):
    shape = (n, 24, 24)
    cell = np.diag([10.0, 6.0, 6.0])
    xyz = np.stack(np.meshgrid(*[np.arange(k) / k for k in shape], indexing="ij"), axis=-1) @ cell
    atoms = np.array([[2.5, 3, 3], [7.5, 3, 3]])
    rho = np.zeros(shape)
    for position, weight in zip(atoms, (1.0, 4.0)):
        for image in (-1, 0, 1):
            dr = xyz - position - np.array([image * 10, 0, 0])
            rho += weight * np.exp(-np.sum(dr * dr, axis=-1) / 2)
    reference = Field(rho, cell, [1, 1], atoms, {"units": "Angstrom^-3"})
    softness = Field(
        np.ones(shape) / reference.volume, cell, [1, 1], atoms, {"units": "eV^-1 Angstrom^-3"}
    )
    return softness, reference


def test_fourier_reference_grid_preserves_integral():
    field, reference = fields(40)
    fine = Field(np.zeros((80, 48, 48)), reference.cell, reference.numbers, reference.positions)
    aligned = on_reference_grid(field, fine)
    assert aligned.integral == pytest.approx(field.integral, abs=1e-12)
    with pytest.raises(ValueError, match="equal or finer"):
        on_reference_grid(fine, reference)


def test_softness_cannot_be_used_as_charge_reference(tmp_path):
    field, _ = fields(40)
    field.save(tmp_path / "softness.npz")
    with pytest.raises(ValueError, match="electron density"):
        run_bader(
            field,
            [tmp_path / "softness.npz"],
            tmp_path / "out",
            executable=__import__("sys").executable,
        )


def test_real_bader_density_boundaries_and_conservation(tmp_path):
    try:
        program = resolve_executable()
    except ValueError:
        pytest.skip("Install official Henkelman Bader for this integration test")
    field, reference = fields()
    reference.save(tmp_path / "reference.npz")
    out = tmp_path / "bader"
    report = run_bader(
        field, [tmp_path / "reference.npz"], out, executable=program, surface_atoms=[1]
    )
    assert abs(report["conservation_error_eV_inverse"]) < 1e-12
    assert report["atomic_sum_eV_inverse"] == pytest.approx(1.0)
    with np.load(out / "basins.npz") as data:
        labels = data["labels"]
        assert labels[20, 12, 12] == 1 and labels[60, 12, 12] == 2

        # Unequal Gaussian densities shift the zero-flux boundary away from
        # the geometric midpoint. This distinguishes Bader from Voronoi masks.
        def derivative(x):
            return -(x - 2.5) * np.exp(-((x - 2.5) ** 2) / 2) - 4 * (x - 7.5) * np.exp(
                -((x - 7.5) ** 2) / 2
            )

        boundary = brentq(derivative, 3.5, 5.5)
        assert boundary < 4.8
        assert labels[39, 12, 12] == 2  # x=4.875 is still left of the Voronoi plane
    subset = select_basins(field, out / "basins.npz", [1])
    assert subset.integral == pytest.approx(report["surface_softness_eV_inverse"])
    assert 0 < subset.integral < 1
