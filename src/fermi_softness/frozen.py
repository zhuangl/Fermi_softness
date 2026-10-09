"""Compact native density export using VASP's fixed-orbital postprocessing.

FERWE = 4*kT*(-df/dE), so occupations stay in [0,1]. With ALGO=None,
LDIAG=false and NELM=1, the resulting density divided by 4*kT is softness.
This scalar route is independently checked against separated PARCHG sums.
"""

import json
from pathlib import Path

import numpy as np

from . import __version__
from .field import Field
from .io import read_field
from .kernel import energy_half_width, fermi_weight
from .parchg import _sha256, prepare_parchg
from .vasprun import read_vasprun
from .wavecar import Wavecar


def prepare_frozen(
    wavecar, vasprun, output, *, incar=None, kt=0.4, threshold=0.001, cancelled=None
):
    run = read_vasprun(vasprun)
    if (
        run.eigenvalues.shape[0] != 1
        or run.parameters.get("LNONCOLLINEAR")
        or run.parameters.get("LSORBIT")
    ):
        raise ValueError(
            "Compact native export currently supports nonmagnetic scalar states. Use PARCHG for collinear spin."
        )
    manifest = prepare_parchg(
        wavecar, vasprun, output, incar=incar, kt=kt, threshold=threshold, cancelled=cancelled
    )
    # XML band energies may be rounded to four decimals. The WAVECAR values
    # are the authoritative energies for constructing the derivative weights.
    with Wavecar(wavecar) as wave:
        energies = wave.energies.copy()
    half = energy_half_width(kt, threshold)
    kernel = fermi_weight(energies, run.efermi, kt)
    kernel[np.abs(energies - run.efermi) > half] = 0
    scale = 4 * kt
    occupations = kernel * scale
    nelect = float(2 * np.sum(occupations * run.weights[None, :, None]))
    root = Path(output)
    controlled = {
        "LPARD",
        "LPARDH5",
        "NBMOD",
        "EINT",
        "IBAND",
        "LSEPB",
        "LSEPK",
        "KPUSE",
        "ALGO",
        "IALGO",
        "LDIAG",
        "NELM",
        "NELMDL",
        "ISMEAR",
        "NELECT",
        "FERWE",
        "FERDO",
        "ICHARG",
        "ISTART",
        "LWAVE",
        "LCHARG",
        "LAECHG",
        "LDIPOL",
        "NUPDOWN",
        "NBANDS",
    }
    retained = [
        line
        for line in (root / "INCAR").read_text().splitlines()
        if line.split("=", 1)[0].strip().upper() not in controlled
    ]
    retained += [
        "ALGO = None",
        "LDIAG = .FALSE.",
        "NELM = 1",
        "NELMDL = 0",
        "ISMEAR = -2",
        "ICHARG = 0",
        "ISTART = 1",
        "LWAVE = .FALSE.",
        "LCHARG = .TRUE.",
        "LAECHG = .FALSE.",
        "LDIPOL = .FALSE.",
        f"NBANDS = {run.eigenvalues.shape[-1]}",
        f"NELECT = {nelect:.15g}",
        "FERWE = " + " ".join(f"{v:.12g}" for v in occupations[0].ravel()),
    ]
    (root / "INCAR").write_text("\n".join(retained) + "\n")
    manifest.update(
        schema="fermi-softness-frozen-1",
        occupation_scale_eV=scale,
        occupations=occupations.tolist(),
        original_eigenvalues=energies.tolist(),
        kpoints=run.kpoints.tolist(),
        kpoint_weights=run.weights.tolist(),
        weighted_nelect=nelect,
    )
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (root / "RUN.md").write_text(
        "# Fixed-orbital density export\n\n"
        "Copy/link the original WAVECAR and matching POTCAR here. Run VASP using a parallel "
        "layout that preserves NBANDS. No orbital optimization is allowed.\n\n"
        "Then run `fermi-softness compute-frozen manifest.json -o ../native-softness`. "
        "The importer checks algorithm, eigenvalues, occupations, source fingerprint and integral.\n\n"
        "This folder contains a mathematical weighted-density postprocessing run. Its energies, "
        "Fermi level and CHGCAR are not ground-state physical results or restart inputs. "
        "Use the original SCF density for visualization envelopes and Bader references.\n"
    )
    return manifest


