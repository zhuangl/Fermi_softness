import numpy as np
import pytest

from fermi_softness.demos import catalog, load_demo
from fermi_softness.field import Field


def test_packaged_demo_provenance_and_bader_selection():
    assert "pt111" in [entry["id"] for entry in catalog()]
    full, charge, scene, _ = load_demo("pt111")
    selected, _, _, _ = load_demo("pt111-bader")
    assert not full.metadata.get("synthetic")
    assert selected.metadata["bader_atom_ids"] == [3]
    assert 0 < selected.integral < full.integral
    assert np.allclose(full.cell, charge.cell)


def test_periodic_display_offset_preserves_physical_sampling():
    pytest.importorskip("pyvista")
    from fermi_softness.render import vtk_grid

    shape = (8, 10, 12)
    grid = np.stack(np.meshgrid(*[np.arange(n) / n for n in shape], indexing="ij"), axis=-1)
    values = 1 + np.sin(2 * np.pi * grid[..., 0]) * np.cos(2 * np.pi * grid[..., 1])
    f = Field(values, [[3, 0, 0], [1, 4, 0], [0.4, 0.7, 5]], [1], [[0.5, 0.5, 0.5]])
    vtk = vtk_grid(f, repeats=(2, 1, 1), stride=2, offset=(-0.25, 0.3, 0))
    np.testing.assert_allclose(vtk["value"], f.sample(vtk.points), atol=1e-12)
