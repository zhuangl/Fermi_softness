"""Run on a desktop session (macOS WindowServer or Linux X/EGL)."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/fermi-mpl")
import numpy as np
from PIL import Image
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

from fermi_softness.gui import CalculationWorker, MainWindow
from fermi_softness.io import read_field
from fermi_softness.render import Scene, capture_camera, export_image

output = Path("results/local/gui")
output.mkdir(parents=True, exist_ok=True)
app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
errors = []
window.error = lambda text: errors.append(text)


def validate():
    try:
        window.load_demo()
        assert not errors, errors
        QTest.qWait(300)
        window.grab().save(str(output / "studio.png"))
        for mode, name in enumerate(("isosurface", "charge", "slice")):
            window.mode.setCurrentIndex(mode)
            window.apply_view()
            assert not errors, errors
            window.plotter.camera.azimuth += 17
            before = capture_camera(window.plotter)
            window.apply_view()
            after = capture_camera(window.plotter)
            np.testing.assert_allclose(before["position"], after["position"])
            export_image(window.plotter, output / f"{name}.png", 1800, 1400, 300)
            with Image.open(output / f"{name}.png") as image:
                assert image.size == (1800, 1400)
                assert abs(image.info["dpi"][0] - 300) < 1
                assert np.asarray(image).std() > 10
        export_image(window.plotter, output / "transparent.tiff", 1000, 800, 600, True)
        with Image.open(output / "transparent.tiff") as image:
            assert image.mode == "RGBA"
            assert image.size == (1000, 800)
        window.scene.camera = capture_camera(window.plotter)
        window.scene.save(output / "view.json")
        restored = Scene.load(output / "view.json")
        assert restored.camera == window.scene.camera
        window.load_scene_path(output / "view.json")
        assert not errors, errors
        native_manifest = Path("results/local/pt111-native-input/manifest.json")
        if native_manifest.exists():
            completed = []
            worker = CalculationWorker(
                {"manifest_path": native_manifest}, window, operation="parchg"
            )
            worker.result.connect(lambda field, channels: completed.append(field))
            worker.failed.connect(errors.append)
            loop = QtCore.QEventLoop()
            worker.finished.connect(loop.quit)
            QtCore.QTimer.singleShot(45000, loop.quit)
            worker.start()
            loop.exec()
            assert not worker.isRunning() and completed and not errors, errors
            window.set_field(completed[0], read_field("results/local/pt111/CHGCAR", density=True))
            window.load_scene_path("docs/images/pt111-native.png.scene.json")
            assert not errors, errors
            QTest.qWait(300)
            window.grab().save(str(output / "studio-native.png"))
            print("Native PARCHG background worker and real Pt(111) GUI: PASS", flush=True)
        print("GUI rotation, modes, camera persistence, PNG/TIFF and DPI: PASS", flush=True)
    except Exception:
        import traceback

        traceback.print_exc()
        app.exit(1)
        return
    finally:
        window.close()
    app.quit()


QtCore.QTimer.singleShot(600, validate)
raise SystemExit(app.exec())
