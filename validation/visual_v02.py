"""Desktop acceptance for legend styles, unit conversion and bundled demos."""

from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

from fermi_softness.gui import MainWindow
from fermi_softness.render import export_image

out = Path("results/local/gui-v02")
out.mkdir(parents=True, exist_ok=True)
app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
errors = []
window.error = errors.append


def check():
    try:
        window.demo_choice.setCurrentIndex(window.demo_choice.findData("pt111"))
        window.load_selected_demo()
        assert not errors, errors
        initial = window.field.values.copy()
        window.tabs.setCurrentIndex(2)
        for index, name in enumerate(("scientific", "paper2016", "presentation", "grayscale")):
            window.style_preset.setCurrentIndex(index)
            window.apply_style_preset(index)
            assert not errors, errors
            expected = 1000.0 if window.units.currentText() == "keV" else 1.0
            assert np.isclose(window.cmax.value() / expected, window.scene.color_max, atol=1e-6)
            np.testing.assert_array_equal(window.field.values, initial)
            QTest.qWait(100)
            window.grab().save(str(out / f"{name}-ui.png"))
            export_image(window.plotter, out / f"{name}.png", 1800, 1400, 300)
        for index in range(window.legend_style.count()):
            window.legend_style.setCurrentIndex(index)
            window.apply_view()
            assert not errors, errors
        window.scene.camera = None
        window.scene.save(out / "style-roundtrip.json")
        window.load_scene_path(out / "style-roundtrip.json")
        assert not errors, errors
        print(
            "Four visual styles, five legend layouts, display-unit invariance and packaged Pt demo: PASS",
            flush=True,
        )
    except Exception:
        import traceback

        traceback.print_exc()
        app.exit(1)
        return
    finally:
        window.close()
    app.quit()


QtCore.QTimer.singleShot(500, check)
raise SystemExit(app.exec())
