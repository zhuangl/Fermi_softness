"""Pixel-level regression for Retina GUI exports, including full-HD output."""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import imageio_ffmpeg
import numpy as np
import pyvista as pv
from PIL import Image
from PySide6 import QtCore, QtWidgets

from fermi_softness.gui import MainWindow
from fermi_softness.render import Scene, capture_camera, draw_scene

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--old-video", type=Path, help="Optional cropped MP4 to verify regression detection")
parser.add_argument("--sample", action="store_true", help="Also export an eight-second full-HD sample")
args = parser.parse_args()

root = Path("results/local/export-pixels")
root.mkdir(parents=True, exist_ok=True)
output = Path(tempfile.mkdtemp(prefix="check-", dir=root))
app = QtWidgets.QApplication([])
window = MainWindow()
window.resize(1180, 820)
window.show()
errors = []
window.error = errors.append


def movie_frame(path):
    if path.suffix == ".gif":
        with Image.open(path) as image:
            return np.array(image.convert("RGB"))
    reader = imageio_ffmpeg.read_frames(str(path), pix_fmt="rgb24")
    meta = next(reader)
    width, height = meta["size"]
    frame = np.frombuffer(next(reader), dtype=np.uint8).reshape(height, width, 3).copy()
    reader.close()
    return frame


def reference_pixels(scene_path, width, height):
    scene = Scene.load(scene_path)
    plotter = pv.Plotter(off_screen=True, window_size=(width, height))
    try:
        draw_scene(plotter, window.field, scene, window.charge)
        return plotter.screenshot(return_img=True, transparent_background=False)[:, :, :3]
    finally:
        plotter.close()


def model_mask(image):
    height, width = image.shape[:2]
    saturated = np.ptp(image.astype(float), axis=2) > 60
    roi = np.zeros((height, width), dtype=bool)
    # Exclude the axes and legend; require the actual 3D structure in the frame.
    roi[int(.03 * height):int(.98 * height), int(.16 * width):int(.82 * width)] = True
    return saturated & roi


def compare(actual, reference):
    assert actual.shape == reference.shape
    a, b = model_mask(actual), model_mask(reference)
    union = np.count_nonzero(a | b)
    assert union > 1000, "Missing 3D structure in reference image"
    return {
        "model_overlap": float(np.count_nonzero(a & b) / union),
        "mean_rgb_error": float(np.abs(actual.astype(float) - reference).mean()),
    }


def validate():
    report = {}
    try:
        window.demo_choice.setCurrentIndex(window.demo_choice.findData("pt3y111"))
        window.load_selected_demo()
        assert not errors, errors
        original = capture_camera(window.plotter)
        size = tuple(window.plotter.window_size)
        widget_size = (window.plotter.width(), window.plotter.height())
        report["device_pixel_ratio"] = window.plotter.devicePixelRatioF()
        report["interactive_framebuffer_size"] = size

        def forbid_widget_capture(*args, **kwargs):
            raise AssertionError("Export must not capture/resize the Qt framebuffer")

        window.plotter.screenshot = forbid_widget_capture
        for width, height, extension in ((640, 480, "mp4"), (1920, 1080, "mp4"), (640, 480, "gif")):
            window.animation_width.setValue(width)
            window.animation_height.setValue(height)
            window.animation_seconds.setValue(1)
            window.animation_fps.setValue(2)
            path = output / f"complete-{width}x{height}.{extension}"
            window.export_movie_to(str(path))
            assert not errors, errors
            actual = movie_frame(path)
            expected = reference_pixels(str(path) + ".scene.json", width, height)
            metrics = compare(actual, expected)
            assert metrics["model_overlap"] > .97, metrics
            assert metrics["mean_rgb_error"] < 4, metrics
            report[path.name] = metrics
            np.testing.assert_allclose(capture_camera(window.plotter)["position"], original["position"])
            assert tuple(window.plotter.window_size) == size
            assert (window.plotter.width(), window.plotter.height()) == widget_size
            Image.fromarray(actual).save(output / f"frame-{width}x{height}-{extension}.png")

        png = output / "complete-transparent.png"
        window.width.setValue(1600)
        window.height.setValue(900)
        window.transparent.setChecked(True)
        with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(png), "PNG")):
            window.export_picture()
        assert not errors, errors
        with Image.open(png) as image:
            assert image.size == (1600, 900) and image.mode == "RGBA"
            assert image.getchannel("A").getextrema() == (0, 255)
            actual = np.asarray(image)[:, :, :3]
            metrics = compare(actual, reference_pixels(str(png) + ".scene.json", 1600, 900))
            assert metrics["model_overlap"] > .97, metrics
            report["transparent_png"] = metrics
        assert tuple(window.plotter.window_size) == size
        np.testing.assert_allclose(capture_camera(window.plotter)["position"], original["position"])

        previous = args.old_video
        if previous is not None:
            bad = movie_frame(previous)
            expected = reference_pixels(str(previous) + ".scene.json", bad.shape[1], bad.shape[0])
            bad_metrics = compare(bad, expected)
            assert bad_metrics["model_overlap"] < .5
            report["old_gui_export_detected_as_broken"] = bad_metrics
        if args.sample:
            window.animation_width.setValue(1920)
            window.animation_height.setValue(1080)
            window.animation_seconds.setValue(8)
            window.animation_fps.setValue(24)
            window.export_movie_to(str(output / "Pt3Y-fixed-HD.mp4"))
            assert not errors, errors
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)
        print("Retina whole-frame GUI export regression: PASS; " + str(output), flush=True)
    except Exception:
        import traceback

        traceback.print_exc()
        app.exit(1)
        return
    finally:
        window.close()
    app.quit()


QtCore.QTimer.singleShot(500, validate)
raise SystemExit(app.exec())
