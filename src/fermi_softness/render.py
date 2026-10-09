"""Shared VTK scene construction for the desktop viewer and batch export."""

import json
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

import numpy as np

from .field import enclosing_isovalue


@dataclass
class Scene:
    mode: str = "softness"
    isovalue: float = 0.025
    charge_fraction: float = 0.95
    charge_isovalue: float | None = None
    cmap: str = "viridis"
    color_min: float = 0.0
    color_max: float = 0.08
    auto_color: bool = True
    opacity: float = 1.0
    repeats: tuple = (1, 1, 1)
    atoms: bool = True
    cell_edges: bool = True
    orthographic: bool = True
    plane_axis: int = 2
    plane_fraction: float = 0.55
    display_stride: int = 1
    background: str = "#f3f6fa"
    camera: dict | None = None
    colorbar_style: str = "horizontal"
    colorbar_labels: int = 5
    colorbar_format: str = "%.3f"
    colorbar_font: str = "arial"
    colorbar_font_size: int = 14
    display_units: str = "eV"
    reverse_cmap: bool = False
    display_offset: tuple = (0.0, 0.0, 0.0)
    atom_scale: float = 0.36

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), indent=2) + "\n")

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text()))


def _validate(scene):
    if not np.isfinite(scene.atom_scale) or not 0.02 <= scene.atom_scale <= 2:
        raise ValueError("Atom marker scale must lie between 0.02 and 2.")
    if len(scene.display_offset) != 3 or not np.all(np.isfinite(scene.display_offset)):
        raise ValueError("Display origin needs three finite fractional coordinates.")
    if scene.colorbar_style not in ("horizontal", "vertical", "compact", "paper", "hidden"):
        raise ValueError("Unknown colorbar style.")
    if scene.display_units not in ("eV", "keV"):
        raise ValueError("Display units must be eV or keV.")
    if scene.colorbar_font not in ("arial", "times", "courier"):
        raise ValueError("Choose Arial, Times or Courier for the colorbar.")
    if not 2 <= scene.colorbar_labels <= 12 or not 8 <= scene.colorbar_font_size <= 32:
        raise ValueError("Invalid colorbar label count or font size.")
    if scene.colorbar_format not in ("%.2f", "%.3f", "%.4f", "%.2e", "%.3g"):
        raise ValueError("Unsupported colorbar number format.")
    if scene.mode not in ("softness", "charge", "slice"):
        raise ValueError("Scene mode must be softness, charge or slice.")
    if len(scene.repeats) != 3 or any(int(n) != n or not 1 <= n <= 8 for n in scene.repeats):
        raise ValueError("Supercell repeats must be three integers between 1 and 8.")
    if (
        scene.display_stride < 1
        or int(scene.display_stride) != scene.display_stride
        or not 0 <= scene.opacity <= 1
        or not scene.color_min < scene.color_max
        or not 0 <= scene.plane_fraction <= 1
        or scene.plane_axis not in (0, 1, 2)
    ):
        raise ValueError("Invalid scene range, opacity, plane or display stride.")
    if not all(
        np.isfinite(x)
        for x in (
            scene.isovalue,
            scene.color_min,
            scene.color_max,
            scene.opacity,
            scene.plane_fraction,
        )
    ):
        raise ValueError("Scene values must be finite.")


def vtk_grid(field, repeats=(1, 1, 1), stride=1, offset=(0.0, 0.0, 0.0)):
    import pyvista as pv

    # Only display sampling is reduced; the archived scientific grid is intact.
    axes = [np.arange(0, n, stride) for n in field.values.shape]
    if any(len(a) < 2 for a in axes):
        raise ValueError("Display stride leaves fewer than two samples on an axis.")
    shifted = field.values
    if np.any(np.asarray(offset) != 0):
        from scipy.ndimage import shift

        shifted = shift(
            field.values,
            -np.asarray(offset) * field.values.shape,
            order=1,
            mode="grid-wrap",
            prefilter=False,
        )
    samples = shifted[np.ix_(*axes)]
    if int(np.prod(np.array(samples.shape) * repeats + 1)) > 12_000_000:
        raise ValueError("Display grid exceeds 12 million points. Increase display stride.")
    values = np.pad(np.tile(samples, repeats), ((0, 1),) * 3, mode="wrap")
    # Nondivisible strides need their actual positions, not an invented uniform spacing.
    frac_axes = [
        np.r_[np.concatenate([a / n + r for r in range(rep)]), float(rep)]
        for a, n, rep in zip(axes, field.values.shape, repeats)
    ]
    frac = np.stack(np.meshgrid(*frac_axes, indexing="ij"), axis=-1)
    xyz = (frac + np.asarray(offset)) @ field.cell + field.origin
    grid = pv.StructuredGrid(xyz[..., 0], xyz[..., 1], xyz[..., 2])
    grid["value"] = values.ravel(order="F")
    return grid


