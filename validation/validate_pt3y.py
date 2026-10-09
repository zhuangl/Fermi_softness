"""Quantitative Pt3Y acceptance, with strict reproduction kept explicitly open."""

import json
from pathlib import Path

import numpy as np
from ase.io import read
from defusedxml.ElementTree import parse
from scipy.optimize import brentq

from fermi_softness.field import Field, enclosing_isovalue
from fermi_softness.io import read_field


def main():
    root = Path(__file__).resolve().parents[1]
    data = root / "results/local/pt3y111"
    native = Field.load(root / "results/local/pt3y-frozen-softness/softness.npz")
    smooth = Field.load(root / "results/local/pt3y-softness/softness.npz")
    charge = read_field(data / "CHGCAR", density=True)
    bader_path = root / "results/local/pt3y-bader-refined/report.json"
    if not bader_path.exists():
        bader_path = root / "results/local/pt3y-bader-native/report.json"
    bader = json.loads(bader_path.read_text())
    atoms = read(data / "POSCAR", format="vasp")
    fixed = set()
    for constraint in atoms.constraints:
        fixed.update(constraint.get_indices())
    free = [i for i in range(len(atoms)) if i not in fixed]
    xml = parse(data / "vasprun.xml")
    rows = xml.findall("calculation")[-1].findall("varray[@name='forces']/v")
    forces = np.array([[float(x) for x in row.text.split()] for row in rows])
    max_force = float(np.linalg.norm(forces[free], axis=1).max())
    assert max_force < 0.05
    iso = enclosing_isovalue(charge.values, 0.95)
    top = np.flatnonzero(native.positions[:, 2] > native.positions[:, 2].max() - 0.6)
    samples = []
    for index in top:
        p = native.positions[index]
        dz = np.linspace(0, 6, 1201)
        values = charge.sample(p + np.column_stack((dz * 0, dz * 0, dz))) - iso
        crossings = np.flatnonzero((values[:-1] >= 0) & (values[1:] < 0))
        if not len(crossings):
            raise ValueError("No outer density crossing above a surface atom.")
        j = crossings[-1]
        height = brentq(lambda z: charge.sample([p + [0, 0, z]])[0] - iso, dz[j], dz[j + 1])
        s = float(native.sample([p + [0, 0, height]])[0])
        samples.append(
            {
                "atom": int(index + 1),
                "element": "Pt" if native.numbers[index] == 78 else "Y",
                "height_above_atom_A": height,
                "softness_keV_inverse_A_inverse3": s * 1000,
            }
        )
    pt = np.mean([p["softness_keV_inverse_A_inverse3"] for p in samples if p["element"] == "Pt"])
    yt = np.mean([p["softness_keV_inverse_A_inverse3"] for p in samples if p["element"] == "Y"])
    assert pt > yt
    ref = Field.load(root / "results/local/pt111-native-softness/softness.npz")
    compact = Field.load(root / "results/local/pt111-frozen-softness/softness.npz")
    delta = compact.values - ref.values
    relative_l2 = float(np.linalg.norm(delta.ravel()) / np.linalg.norm(ref.values.ravel()))
    assert relative_l2 < 1e-4
    spectral = native.metadata["spectral_softness_eV_inverse"]
    report = {
        "system": "Pt3Y(111), four-layer Pt12Y4 slab",
        "functional": "PW91",
        "ENCUT_eV": 408,
        "kmesh": [6, 6, 1],
        "SCF_SIGMA_eV": 0.1,
        "kt_eV": 0.4,
        "NBANDS": 144,
        "max_free_atom_force_eV_A": max_force,
        "top_atoms": (top + 1).tolist(),
        "native_integral_eV_inverse": native.integral,
        "spectral_softness_eV_inverse": spectral,
        "native_relative_integral_error": abs(native.integral - spectral) / spectral,
        "smooth_integral_eV_inverse": smooth.integral,
        "charge_enclosure_fraction": 0.95,
        "charge_isovalue_A_inverse3": iso,
        "surface_site_samples": samples,
        "Pt_to_Y_site_ratio": float(pt / yt),
        "qualitative_Pt_high_Y_low": "PASS",
        "bader_conservation_error_eV_inverse": bader["conservation_error_eV_inverse"],
        "bader_surface_softness_eV_inverse": bader["surface_softness_eV_inverse"],
        "compact_native_vs_parchg_Pt111": {
            "max_abs_error": float(abs(delta).max()),
            "rms_error": float(np.sqrt(np.mean(delta**2))),
            "relative_L2_error": relative_l2,
        },
        "paper_color_range_keV_inverse_A_inverse3": [1, 28],
        "strict_original_reproduction": {
            "status": "NOT PASSED",
            "reason": "Original final DACAPO Pt3Y softness grid and generation script are unavailable. Absolute values differ; no empirical rescaling is applied.",
            "differences": [
                "VASP PAW versus DACAPO ultrasoft datasets",
                "Archival initial geometry rather than confirmed final original geometry",
                "Original per-state/spin normalization and Bader reference file require verification",
            ],
        },
        "slurm_jobs": {"relax_static": 342345, "native_export_validation": 342352},
    }
    (root / "results/pt3y-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
