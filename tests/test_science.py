import numpy as np
import pytest
from conftest import make_pair, reference_vectors
from scipy.integrate import quad

from fermi_softness.compute import calculate
from fermi_softness.kernel import energy_half_width, fermi_weight
from fermi_softness.wavecar import Wavecar, density_from_coefficients, g_vectors


def test_derivative_and_normalization():
    for kt in (0.01, 0.4, 2):
        assert quad(lambda e: fermi_weight(e, kt=kt), -40 * kt, 40 * kt)[0] == pytest.approx(1)
        assert fermi_weight(0, kt=kt) == pytest.approx(1 / (4 * kt))
        e = np.array([-0.3, 0.0, 0.3]) * kt
        h = kt * 1e-5

        def f(x):
            return 1 / (1 + np.exp(x / kt))

        np.testing.assert_allclose(
            fermi_weight(e, kt=kt), (f(e - h) - f(e + h)) / (2 * h), rtol=1e-8
        )
    assert np.isfinite(fermi_weight(1e6))
    assert fermi_weight(energy_half_width(), kt=0.4) == pytest.approx(0.001)


@pytest.mark.parametrize("kt", [0, -1, np.nan, np.inf])
def test_invalid_temperature(kt):
    with pytest.raises(ValueError):
        fermi_weight(0, kt=kt)


def test_direct_fourier_interference_and_norm(pair):
    path, _, coeffs, vectors, _, cell = pair
    with Wavecar(path) as wave:
        shape = wave.recommended_grid()
        rho = wave.density(0, 0, 1, shape)
    frac = np.stack(np.meshgrid(*[np.arange(n) / n for n in shape], indexing="ij"), axis=-1)
    direct = np.exp(2j * np.pi * frac.reshape(-1, 3) @ vectors[0].T) @ coeffs[0, 0, 1][0]
    expected = (np.abs(direct) ** 2 / abs(np.linalg.det(cell))).reshape(shape)
    np.testing.assert_allclose(rho, expected, atol=3e-10)
    assert rho.mean() * abs(np.linalg.det(cell)) == pytest.approx(0.59, rel=1e-7)
    assert np.ptp(rho) > 0.005  # verifies actual spatial interference, not just an integral


@pytest.mark.parametrize(
    "kind,nspin", [("standard", 1), ("standard", 2), ("spinor", 1), ("gamma", 1)]
)
def test_weighted_sum_spin_and_norm(tmp_path, kind, nspin):
    p, x, coeff, _, energies, _ = make_pair(tmp_path, kind=kind, nspin=nspin)
    field, channels = calculate(p, x)
    degeneracy = 2 if nspin == 1 and kind != "spinor" else 1
    expected = sum(np.sum(abs(coeff[s, 0, 1]) ** 2) for s in range(nspin)) * degeneracy / (4 * 0.4)
    assert field.integral == pytest.approx(expected, rel=1e-7)
    assert field.metadata["spectral_softness_eV_inverse"] == pytest.approx(
        nspin * degeneracy / (4 * 0.4)
    )
    assert not field.metadata["diagnostic_only"]
    if channels:
        np.testing.assert_allclose(field.values, channels["up"].values + channels["down"].values)


def test_unoccupied_states_and_nonuniform_kpoints(tmp_path):
    energies = np.array([[[-8.0, -0.2, 8.0], [-8.0, 0.7, 8.0]]])
    p, x, coeff, _, _, _ = make_pair(
        tmp_path, kpoints=[[0, 0, 0], [0.1, 0, 0]], weights=[0.2, 0.8], energies=energies
    )
    field, _ = calculate(p, x)
    expected = 2 * sum(
        kw * fermi_weight(e) * np.sum(abs(coeff[0, k, 1]) ** 2)
        for k, (e, kw) in enumerate(zip((-0.2, 0.7), (0.2, 0.8)))
    )
    assert field.integral == pytest.approx(expected, rel=1e-7)


@pytest.mark.parametrize("rtag,endian", [(45200, "<"), (45210, "<"), (53300, ">"), (53310, ">")])
def test_precision_and_endianness(tmp_path, rtag, endian):
    p, *_ = make_pair(tmp_path, rtag=rtag, endian=endian)
    with Wavecar(p) as wave:
        assert wave.coefficients(0, 0, 1)[0, 0] == pytest.approx(0.7)


@pytest.mark.parametrize("axis", ["x", "z"])
def test_gamma_storage_and_multirecord_metadata(tmp_path, axis):
    p, _, c, _, _, _ = make_pair(
        tmp_path, kind="gamma", gamma_half=axis, rtag=53300, energies=[-8, -4, 0, 4, 8], recl=104
    )
    with Wavecar(p, gamma_half=axis) as wave:
        assert wave.metadata_records == 2
        np.testing.assert_allclose(wave.coefficients(0, 0, 2), c[0, 0, 2], atol=3e-8)


def test_skew_cell_g_vectors():
    cell = np.array([[4, 0, 0], [3.8, 1.2, 0], [1.1, 0.4, 4.1]])
    k = np.array([0.31, -0.27, 0.1])
    actual = g_vectors(cell, 100, k)
    assert len(actual) > 5
    np.testing.assert_array_equal(actual, reference_vectors(cell, 100, k))


def test_fft_alias_rejected():
    with pytest.raises(ValueError, match="aliasing"):
        density_from_coefficients(np.array([[-1, 0, 0], [1, 0, 0]]), [1, 1], np.eye(3), (4, 3, 3))


@pytest.mark.parametrize("kind,isym", [("standard", 2), ("spinor", 0)])
def test_reduced_mesh_rejected(tmp_path, kind, isym):
    p, x, *_ = make_pair(tmp_path, kind=kind, isym=isym)
    with pytest.raises(ValueError, match="symmetry"):
        calculate(p, x)
    f, _ = calculate(p, x, allow_reduced=True)
    assert f.metadata["diagnostic_only"]


def test_incomplete_bands_rejected(tmp_path):
    p, x, *_ = make_pair(tmp_path, energies=[-8, 0, 1])
    with pytest.raises(ValueError, match="NBANDS"):
        calculate(p, x)
    f, _ = calculate(p, x, allow_incomplete=True)
    assert not f.metadata["energy_window_covered"]


@pytest.mark.parametrize(
    "old,new,message",
    [
        ("<r>0.0 0</r>", "<r>0.1 0</r>", "eigenvalues"),
        ("<i name='IBRION' type='int'>-1</i>", "<i name='IBRION' type='int'>0</i>", "MD WAVECAR"),
        ("<i name='NELM' type='int'>60</i>", "<i name='NELM' type='int'>1</i>", "NELM"),
    ],
)
def test_bad_pair_rejected(pair, old, new, message):
    p, x, *_ = pair
    assert old in x.read_text()
    x.write_text(x.read_text().replace(old, new))
    with pytest.raises(ValueError, match=message):
        calculate(p, x)


def test_memory_cancel_and_grid_guards(pair):
    p, x, *_ = pair
    with pytest.raises(ValueError, match="coarse"):
        calculate(p, x, grid=(2, 2, 2))
    with pytest.raises(ValueError, match="memory"):
        calculate(p, x, max_memory_gb=1e-9)
    with pytest.raises(InterruptedError):
        calculate(p, x, cancelled=lambda: True)


def test_truncated_wavecar_rejected(pair):
    p, *_ = pair
    p.write_bytes(p.read_bytes()[:-8])
    with pytest.raises(ValueError, match="truncated"):
        Wavecar(p)