def capture_camera(plotter):
    return {
        "position": [list(x) for x in plotter.camera_position],
        "parallel_scale": float(plotter.camera.parallel_scale),
    }


def softness_unit_label(display_units):
    """Display typography, independent of the numerical field's stored units."""
    # VTK's bundled fonts omit the Unicode superscript minus; mathtext retains it.
    return rf"$\mathrm{{{display_units}}}^{{-1}}\,\mathrm{{\AA}}^{{-3}}$"


def scalar_bar_options(scene, color):
    title = f"Fermi softness / ({softness_unit_label(scene.display_units)})"
    options = dict(
        title=title,
        color=color,
        vertical=False,
        position_x=0.20,
        position_y=0.035,
        width=0.57,
        height=0.09,
        fmt=scene.colorbar_format,
        title_font_size=scene.colorbar_font_size,
        label_font_size=max(8, scene.colorbar_font_size - 2),
        n_labels=scene.colorbar_labels,
        font_family=scene.colorbar_font,
    )
    if scene.colorbar_style in ("vertical", "paper"):
        options.update(
            vertical=True,
            position_x=0.87,
            position_y=0.19,
            width=0.10,
            height=0.62,
            title="",
        )
    if scene.colorbar_style == "paper":
        options.update(n_labels=2, fmt="%.3g", title_font_size=max(8, scene.colorbar_font_size - 2))
    if scene.colorbar_style == "compact":
        options.update(
            position_x=0.28,
            width=0.44,
            height=0.065,
            n_labels=3,
            title=f"sF / ({softness_unit_label(scene.display_units)})",
        )
    return options