def calculate_frozen(manifest_path, *, progress=None, cancelled=None):
    root = Path(manifest_path).parent
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get("schema") != "fermi-softness-frozen-1":
        raise ValueError("Unsupported fixed-orbital manifest.")
    if (
        not (root / "WAVECAR").is_file()
        or _sha256(root / "WAVECAR", cancelled) != manifest["source_wavecar_sha256"]
    ):
        raise ValueError("Original WAVECAR missing or source fingerprint differs.")
    if progress:
        progress(0, 2)
    run = read_vasprun(root / "vasprun.xml")
    required = {"IALGO": 2, "ISMEAR": -2, "LDIAG": False, "ICHARG": 0, "NELM": 1, "NSW": 0}
    if any(run.parameters.get(key) != value for key, value in required.items()):
        raise ValueError("The output was not a verified frozen-orbital postprocessing run.")
    expected = np.asarray(manifest["original_eigenvalues"])
    if (
        run.eigenvalues.shape != expected.shape
        or not np.allclose(run.eigenvalues, expected, atol=2e-4, rtol=0)
        or not np.allclose(run.kpoints, manifest["kpoints"], atol=2e-6, rtol=0)
        or not np.allclose(run.weights, manifest["kpoint_weights"], atol=2e-6, rtol=0)
    ):
        raise ValueError("Frozen output band energies or k-point order differ from the source.")
    # vasprun.xml reports per-spin occupations to only four decimal places.
    if run.occupations is None or not np.allclose(
        run.occupations, manifest["occupations"], atol=5.1e-5, rtol=0
    ):
        raise ValueError("VASP occupations do not match the requested softness kernel.")
    charge = read_field(root / "CHGCAR", density=True)
    if (
        not np.allclose(charge.cell, manifest["cell"], atol=2e-5, rtol=1e-6)
        or not np.array_equal(charge.numbers, manifest["numbers"])
        or not np.allclose(charge.positions, manifest["positions"], atol=2e-4, rtol=0)
    ):
        raise ValueError("Frozen density geometry differs from the source.")
    scale = float(manifest["occupation_scale_eV"])
    if scale <= 0 or not np.isclose(scale, 4 * manifest["kt_eV"]):
        raise ValueError("Invalid occupation scaling in manifest.")
    metadata = {
        "software": "fermi-softness",
        "version": __version__,
        "units": "eV^-1 Angstrom^-3",
        "representation": "VASP native weighted density (fixed orbitals)",
        "paw_augmentation_included": True,
        "all_electron_reconstruction": False,
        "kt_eV": manifest["kt_eV"],
        "mu_eV": manifest["mu_eV"],
        "kernel_cutoff_eV_inverse": manifest["kernel_cutoff_eV_inverse"],
        "occupation_scale_eV": scale,
        "energy_window_eV": manifest["energy_window_eV"],
        "source_wavecar_sha256": manifest["source_wavecar_sha256"],
        "spectral_softness_eV_inverse": manifest["spectral_softness_eV_inverse"],
        "diagnostic_only": False,
        "warnings": [],
        "reference": "10.1002/anie.201601824",
    }
    field = Field(charge.values / scale, charge.cell, charge.numbers, charge.positions, metadata)
    if not np.isclose(
        field.integral, manifest["spectral_softness_eV_inverse"], atol=1e-8, rtol=1e-5
    ):
        raise ValueError("Native weighted density fails the spectral integral check.")
    metadata["native_integral_eV_inverse"] = field.integral
    if progress:
        progress(2, 2)
    return field, {}
