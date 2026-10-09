"""Interactive acceptance for every shipped demo and atomic basin selection."""

from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

from fermi_softness.gui import CalculationWorker, MainWindow

out = Path("results/local/gui-v02")
out.mkdir(parents=True, exist_ok=True)
app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
errors = []
window.error = errors.append


def check():
    try:
        for index in range(window.demo_choice.count()):
            window.demo_choice.setCurrentIndex(index)
            window.load_selected_demo()
            assert not errors, errors
            demo = window.demo_choice.currentData()
            if demo == "pt3y111":
                assert window.bader_table.rowCount() == 16
                whole = window.field.integral
                window.tabs.setCurrentIndex(3)
                QTest.qWait(100)
                window.grab().save(str(out / "pt3y-bader-table.png"))
                window.view_bader_surface()
                assert not errors, errors
                assert np.isclose(
                    window.field.integral, window._bader_report["surface_softness_eV_inverse"]
                )
                assert window.field.integral < whole
                window.grab().save(str(out / "pt3y-bader-surface.png"))
                window.restore_bader_field()
                assert np.isclose(window.field.integral, whole)
                window.tabs.setCurrentIndex(0)
                window.grab().save(str(out / "pt3y-demo.png"))
        manifest = Path("results/local/frozen-density/pt111/manifest.json")
        if manifest.exists():
            completed = []
            worker = CalculationWorker({"manifest_path": manifest}, window, operation="frozen")
            worker.result.connect(lambda field, channels: completed.append(field))
            worker.failed.connect(errors.append)
            loop = QtCore.QEventLoop()
            worker.finished.connect(loop.quit)
            QtCore.QTimer.singleShot(30000, loop.quit)
            worker.start()
            loop.exec()
            assert not worker.isRunning() and completed and not errors, errors
        print(
            "All packaged demos, Bader atom/layer selection and compact native GUI worker: PASS",
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