def draw_scene(plotter, field, scene, charge=None, *, preserve_camera=False):
    import pyvista as pv
    from ase.data import covalent_radii
    from ase.data.colors import jmol_colors

    _validate(scene)
    from matplotlib.colors import to_rgb

    rgb = to_rgb(scene.background)
    text_color = "white" if np.dot(rgb, [0.2126, 0.7152, 0.0722]) < 0.4 else "#27364b"
    camera = capture_camera(plotter) if preserve_camera else scene.camera
    if scene.mode == "charge":
        if charge is None:
            raise ValueError("Load CHGCAR or a charge-density Cube to color its isosurface.")
        if "eV" in charge.metadata.get("units", ""):
            raise ValueError(
                "A charge envelope requires electron density, not another softness field."
            )
        if not np.allclose(charge.cell, field.cell, rtol=1e-5, atol=1e-5):
            raise ValueError("Charge and softness fields must have the same cell.")
        if (
            not np.array_equal(charge.numbers, field.numbers)
            or not np.allclose(charge.positions, field.positions, atol=2e-4)
            or not np.allclose(charge.origin, field.origin, atol=1e-5)
        ):
            raise ValueError("Charge and softness structures/origins do not match.")
        grid = vtk_grid(charge, scene.repeats, scene.display_stride, scene.display_offset)
        iso = scene.charge_isovalue
        if iso is None:
            iso = enclosing_isovalue(charge.values, scene.charge_fraction)
        mesh = grid.contour([iso], scalars="value")
    else:
        grid = vtk_grid(field, scene.repeats, scene.display_stride, scene.display_offset)
        if scene.mode == "slice":
            axis = scene.plane_axis
            others = [i for i in range(3) if i != axis]
            normal = np.cross(field.cell[others[0]], field.cell[others[1]])
            center = np.asarray(scene.repeats, dtype=float) / 2
            center[axis] = scene.plane_fraction * scene.repeats[axis]
            mesh = grid.slice(
                normal=normal, origin=field.origin + (center + scene.display_offset) @ field.cell
            )
        else:
            mesh = grid.contour([scene.isovalue], scalars="value")
    if not mesh.n_points:
        raise ValueError("No surface at this level. Choose an isovalue within the field range.")
    mesh["softness"] = field.sample(mesh.points)
    if scene.auto_color:
        scene.color_min = float(mesh["softness"].min())
        scene.color_max = float(mesh["softness"].max())
        if scene.color_max - scene.color_min < 1e-12:
            scene.color_max = scene.color_min + max(abs(scene.color_min) * 0.01, 1e-9)
    plotter.clear()
    plotter.set_background(scene.background)
    factor = 1000.0 if scene.display_units == "keV" else 1.0
    mesh["display_softness"] = mesh["softness"] * factor
    if scene.mode == "softness":
        plotter.add_mesh(
            mesh, color="#6863c9", opacity=scene.opacity, smooth_shading=True, specular=0.25
        )
    else:
        plotter.add_mesh(
            mesh,
            scalars="display_softness",
            cmap=scene.cmap,
            flip_scalars=scene.reverse_cmap,
            clim=(scene.color_min * factor, scene.color_max * factor),
            opacity=scene.opacity,
            smooth_shading=scene.mode != "slice",
            specular=0.15,
            show_scalar_bar=scene.colorbar_style != "hidden",
            scalar_bar_args=scalar_bar_options(scene, text_color),
        )
        if scene.colorbar_style in ("vertical", "paper"):
            plotter.add_text(
                softness_unit_label(scene.display_units),
                position=(0.83, 0.12),
                viewport=True,
                font_size=9,
                color=text_color,
                name="colorbar_units",
            )
    offsets = list(product(*[range(n) for n in scene.repeats]))
    fraction = (field.positions - field.origin) @ np.linalg.inv(field.cell)
    wrapped = (
        (fraction - scene.display_offset) % 1 + scene.display_offset
    ) @ field.cell + field.origin
    if scene.atoms:
        for number in np.unique(field.numbers):
            positions = np.concatenate(
                [
                    wrapped[field.numbers == number] + np.asarray(offset) @ field.cell
                    for offset in offsets
                ]
            )
            points = pv.PolyData(positions)
            spheres = points.glyph(
                geom=pv.Sphere(
                    radius=float(covalent_radii[number] * scene.atom_scale),
                    theta_resolution=20,
                    phi_resolution=20,
                ),
                scale=False,
                orient=False,
            )
            plotter.add_mesh(spheres, color=jmol_colors[number], smooth_shading=True, specular=0.35)
    if scene.cell_edges:
        corners = {
            p: field.origin + (np.asarray(p) * scene.repeats + scene.display_offset) @ field.cell
            for p in product((0, 1), repeat=3)
        }
        lines = []
        for p, point in corners.items():
            for axis in range(3):
                if p[axis] == 0:
                    q = list(p)
                    q[axis] = 1
                    lines.extend([point, corners[tuple(q)]])
        plotter.add_lines(np.array(lines), color="#a3b1c3", width=1)
    annotation = "FERMI SOFTNESS"
    if field.metadata.get("synthetic"):
        annotation += "  /  SYNTHETIC DEMO"
    elif field.metadata.get("diagnostic_only"):
        annotation += "  /  DIAGNOSTIC ONLY"
    if field.metadata.get("benchmark_status") == "reconstruction":
        annotation += "  /  RECONSTRUCTION"
    if field.metadata.get("bader_atom_ids"):
        annotation += "  /  BADER ATOMS " + ",".join(map(str, field.metadata["bader_atom_ids"]))
    plotter.add_text(annotation, position="upper_left", color=text_color, font_size=10)
    # VTK caption text can be scaled twice by tiled screenshots. Colored axes
    # retain a stable orientation marker without oversized exported letters.
    plotter.add_axes(labels_off=True)
    if scene.orthographic:
        plotter.enable_parallel_projection()
    else:
        plotter.disable_parallel_projection()
    if camera:
        plotter.camera_position = camera["position"]
        plotter.camera.parallel_scale = camera["parallel_scale"]
    else:
        plotter.view_isometric()
        plotter.reset_camera(bounds=mesh.bounds)
    plotter.render()
    return mesh


def export_image(plotter, path, width=3600, height=2600, dpi=300, transparent=False):
    from PIL import Image

    if not 128 <= width <= 16384 or not 128 <= height <= 16384 or dpi <= 0:
        raise ValueError("Image dimensions must be 128–16384 pixels; DPI must be positive.")
    path = Path(path)
    if path.suffix.lower() not in (".png", ".tif", ".tiff"):
        raise ValueError("Choose a PNG or TIFF file.")
    # Supersample a display-sized viewport so publication text scales with pixels.
    divisors = [s for s in range(1, 17) if width % s == 0 and height % s == 0]
    scale = min(divisors, key=lambda s: abs(np.log((width / s) / 1200)))
    pixels = plotter.screenshot(
        return_img=True,
        window_size=(width // scale, height // scale),
        scale=scale,
        transparent_background=transparent,
    )
    image = Image.fromarray(pixels)
    image.save(path, dpi=(dpi, dpi))
    return path


def render_file(field, output, scene=None, charge=None, width=3600, height=2600, dpi=300):
    import pyvista as pv

    scene = scene or Scene(
        isovalue=float(np.max(field.values) * 0.4), color_max=float(np.max(field.values))
    )
    plotter = pv.Plotter(off_screen=True, window_size=(1200, 900))
    try:
        draw_scene(plotter, field, scene, charge)
        export_image(plotter, output, width, height, dpi)
        scene.camera = capture_camera(plotter)
        return scene
    finally:
        plotter.close()
