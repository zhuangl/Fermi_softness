"""Exercise the real Qt timer, rotation controls, encoder and restored camera."""

import json
import tempfile
from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

from fermi_softness.gui import MainWindow
from fermi_softness.render import capture_camera

output = Path("results/local/animation-gui")
output.mkdir(parents=True, exist_ok=True)
output = Path(tempfile.mkdtemp(prefix="check-", dir=output))
app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
errors = []
window.error = errors.append


def validate():
    try:
        window.demo_choice.setCurrentIndex(window.demo_choice.findData("pt3y111"))
        window.load_selected_demo()
        assert not errors, errors
        start = capture_camera(window.plotter)
        integral = window.field.integral
        window.rotate_button.setChecked(True)
        QTest.qWait(350)
        window.stop_rotation()
        rotated = capture_camera(window.plotter)
        assert not np.allclose(start["position"][0], rotated["position"][0])
        assert not window.rotation_timer.isActive()
        window.apply_scene(window.scene)
        window.animation_width.setValue(640)
        window.animation_height.setValue(480)
        window.animation_seconds.setValue(1)
        window.animation_fps.setValue(6)
        original = capture_camera(window.plotter)
        old_size = tuple(window.plotter.window_size)
        path = output / "gui-turntable.mp4"
        window.export_movie_to(str(path))
        assert not errors, errors
        assert path.is_file()
        after = capture_camera(window.plotter)
        np.testing.assert_allclose(after["position"], original["position"], atol=1e-10)
        assert after["view_angle"] == original["view_angle"]
        assert tuple(window.plotter.window_size) == old_size
        assert window.field.integral == integral
        assert not window._exporting_animation
        assert json.loads(Path(str(path) + ".animation.json").read_text())["frames"] == 6
        cancel_path = output / "cancelled.mp4"

        def cancel_dialog():
            dialog = app.activeModalWidget()
            if isinstance(dialog, QtWidgets.QProgressDialog):
                dialog.cancel()

        QtCore.QTimer.singleShot(100, cancel_dialog)
        window.export_movie_to(str(cancel_path))
        assert not cancel_path.exists()
        np.testing.assert_allclose(capture_camera(window.plotter)["position"], original["position"])
        assert not errors, errors
        window.rotate_button.setChecked(True)
        window.orient("view_isometric")
        assert not window.rotation_timer.isActive() and not window.rotate_button.isChecked()
        window.tabs.setCurrentIndex(4)
        window.grab().save(str(output / "studio-animation.png"))
        print("GUI timer, export/cancel, fixed data and restored view: PASS; " + str(output), flush=True)
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
