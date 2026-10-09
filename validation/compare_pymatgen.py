"""Optional independent-reader comparison over every band in public fixtures."""

import json
from pathlib import Path

import numpy as np
from pymatgen.io.vasp.outputs import Wavecar as ReferenceWavecar

from fermi_softness.wavecar import Wavecar


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "public-fixtures.json").read_text())
    report = []
    for entry in manifest["files"]:
        if entry["name"].endswith(("malformed", "45210")):
            continue
        path = root / "data" / entry["name"]
        reference = ReferenceWavecar(path)
        with Wavecar(path) as wave:
            coeff_error = energy_error = 0.0
            for k in range(wave.nk):
                lookup = {tuple(v.astype(int)): i for i, v in enumerate(reference.Gpoints[k])}
                order = [lookup[tuple(v)] for v in wave.vectors(k)]
                for s in range(wave.nspin):
                    energies = (
                        reference.band_energy[s][k] if wave.nspin == 2 else reference.band_energy[k]
                    )
                    energy_error = max(
                        energy_error,
                        float(np.max(abs(wave.energies[s, k] - np.array(energies)[:, 0]))),
                    )
                    for b in range(wave.nb):
                        coeff = (
                            reference.coeffs[s][k][b] if wave.nspin == 2 else reference.coeffs[k][b]
                        )
                        coeff = np.asarray(coeff).reshape(-1, len(wave.vectors(k)))[:, order]
                        coeff_error = max(
                            coeff_error, float(np.max(abs(wave.coefficients(s, k, b) - coeff)))
                        )
            assert coeff_error < 1e-7 and energy_error < 1e-10
            report.append(
                {
                    "file": path.name,
                    "kind": wave.kind,
                    "bands_per_spin": wave.nb,
                    "maximum_coefficient_error": coeff_error,
                    "maximum_energy_error_eV": energy_error,
                }
            )
    output = root.parent / "results/local/public-reference.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(output.read_text())


if __name__ == "__main__":
    main()
