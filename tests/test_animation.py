import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from fermi_softness.animation import (
    ExportCancelled,
    export_animation,
    fit_rotation_camera,
    orbit_camera,
    rotation_axis,
    validate_animation,
)
from fermi_softness.render import Scene, capture_camera


class FakePlotter:
    """No OpenGL: encoder tests use independently varying RGB frames."""

    def __init__(self):
        self.camera_position = [[2., 0., 1.], [0., 0., 1.], [0., 0., 1.]]
        self.camera = SimpleNamespace(parallel_scale=5., view_angle=33.)
        self.window_size = (320, 240)
        self.bounds = (-1., 1., -1., 1., -1., 1.)

    def reset_camera_clipping_range(self):
        pass

    def render(self):
        pass

    def screenshot(self, *, return_img, window_size, transparent_background):
        self.window_size = window_size
        width, height = window_size
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = round(100 + 40 * self.camera_position[0][0])
        frame[:, :, 1] = np.arange(width, dtype=np.uint8)
        frame[:, :, 2] = np.arange(height, dtype=np.uint8)[:, None]
        return frame


def test_rotation_geometry_closure_and_skew_surface_normal():
    camera = capture_camera(FakePlotter())
    before = copy.deepcopy(camera)
    quarter = orbit_camera(camera, [0, 0, 1], 90)
    np.testing.assert_allclose(quarter["position"][0], [0, 2, 1], atol=1e-12)
    np.testing.assert_allclose(orbit_camera(camera, [0, 0, 1], 360)["position"],
                               camera["position"], atol=1e-12)
    assert camera == before
    assert quarter["view_angle"] == 33 and quarter["parallel_scale"] == 5
    cell = np.array([[2., 0, 0], [1, 2, 1], [0, 0, 4]])
    normal = rotation_axis("normal", cell, camera)
    assert abs(normal @ cell[0]) < 1e-12 and abs(normal @ cell[1]) < 1e-12
    assert np.linalg.norm(normal) == pytest.approx(1)
    with pytest.raises(ValueError):
        orbit_camera(camera, [0, 0, 0], 20)


@pytest.mark.parametrize("extension", ["mp4", "gif"])
def test_encoded_animation_timing_sidecars_and_view_restoration(tmp_path, extension):
    ffmpeg = pytest.importorskip("imageio_ffmpeg")
    plotter = FakePlotter()
    original = capture_camera(plotter)
    path = tmp_path / "animation space" / f"rotation.{extension}"
    scene = Scene(color_min=0.01, color_max=0.05)
    report = export_animation(plotter, path, scene, np.eye(3), width=128, height=128,
                              fps=6, seconds=1, fit=False)
    assert capture_camera(plotter) == original and plotter.window_size == (320, 240)
    assert report["frames"] == 6 and not report["duplicate_endpoint"]
    assert report["color_range_eV_inverse_Angstrom_inverse3"] == [0.01, 0.05]
    assert json.loads(path.with_name(path.name + ".scene.json").read_text())["camera"] == original
    assert json.loads(path.with_name(path.name + ".animation.json").read_text()) == report
    if extension == "mp4":
        reader = ffmpeg.read_frames(str(path), pix_fmt="rgb24")
        metadata = next(reader)
        decoded = list(reader)
        assert metadata["size"] == (128, 128)
        assert metadata["fps"] == pytest.approx(6)
        assert len(decoded) == 6 and decoded[0] != decoded[3]
    else:
        from PIL import Image

        with Image.open(path) as movie:
            assert movie.size == (128, 128) and movie.n_frames == 6
            assert movie.info["loop"] == 0
            duration = 0
            for i in range(movie.n_frames):
                movie.seek(i)
                duration += movie.info["duration"]
            assert abs(duration - 1000) <= 50
    assert not list(path.parent.glob(".fermi-animation-*"))


def test_cancel_and_existing_outputs_preserve_files_and_camera(tmp_path):
    pytest.importorskip("imageio_ffmpeg")
    plotter = FakePlotter()
    original = capture_camera(plotter)
    path = tmp_path / "cancel.mp4"
    done = []
    with pytest.raises(ExportCancelled):
        export_animation(plotter, path, Scene(), np.eye(3), width=128, height=128,
                         fps=6, seconds=1, progress=lambda n, *_: done.append(n),
                         cancelled=lambda: len(done) >= 2)
    assert capture_camera(plotter) == original and plotter.window_size == (320, 240)
    assert not list(tmp_path.iterdir())
    path.write_bytes(b"preserve me")
    with pytest.raises(ValueError, match="already exists"):
        export_animation(plotter, path, Scene(), np.eye(3), width=128, height=128,
                         fps=6, seconds=1)
    assert path.read_bytes() == b"preserve me"
    assert capture_camera(plotter) == original


def test_animation_rejects_invalid_dimensions_and_duration():
    with pytest.raises(ValueError, match="even"):
        validate_animation("test.mp4", 129, 128, 30, 12, 1)
    with pytest.raises(ValueError, match="two frames"):
        validate_animation("test.gif", 128, 128, 1, 0.25, 1)
    with pytest.raises(ValueError, match="duration"):
        validate_animation("test.mp4", 128, 128, 30, float("nan"), 1)


def test_full_rotation_fit_preserves_direction_and_contains_bounds():
    camera = capture_camera(FakePlotter())
    bounds = (-2, 2, -3, 3, -1, 1)
    fitted = fit_rotation_camera(camera, bounds, 1280, 720, False)
    eye, focus, _ = np.array(fitted["position"])
    np.testing.assert_allclose((eye - focus) / np.linalg.norm(eye - focus), [1, 0, 0])
    radius = np.linalg.norm([2, 3, 2])
    assert np.linalg.norm(eye - focus) * np.sin(np.deg2rad(33 / 2)) >= radius
    ortho = fit_rotation_camera(camera, bounds, 480, 640, True)
    assert ortho["parallel_scale"] * 480 / 640 >= radius
