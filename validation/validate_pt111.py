"""Audit the local Pt(111) VASP integration fixture and export a compact report."""

import json
from pathlib import Path

import numpy as np
from pymatgen.io.vasp.outputs import Wavecar as ReferenceWavecar

from fermi_softness.field import Field
from fermi_softness.kernel import fermi_weight
from fermi_softness.vasprun import read_vasprun


def main():
    root = Path(__file__).resolve().parents[1]
    data = root / "results/local/pt111"
    run = read_vasprun(data / "vasprun.xml")
    smooth = Field.load(root / "results/local/pt111-softness/softness.npz")
    native = Field.load(root / "results/local/pt111-native-softness/softness.npz")
    reference = ReferenceWavecar(data / "WAVECAR")
    indices = np.array([[0, 0, 0], [3, 5, 71], [8, 11, 83], [13, 4, 119]])
    positions = (indices / np.array(smooth.values.shape)) @ smooth.cell
    expected = np.zeros(len(positions))
    low, high = smooth.metadata["energy_window_eV"]
    for k in range(reference.nk):
        for b in range(reference.nb):
            energy = reference.band_energy[k][b][0]
            if low <= energy <= high:
                weight = 2 * run.weights[k] * fermi_weight(energy, run.efermi, 0.4)
                for j, point in enumerate(positions):
                    value = reference.evaluate_wavefunc(k, b, point)
                    expected[j] += weight * abs(value) ** 2
    observed = smooth.values[tuple(indices.T)]
    error = float(np.max(abs(expected - observed)))
    # pymatgen's point evaluator intentionally evaluates its phase in complex64.
    assert error < 1e-7
    spectral = smooth.metadata["spectral_softness_eV_inverse"]
    relative_integral_error = abs(native.integral - spectral) / spectral
    assert relative_integral_error < 1e-5
    report = {
        "system": "Pt(111), 3 layers, 1x1 primitive surface cell",
        "vasp_version": "6.4.2 gompi",
        "ENCUT_eV": 400,
        "kmesh": [4, 4, 1],
        "ISYM": -1,
        "NBANDS": 48,
        "SCF_SIGMA_eV": 0.1,
        "SCF_EDIFF_eV": 1e-8,
        "electronic_steps": run.electronic_steps,
        "kt_eV": 0.4,
        "selected_states": smooth.metadata["states_used"],
        "smooth_grid": list(smooth.values.shape),
        "native_grid": list(native.values.shape),
        "spectral_softness_eV_inverse": spectral,
        "smooth_integral_eV_inverse": smooth.integral,
        "native_integral_eV_inverse": native.integral,
        "native_relative_integral_error": relative_integral_error,
        "native_max_state_norm_error": native.metadata["max_state_norm_error"],
        "independent_pymatgen_point_max_abs_error_eV_inverse_A_inverse3": error,
        "validation_scope": "software integration benchmark, not a convergence study or paper reproduction",
        "archive_jobs": {
            "static": 342335,
            "single_state_partial": 342336,
            "native_selected_states": 342341,
        },
    }
    path = root / "results/pt111-validation.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(path.read_text())


if __name__ == "__main__":
    main()
