"""Packaged, offline demonstration gallery with explicit scientific provenance."""

import json
from importlib.resources import files

from .demo import demo_fields
from .field import Field
from .render import Scene


def catalog():
    root = files("fermi_softness").joinpath("data")
    return json.loads(root.joinpath("catalog.json").read_text(encoding="utf-8"))


def load_demo(demo_id):
    entry = next((e for e in catalog() if e["id"] == demo_id), None)
    if entry is None:
        raise ValueError(f"Unknown demo {demo_id!r}.")
    if demo_id == "analytic":
        field, charge = demo_fields()
        return (
            field,
            charge,
            Scene(mode="charge", color_max=float(field.values.max()), cell_edges=False),
            None,
        )
    root = files("fermi_softness").joinpath(
        "data", "pt111" if demo_id == "pt111-bader" else demo_id
    )
    with root.joinpath("softness.npz").open("rb") as stream:
        field = Field.load(stream)
    with root.joinpath("charge.npz").open("rb") as stream:
        charge = Field.load(stream)
    scene = Scene(**json.loads(root.joinpath("scene.json").read_text()))
    if demo_id == "pt111-bader":
        from .bader import select_basins

        field = select_basins(field, root.joinpath("basins.npz"), [3])
        scene = Scene(
            mode="softness", isovalue=0.04, repeats=(3, 3, 1), cell_edges=False, display_stride=2
        )
    return field, charge, scene, root
