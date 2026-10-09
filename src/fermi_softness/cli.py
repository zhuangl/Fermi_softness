"""Command line entry point; visualization dependencies remain optional."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def save_result(field, channels, output):
    from .io import write_field_cube

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    targets = [output / "softness.npz", output / "softness.cube", output / "metadata.json"]
    targets += [output / f"softness_{name}.npz" for name in channels]
    if any(p.exists() for p in targets):
        raise ValueError(f"Results already exist in {output}. Choose a new output directory.")
    field.save(targets[0])
    write_field_cube(field, targets[1])
    targets[2].write_text(json.dumps(field.metadata, indent=2) + "\n")
    for name, channel in channels.items():
        channel.save(output / f"softness_{name}.npz")
    return output


def parser():
    p = argparse.ArgumentParser(description="Fermi Softness: VASP wavefunctions to reactivity maps")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    compute = sub.add_parser("compute", help="Calculate a quantitative local softness field")
    compute.add_argument("--wavecar", default="WAVECAR")
    compute.add_argument("--vasprun", default="vasprun.xml")
    compute.add_argument("--kt", type=float, default=0.4, help="Nominal kT in eV, default 0.4")
    compute.add_argument(
        "--threshold", type=float, default=0.001, help="Absolute kernel cutoff in eV^-1"
    )
    compute.add_argument("--mu", type=float, help="Override the Fermi energy, in eV")
    compute.add_argument("--grid", nargs=3, type=int, metavar=("NX", "NY", "NZ"))
    compute.add_argument("--gamma-half", choices=("x", "z"), default="x")
    compute.add_argument("--max-memory-gb", type=float, default=4)
    compute.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Label insufficient-band output as diagnostic",
    )
    compute.add_argument(
        "--allow-reduced", action="store_true", help="Label unsymmetrized output as diagnostic"
    )
    compute.add_argument("-o", "--output", default="fermi-results")
    prepare = sub.add_parser("prepare-parchg", help="Prepare a native VASP partial-density deck")
    prepare.add_argument("--wavecar", default="WAVECAR")
    prepare.add_argument("--vasprun", default="vasprun.xml")
    prepare.add_argument("--incar")
    prepare.add_argument("--kt", type=float, default=0.4)
    prepare.add_argument("--threshold", type=float, default=0.001)
    prepare.add_argument("-o", "--output", required=True)
    native = sub.add_parser(
        "compute-parchg", help="Sum native VASP densities using a prepared manifest"
    )
    native.add_argument("manifest")
    native.add_argument("-o", "--output", required=True)
    frozen_prepare = sub.add_parser(
        "prepare-frozen", help="Prepare compact native VASP export (nonmagnetic scalar)"
    )
    frozen_prepare.add_argument("--wavecar", default="WAVECAR")
    frozen_prepare.add_argument("--vasprun", default="vasprun.xml")
    frozen_prepare.add_argument("--incar")
    frozen_prepare.add_argument("--kt", type=float, default=0.4)
    frozen_prepare.add_argument("--threshold", type=float, default=0.001)
    frozen_prepare.add_argument("-o", "--output", required=True)
    frozen = sub.add_parser(
        "compute-frozen", help="Import a validated fixed-orbital native density"
    )
    frozen.add_argument("manifest")
    frozen.add_argument("-o", "--output", required=True)
    inspect = sub.add_parser("inspect", help="Show WAVECAR format and recommended FFT grid")
    inspect.add_argument("wavecar")
    inspect.add_argument("--gamma-half", choices=("x", "z"), default="x")
    gui = sub.add_parser("gui", help="Open the interactive desktop viewer")
    gui.add_argument("field", nargs="?")
    gui.add_argument("--charge")
    gui.add_argument("--demo", action="store_true")
    gui.add_argument("--scene", help="Restore a saved view on opening")
    gui.add_argument("--example", help="Open a packaged demo (see demos command)")
    sub.add_parser("demos", help="List packaged offline demonstration surfaces")
    install = sub.add_parser(
        "install-bader", help="Download and verify the official Bader 1.05 executable"
    )
    install.add_argument("-o", "--output", default=".tools/bader")
    demo = sub.add_parser("demo", help="Generate explicitly synthetic tutorial data")
    demo.add_argument("-o", "--output", default="fermi-demo")
    render = sub.add_parser("render", help="Render a saved field to PNG or TIFF")
    render.add_argument("field")
    render.add_argument("-o", "--output", required=True)
    render.add_argument("--charge")
    render.add_argument("--scene")
    render.add_argument("--mode", choices=("softness", "charge", "slice"))
    render.add_argument("--width", type=int, default=3600)
    render.add_argument("--height", type=int, default=2600)
    render.add_argument("--dpi", type=int, default=300)
    integrate = sub.add_parser(
        "integrate", help="Integrate a grid-aligned external basin partition"
    )
    integrate.add_argument("field")
    integrate.add_argument(
        "--labels", required=True, help="Integer .npy labels, same cell/origin/grid"
    )
    integrate.add_argument("-o", "--output", required=True)
    bader = sub.add_parser("bader", help="Generate charge-density Bader basins and atomic softness")
    bader.add_argument("field")
    bader.add_argument(
        "--reference", nargs="+", required=True, help="One reference density, or AECCAR0 AECCAR2"
    )
    bader.add_argument("--charge", help="Optional valence CHGCAR for electron populations")
    bader.add_argument("--executable", help="Henkelman Bader executable")
    bader.add_argument("--vacuum", choices=("off", "auto"), default="off")
    bader.add_argument("--surface-atoms", nargs="+", type=int)
    bader.add_argument("-o", "--output", required=True)
    select = sub.add_parser(
        "select-basins", help="Export softness restricted to selected Bader atoms"
    )
    select.add_argument("field")
    select.add_argument("--basins", required=True)
    select.add_argument("--atoms", nargs="+", type=int, required=True)
    select.add_argument("-o", "--output", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare-frozen":
            from .frozen import prepare_frozen

            options = vars(args).copy()
            options.pop("command")
            manifest = prepare_frozen(**options)
            print(
                f"Prepared one native density export for {len(manifest['states'])} states. See RUN.md."
            )
        elif args.command == "compute-frozen":
            from .frozen import calculate_frozen

            field, channels = calculate_frozen(args.manifest)
            save_result(field, channels, args.output)
            print(
                json.dumps(
                    {
                        "output": str(Path(args.output).resolve()),
                        "native_integral_eV_inverse": field.integral,
                    },
                    indent=2,
                )
            )
        elif args.command == "install-bader":
            from .install_bader import install

            print(install(args.output))
        elif args.command == "demos":
            from .demos import catalog

            print(json.dumps(catalog(), indent=2, ensure_ascii=False))
        elif args.command == "bader":
            from .bader import run_bader
            from .io import read_field

            report = run_bader(
                read_field(args.field),
                args.reference,
                args.output,
                charge=args.charge,
                executable=args.executable,
                vacuum=args.vacuum,
                surface_atoms=args.surface_atoms,
            )
            print(
                json.dumps(
                    {
                        k: report[k]
                        for k in (
                            "atomic_sum_eV_inverse",
                            "vacuum_softness_eV_inverse",
                            "conservation_error_eV_inverse",
                            "surface_softness_eV_inverse",
                        )
                    },
                    indent=2,
                )
            )
        elif args.command == "select-basins":
            from .bader import select_basins
            from .io import read_field

            if Path(args.output).exists():
                raise ValueError("Output already exists; choose a new filename.")
            select_basins(read_field(args.field), args.basins, args.atoms).save(args.output)
            print(Path(args.output).resolve())
        elif args.command == "prepare-parchg":
            from .parchg import prepare_parchg

            options = vars(args).copy()
            options.pop("command")
            manifest = prepare_parchg(**options)
            print(
                f"Prepared {len(manifest['states'])} state densities in {args.output}. See RUN.md."
            )
        elif args.command == "compute-parchg":
            from .parchg import calculate_parchg

            field, channels = calculate_parchg(args.manifest)
            save_result(field, channels, args.output)
            print(
                json.dumps(
                    {
                        "output": str(Path(args.output).resolve()),
                        "native_integral_eV_inverse": field.integral,
                        "spectral_softness_eV_inverse": field.metadata[
                            "spectral_softness_eV_inverse"
                        ],
                    },
                    indent=2,
                )
            )
        elif args.command == "compute":
            from .compute import calculate

            options = vars(args).copy()
            output = options.pop("output")
            options.pop("command")
            if Path(output, "softness.npz").exists():
                raise ValueError("Output already exists. Choose a new directory.")

            def progress(done, total):
                if done == total or done == 1 or done % max(1, total // 20) == 0:
                    print(
                        f"\rReconstructing states: {done}/{total}",
                        end="",
                        file=sys.stderr,
                        flush=True,
                    )

            field, channels = calculate(**options, progress=progress)
            print(file=sys.stderr)
            save_result(field, channels, output)
            for warning in field.metadata["warnings"]:
                print("DIAGNOSTIC: " + warning, file=sys.stderr)
            print(
                json.dumps(
                    {
                        "output": str(Path(output).resolve()),
                        "spectral_softness_eV_inverse": field.metadata[
                            "spectral_softness_eV_inverse"
                        ],
                        "smooth_integral_eV_inverse": field.integral,
                        "diagnostic_only": field.metadata["diagnostic_only"],
                    },
                    indent=2,
                )
            )
        elif args.command == "inspect":
            from .wavecar import Wavecar

            with Wavecar(args.wavecar, gamma_half=args.gamma_half) as wave:
                print(
                    json.dumps(
                        {
                            "kind": wave.kind,
                            "rtag": wave.rtag,
                            "nspin": wave.nspin,
                            "nkpoints": wave.nk,
                            "nbands": wave.nb,
                            "encut_eV": wave.encut,
                            "efermi_eV": wave.efermi,
                            "recommended_grid": wave.recommended_grid(),
                        },
                        indent=2,
                    )
                )
        elif args.command == "demo":
            from .demo import demo_fields
            from .io import write_field_cube

            field, charge = demo_fields()
            output = save_result(field, {}, args.output)
            charge.save(output / "charge.npz")
            write_field_cube(charge, output / "charge.cube")
            print(f"Synthetic tutorial data: {output.resolve()}")
        elif args.command == "gui":
            from .gui import launch

            return launch(args.field, args.charge, args.demo, args.scene, args.example)
        elif args.command == "render":
            import numpy as np

            from .io import read_field
            from .render import Scene, render_file

            field = read_field(args.field)
            charge = read_field(args.charge, density=True) if args.charge else None
            scene = (
                Scene.load(args.scene)
                if args.scene
                else Scene(
                    isovalue=float(np.max(field.values) * 0.4),
                    color_max=float(np.max(field.values)),
                )
            )
            if args.mode:
                scene.mode = args.mode
            if Path(args.output).exists():
                raise ValueError("Image already exists; choose a new output path.")
            scene = render_file(
                field, args.output, scene, charge, args.width, args.height, args.dpi
            )
            scene.save(str(args.output) + ".scene.json")
            print(Path(args.output).resolve())
        elif args.command == "integrate":
            import numpy as np

            from .io import read_field

            field = read_field(args.field)
            results = field.integrate_regions(np.load(args.labels, allow_pickle=False))
            if Path(args.output).exists():
                raise ValueError("Integration output already exists; choose a new path.")
            Path(args.output).write_text(
                json.dumps(
                    {"units": "eV^-1", "basins": results, "sum": sum(results.values())}, indent=2
                )
                + "\n"
            )
    except ImportError as exc:
        print(
            f"Missing optional dependency: {exc}. Install with pip install 'fermi-softness[gui]'.",
            file=sys.stderr,
        )
        return 2
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0
