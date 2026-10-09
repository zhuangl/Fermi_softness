"""Optional real VASP regressions; fixtures are fetched with the validation script."""

from pathlib import Path

import numpy as np
import pytest

from fermi_softness.wavecar import Wavecar

DATA = Path(__file__).resolve().parents[1] / "validation/data"


@pytest.mark.parametrize(
    "name,kind",
    [
        ("WAVECAR.N2", "standard"),
        ("WAVECAR.N2.spin", "standard"),
        ("WAVECAR.H2_low_symm", "standard"),
        ("WAVECAR.H2_low_symm.gamma", "gamma"),
        ("WAVECAR.H2.ncl", "spinor"),
        ("WAVECAR.frac_encut", "standard"),
    ],
)
def test_real_vasp_reader_and_independent_fourier(name, kind):
    if not (DATA / name).exists():
        pytest.skip("Fetch public fixtures with validation/fetch_public_fixtures.py")
    with Wavecar(DATA / name) as wave:
        assert wave.kind == kind
        shape = wave.recommended_grid()
        rho = wave.density(0, 0, 0, shape)
        coeff = wave.coefficients(0, 0, 0)
        g = wave.vectors(0)
        for ijk in ([0, 0, 0], [1, 2, 3], [3, 1, 2]):
            phase = np.exp(2j * np.pi * (g @ (np.array(ijk) / shape)))
            direct = np.sum(abs(coeff @ phase) ** 2) / abs(np.linalg.det(wave.cell))
            assert rho[tuple(ijk)] == pytest.approx(direct, abs=1e-12)


def test_real_gamma_and_standard_agree():
    if not (DATA / "WAVECAR.H2_low_symm.gamma").exists():
        pytest.skip("Public fixtures are optional")
    with (
        Wavecar(DATA / "WAVECAR.H2_low_symm") as a,
        Wavecar(DATA / "WAVECAR.H2_low_symm.gamma") as b,
    ):
        shape = (24, 24, 32)
        # The same physical ground-state orbital has an arbitrary global phase.
        np.testing.assert_allclose(a.density(0, 0, 0, shape), b.density(0, 0, 0, shape), atol=5e-8)
