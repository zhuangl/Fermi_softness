"""Local desktop application: calculation, interactive viewing and export."""

import json
import sys
from importlib.resources import as_file, files
from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtGui
from PySide6 import QtWidgets as W
from pyvistaqt import QtInteractor

from . import __version__
from .animation import (
    ExportCancelled,
    export_animation,
    fit_rotation_camera,
    orbit_camera,
    rotation_axis,
)
from .io import read_field, write_field_cube
from .render import Scene, capture_camera, draw_scene, export_image, restore_camera


class CalculationWorker(QtCore.QThread):
    progress = QtCore.Signal(int, int)
    result = QtCore.Signal(object, object)
    failed = QtCore.Signal(str)

    def __init__(self, options, parent=None, operation="wavecar"):
        super().__init__(parent)
        self.options = options
        self.operation = operation

    def run(self):
        from .compute import calculate

        try:
            if self.operation == "bader":
                from .bader import run_bader

                report = run_bader(
                    **self.options,
                    progress=self.progress.emit,
                    cancelled=self.isInterruptionRequested,
                )
                self.result.emit(report, self.options["field"])
                return
            if self.operation in ("prepare", "prepare_frozen"):
                if self.operation == "prepare_frozen":
                    from .frozen import prepare_frozen as prepare_parchg
                else:
                    from .parchg import prepare_parchg

                manifest = prepare_parchg(**self.options, cancelled=self.isInterruptionRequested)
                self.result.emit(manifest, None)
                return
            if self.operation in ("parchg", "frozen"):
                if self.operation == "frozen":
                    from .frozen import calculate_frozen as calculate_parchg
                else:
                    from .parchg import calculate_parchg

                field, channels = calculate_parchg(
                    **self.options,
                    progress=self.progress.emit,
                    cancelled=self.isInterruptionRequested,
                )
            else:
                field, channels = calculate(
                    **self.options,
                    progress=self.progress.emit,
                    cancelled=self.isInterruptionRequested,
                )
            self.result.emit(field, channels)
        except Exception as exc:
            self.failed.emit(str(exc))


def _number(value, low=0, high=1e6, decimals=4, step=0.001):
    widget = W.QDoubleSpinBox()
    widget.setRange(low, high)
    widget.setDecimals(decimals)
    widget.setSingleStep(step)
    widget.setValue(value)
    return widget


class MainWindow(W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Fermi Softness Studio {__version__}")
        self.resize(1380, 920)
        self.field = self.charge = self.worker = None
        self.scene = Scene()
        self._drawn = False
        self._bader_source = None
        self._bader_directory = None
        self._exporting_animation = False
        self._animation_cancel_requested = False
        self.rotation_timer = QtCore.QTimer(self)
        self.rotation_timer.setInterval(33)
        self.rotation_timer.timeout.connect(self.rotate_step)
        self.rotation_clock = QtCore.QElapsedTimer()
        root = W.QSplitter()
        self.setCentralWidget(root)
        panel = W.QWidget()
        panel.setMinimumWidth(355)
        panel.setMaximumWidth(455)
        layout = W.QVBoxLayout(panel)
        title = W.QLabel("Fermi Softness")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = W.QLabel(f"SURFACE REACTIVITY STUDIO  ·  {__version__}")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        self.tabs = W.QTabWidget()
        self.tabs.setElideMode(QtCore.Qt.ElideNone)
        layout.addWidget(self.tabs)
        self._data_tab()
        self._scene_tab()
        self._style_tab()
        self._bader_tab()
        self._export_tab()
        self.summary = W.QLabel(
            "Open a field or try the synthetic demo.\nDrag to rotate · wheel to zoom."
        )
        self.summary.setWordWrap(True)
        self.summary.setObjectName("summary")
        layout.addWidget(self.summary)
        root.addWidget(panel)
        viewer = W.QWidget()
        vl = W.QVBoxLayout(viewer)
        vl.setContentsMargins(0, 0, 0, 0)
        toolbar = W.QHBoxLayout()
        for text, method in (
            ("Top", "view_xy"),
            ("Side", "view_xz"),
            ("Oblique", "view_isometric"),
        ):
            button = W.QPushButton(text)
            button.clicked.connect(lambda checked=False, m=method: self.orient(m))
            toolbar.addWidget(button)
        self.rotate_button = W.QPushButton("Auto rotate")
        self.rotate_button.setCheckable(True)
        self.rotate_button.setEnabled(False)
        self.rotate_button.toggled.connect(self.toggle_rotation)
        toolbar.addWidget(self.rotate_button)
        self.rotation_axis_choice = W.QComboBox()
        for label, axis in (("Surface normal", "normal"), ("View up", "view"),
                            ("X", "x"), ("Y", "y"), ("Z", "z")):
            self.rotation_axis_choice.addItem(label, axis)
        self.rotation_axis_choice.setToolTip("Rotation axis; Surface normal is normal to the a–b plane.")
        toolbar.addWidget(self.rotation_axis_choice)
        self.rotation_speed = _number(30, 1, 180, 1, 5)
        self.rotation_speed.setSuffix(" °/s")
        self.rotation_speed.setMaximumWidth(105)
        self.rotation_speed.setToolTip("Preview rotation speed")
        toolbar.addWidget(self.rotation_speed)
        toolbar.addStretch()
        self.view_label = W.QLabel("Interactive 3D")
        toolbar.addWidget(self.view_label)
        vl.addLayout(toolbar)
        self.plotter = QtInteractor(viewer)
        self.plotter.iren.add_observer("StartInteractionEvent", lambda *_: self.stop_rotation())
        self.plotter.set_background("#f3f6fa")
        self.plotter.add_text(
            "Fermi Softness Studio\n\nOpen a result or load the demo",
            font_size=18,
            color="#6b7b91",
            position="upper_left",
        )
        vl.addWidget(self.plotter.interactor)
        root.addWidget(viewer)
        root.setSizes([380, 1000])
        self.statusBar().showMessage("Ready · Calculations and visualization stay on this computer")
        self.setStyleSheet("""
            QMainWindow, QWidget { font-family: 'Arial'; font-size: 13px; color: #24344b;
                                  background: #f8fafc; }
            QMainWindow { background: #f8fafc; }
            QLabel#title { font-size: 29px; font-weight: bold; color: #293854; margin: 12px 4px 0; }
            QLabel#subtitle { font-size: 10px; color: #64758c; letter-spacing: 1px; margin: 4px 4px 14px; }
            QLabel#summary { background: #e9edf5; padding: 12px; border-radius: 7px; font-size: 12px; }
            QPushButton { background: #edf1f7; border: 1px solid #ccd5e3; border-radius: 5px;
                          padding: 7px 10px; min-height: 18px; }
            QPushButton:hover { background: #dee6f4; }
            QPushButton#primary { background: #5555b6; color: white; border: 0; font-weight: bold; }
            QPushButton#primary:disabled { background: #9b9fc1; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: white; border: 1px solid #cbd4e1;
                          border-radius: 4px; padding: 5px; min-height: 18px; }
            QGroupBox { border: 1px solid #d7deea; border-radius: 6px; margin-top: 15px; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QTabWidget::pane { border: 0; }
            QTabBar::tab { padding: 10px 12px; background: #edf1f7; }
            QTabBar::tab:selected { color: #514ba3; font-weight: bold; background: white; }
            QProgressBar { border: 0; background: #e6eaf1; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: #7775cd; border-radius: 4px; }
        """)
        shortcut = QtGui.QShortcut(QtGui.QKeySequence.Open, self)
        shortcut.activated.connect(self.open_field)

    def _tab(self, name):
        widget = W.QWidget()
        layout = W.QVBoxLayout(widget)
        layout.setContentsMargins(5, 12, 5, 6)
        scroll = W.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(W.QFrame.NoFrame)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, name)
        return layout

    def _button(self, layout, text, callback, primary=False):
        button = W.QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    def _file_row(self, form, label, existing=True):
        row = W.QWidget()
        layout = W.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        edit = W.QLineEdit()
        edit.setPlaceholderText(label)
        button = W.QPushButton("…")
        button.setMaximumWidth(36)

        def choose():
            if existing:
                selected, _ = W.QFileDialog.getOpenFileName(self, label)
            else:
                selected = W.QFileDialog.getExistingDirectory(self, label)
            if selected:
                edit.setText(selected)
                if label == "WAVECAR":
                    sibling = Path(selected).parent / "vasprun.xml"
                    if sibling.exists():
                        self.xml_path.setText(str(sibling))

        button.clicked.connect(choose)
        layout.addWidget(edit)
        layout.addWidget(button)
        form.addRow(label, row)
        return edit

    def _data_tab(self):
        layout = self._tab("Data")
        self._button(layout, "Open softness field…", self.open_field)
        self._button(layout, "Load charge density…", self.open_charge)
        from .demos import catalog

        self.demo_choice = W.QComboBox()
        for entry in catalog():
            self.demo_choice.addItem(entry["title"], entry["id"])
        layout.addWidget(self.demo_choice)
        self.demo_description = W.QLabel()
        self.demo_description.setWordWrap(True)

        def describe_demo():
            self.demo_description.setText(catalog()[self.demo_choice.currentIndex()]["description"])

        self.demo_choice.currentIndexChanged.connect(describe_demo)
        describe_demo()
        layout.addWidget(self.demo_description)
        self._button(layout, "Open selected demo", self.load_selected_demo)
        group = W.QGroupBox("Calculate from VASP")
        form = W.QFormLayout(group)
        form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        self.wave_path = self._file_row(form, "WAVECAR")
        self.xml_path = self._file_row(form, "vasprun.xml")
        self.kt = _number(0.4, 0.0001, 100, 4, 0.05)
        self.threshold = _number(0.001, 1e-8, 100, 8, 0.0001)
        self.grid_text = W.QLineEdit()
        self.grid_text.setPlaceholderText("Automatic, or NX NY NZ")
        form.addRow("kT / eV", self.kt)
        form.addRow("Cutoff / eV⁻¹", self.threshold)
        form.addRow("FFT grid", self.grid_text)
        layout.addWidget(group)
        note = W.QLabel(
            "Use matching static-run files with ISYM = −1 (or 0 for scalar states). "
            "Include empty bands above the Fermi level. The calculated field uses "
            "smooth PAW wavefunctions."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.compute_button = self._button(
            layout, "Calculate softness", self.start_calculation, True
        )
        self.native_mode = W.QComboBox()
        self.native_mode.addItems(
            ["Native: state-resolved PARCHG", "Native: compact fixed orbitals (nonmagnetic)"]
        )
        layout.addWidget(self.native_mode)
        self._button(layout, "Prepare native VASP densities…", self.prepare_native)
        self._button(layout, "Combine native densities…", self.combine_native)
        self.progress = W.QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.cancel_button = self._button(layout, "Cancel calculation", self.cancel_calculation)
        self.cancel_button.setEnabled(False)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        self.log.setPlaceholderText("Calculation messages and validation results")
        layout.addWidget(self.log)
        layout.addStretch()

    def _scene_tab(self):
        layout = self._tab("Scene")
        form = W.QFormLayout()
        form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        self.mode = W.QComboBox()
        self.mode.addItems(
            ["Softness isosurface", "Charge surface · softness colors", "Planar section"]
        )
        self.iso = _number(0.025, 0, 1e5, 6)
        self.fraction = _number(0.95, 0.01, 0.9999, 4, 0.01)
        self.charge_iso = W.QLineEdit()
        self.charge_iso.setPlaceholderText("Auto from enclosed charge")
        self.cmap = W.QComboBox()
        self.cmap.addItems(
            [
                "viridis",
                "plasma",
                "inferno",
                "cividis",
                "turbo",
                "coolwarm",
                "jet",
                "Spectral",
                "Greys",
            ]
        )
        self.cmin = _number(0, -1e5, 1e5, 6)
        self.cmax = _number(0.08, 0, 1e5, 6)
        self.opacity = _number(1, 0, 1, 2, 0.05)
        self.atom_scale = _number(0.36, 0.02, 2, 2, 0.02)
        self.repeats = W.QLineEdit("1 1 1")
        self.display_offset = W.QLineEdit("0 0 0")
        self.stride = W.QSpinBox()
        self.stride.setRange(1, 32)
        self.axis = W.QComboBox()
        self.axis.addItems(["a", "b", "c"])
        self.axis.setCurrentIndex(2)
        self.plane = _number(0.55, 0, 1, 3, 0.01)
        for label, widget in [
            ("Display", self.mode),
            ("Softness level", self.iso),
            ("Enclosed charge", self.fraction),
            ("Charge level", self.charge_iso),
            ("Opacity", self.opacity),
            ("Atom marker size", self.atom_scale),
            ("Supercell a b c", self.repeats),
            ("Cell view origin", self.display_offset),
            ("Display stride", self.stride),
            ("Plane normal", self.axis),
            ("Plane fraction", self.plane),
        ]:
            form.addRow(label, widget)
        layout.addLayout(form)
        self.atoms = W.QCheckBox("Show atoms")
        self.auto_color = W.QCheckBox("Fit color range to visible surface")
        self.edges = W.QCheckBox("Show unit-cell edges")
        self.ortho = W.QCheckBox("Orthographic projection")
        for box in (self.auto_color, self.atoms, self.edges, self.ortho):
            box.setChecked(True)
            layout.addWidget(box)
        self._button(layout, "Apply view", self.apply_view, True)
        self._button(layout, "Save view…", self.save_scene)
        self._button(layout, "Load view…", self.load_scene)
        label = W.QLabel(
            "Softness levels use the units selected in Style.\nCharge level: Å⁻³. "
            "Display stride affects the view only."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()

    def _style_tab(self):
        layout = self._tab("Style")
        form = W.QFormLayout()
        form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        self.style_preset = W.QComboBox()
        self.style_preset.addItems(
            ["Scientific light", "Paper 2016", "Presentation dark", "Grayscale print"]
        )
        self.legend_style = W.QComboBox()
        for label, value in (
            ("Horizontal", "horizontal"),
            ("Vertical", "vertical"),
            ("Compact", "compact"),
            ("Paper endpoints", "paper"),
            ("Hidden", "hidden"),
        ):
            self.legend_style.addItem(label, value)
        self.units = W.QComboBox()
        self.units.addItems(["eV", "keV"])
        self._display_factor = 1.0
        self.units.currentTextChanged.connect(self.change_display_units)
        self.bg = W.QComboBox()
        for name, color in (
            ("Light gray", "#f3f6fa"),
            ("White", "#ffffff"),
            ("Black", "#000000"),
            ("Navy", "#101b30"),
        ):
            self.bg.addItem(name, color)
        self.legend_font = W.QComboBox()
        self.legend_font.addItems(["arial", "times", "courier"])
        self.legend_size = W.QSpinBox()
        self.legend_size.setRange(8, 32)
        self.legend_size.setValue(14)
        self.legend_labels = W.QSpinBox()
        self.legend_labels.setRange(2, 12)
        self.legend_labels.setValue(5)
        self.legend_format = W.QComboBox()
        self.legend_format.addItems(["%.3f", "%.2f", "%.4f", "%.2e", "%.3g"])
        self.reverse = W.QCheckBox("Reverse color map")
        for label, widget in (
            ("Preset", self.style_preset),
            ("Color map", self.cmap),
            ("Colorbar", self.legend_style),
            ("Display units", self.units),
            ("Color minimum", self.cmin),
            ("Color maximum", self.cmax),
            ("Background", self.bg),
            ("Font", self.legend_font),
            ("Font size", self.legend_size),
            ("Tick labels", self.legend_labels),
            ("Number format", self.legend_format),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)
        layout.addWidget(self.reverse)
        self._button(layout, "Apply style", self.apply_view, True)
        self.style_preset.currentIndexChanged.connect(self.apply_style_preset)
        note = W.QLabel(
            "Changing eV to keV multiplies display values by 1000. Numerical data remain unchanged. "
            "For comparisons, turn off automatic scaling in Scene and keep one common range."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def change_display_units(self, units):
        factor = 1000.0 if units == "keV" else 1.0
        for widget in (self.iso, self.cmin, self.cmax):
            widget.setValue(widget.value() * factor / self._display_factor)
        self._display_factor = factor

    def apply_style_preset(self, index):
        settings = [
            ("viridis", "horizontal", "#f3f6fa", "arial", "eV"),
            ("jet", "paper", "#000000", "arial", "keV"),
            ("inferno", "vertical", "#101b30", "arial", "eV"),
            ("Greys", "compact", "#ffffff", "times", "eV"),
        ]
        cmap, style, bg, font, units = settings[index]
        self.cmap.setCurrentText(cmap)
        self.legend_style.setCurrentIndex(self.legend_style.findData(style))
        self.bg.setCurrentIndex(self.bg.findData(bg))
        self.legend_font.setCurrentText(font)
        self.units.setCurrentText(units)
        self.legend_format.setCurrentText("%.3g" if units == "keV" else "%.3f")
        self.legend_labels.setValue(2 if style == "paper" else 5)
        self.reverse.setChecked(False)
        if self.field is not None:
            self.apply_view()

    def _export_tab(self):
        layout = self._tab("Export")
        form = W.QFormLayout()
        self.width = W.QSpinBox()
        self.height = W.QSpinBox()
        for box, value in ((self.width, 3600), (self.height, 2600)):
            box.setRange(128, 16384)
            box.setValue(value)
        self.dpi = W.QSpinBox()
        self.dpi.setRange(72, 2400)
        self.dpi.setValue(300)
        form.addRow("Width / pixels", self.width)
        form.addRow("Height / pixels", self.height)
        form.addRow("DPI", self.dpi)
        layout.addLayout(form)
        self.transparent = W.QCheckBox("Transparent background")
        layout.addWidget(self.transparent)
        self._button(layout, "Export PNG or TIFF…", self.export_picture, True)
        self._button(layout, "Export animation (MP4 / GIF)…", self.export_movie, True)
        self._button(layout, "Save field (.npz)…", self.save_field)
        self._button(layout, "Export Cube for VMD / VESTA…", self.export_cube)
        self._button(layout, "Show numerical metadata", self.show_metadata)
        label = W.QLabel(
            "Images use the current camera and an explicit pixel size. "
            "The view settings are saved beside each exported image. "
            "Keep the native field for quantitative analysis."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        animation_group = W.QGroupBox("Rotation animation")
        animation_form = W.QFormLayout(animation_group)
        self.animation_width = W.QSpinBox()
        self.animation_height = W.QSpinBox()
        for box, value in ((self.animation_width, 1920), (self.animation_height, 1080)):
            box.setRange(128, 4096)
            box.setSingleStep(2)
            box.setValue(value)
        self.animation_seconds = _number(12, 0.25, 120, 2, 1)
        self.animation_fps = W.QSpinBox()
        self.animation_fps.setRange(1, 60)
        self.animation_fps.setValue(30)
        self.animation_turns = W.QSpinBox()
        self.animation_turns.setRange(1, 10)
        self.animation_turns.setValue(1)
        self.animation_reverse = W.QCheckBox("Reverse direction")
        self.animation_reverse.setToolTip("Applies to the preview and exported animation")
        self.animation_fit = W.QCheckBox("Fit full rotation (avoid clipping)")
        self.animation_fit.setChecked(True)
        for name, widget in (("Width / pixels", self.animation_width),
                             ("Height / pixels", self.animation_height),
                             ("Duration / seconds", self.animation_seconds),
                             ("Frames / second", self.animation_fps),
                             ("Full rotations", self.animation_turns)):
            animation_form.addRow(name, widget)
        animation_form.addRow(self.animation_reverse)
        animation_form.addRow(self.animation_fit)
        layout.addWidget(animation_group)
        animation_note = W.QLabel(
            "Export starts from the current view and uses the rotation axis above. "
            "Duration and full rotations set the movie's speed. MP4 preserves smooth colors; "
            "GIF loops continuously. Animation uses the scene background."
        )
        animation_note.setWordWrap(True)
        layout.addWidget(animation_note)
        layout.addStretch()

    def _bader_tab(self):
        layout = self._tab("Bader")
        text = W.QLabel(
            "Partition space using charge-density zero-flux surfaces, then integrate softness in each atom's basin. "
            "For VASP, use AECCAR0 + AECCAR2 as the reference."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        form = W.QFormLayout()
        self.bader_ref1 = self._file_row(form, "Reference / AECCAR0")
        self.bader_ref2 = self._file_row(form, "AECCAR2 (optional)")
        self.bader_charge = self._file_row(form, "CHGCAR (optional)")
        self.bader_program = self._file_row(form, "Bader executable")
        try:
            from .bader import resolve_executable

            self.bader_program.setText(str(resolve_executable()))
        except ValueError:
            pass
        self.bader_output = self._file_row(form, "Output parent", existing=False)
        self.bader_atoms = W.QLineEdit()
        self.bader_atoms.setPlaceholderText("Optional: 1 5 9 13")
        form.addRow("Surface atom IDs", self.bader_atoms)
        layout.addLayout(form)
        self.bader_button = self._button(
            layout, "Calculate atomic softness", self.start_bader, True
        )
        self.bader_table = W.QTableWidget(0, 6)
        self.bader_table.setHorizontalHeaderLabels(
            ["Atom", "Element", "z / Å", "sF / eV⁻¹", "Volume / Å³", "Valence e⁻"]
        )
        self.bader_table.setSelectionBehavior(W.QAbstractItemView.SelectRows)
        self.bader_table.setSelectionMode(W.QAbstractItemView.ExtendedSelection)
        self.bader_table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.bader_table.setMinimumHeight(200)
        layout.addWidget(self.bader_table)
        self._button(layout, "View selected atom basins", self.view_bader_atoms)
        self._button(layout, "View recorded surface layer", self.view_bader_surface)
        self._button(layout, "Restore full field", self.restore_bader_field)
        self.bader_status = W.QLabel("No Bader partition loaded. Atom IDs are one based.")
        self.bader_status.setWordWrap(True)
        layout.addWidget(self.bader_status)
        layout.addStretch()

    def start_bader(self):
        if self.worker is not None and self.worker.isRunning():
            return
        try:
            self.require_field()
            references = [self.bader_ref1.text().strip()]
            if self.bader_ref2.text().strip():
                references.append(self.bader_ref2.text().strip())
            parent = self.bader_output.text().strip()
            if not parent:
                raise ValueError("Choose a parent folder for the Bader result.")
            atoms = [int(x) for x in self.bader_atoms.text().replace(",", " ").split()]
            self._bader_directory = Path(parent) / "bader-result"
            options = dict(
                field=self._bader_source or self.field,
                references=references,
                output=self._bader_directory,
                charge=self.bader_charge.text().strip() or None,
                executable=self.bader_program.text().strip() or None,
                surface_atoms=atoms,
            )
            self.compute_button.setEnabled(False)
            self.bader_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress.setRange(0, 0)
            self.worker = CalculationWorker(options, self, operation="bader")
            self.worker.progress.connect(self.on_progress)
            self.worker.result.connect(self.bader_complete)
            self.worker.failed.connect(self.error)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()
        except Exception as exc:
            self.error(str(exc))

    def bader_complete(self, report, source):
        self._bader_source = source
        self._bader_report = report
        self.bader_table.setRowCount(len(report["atoms"]))
        for row, atom in enumerate(report["atoms"]):
            values = [
                str(atom["atom"]),
                atom["element"],
                f"{atom['z_A']:.4f}",
                f"{atom['softness_eV_inverse']:.7g}",
                f"{atom['volume_A3']:.5g}",
                f"{atom['valence_electrons']:.5g}" if "valence_electrons" in atom else "—",
            ]
            for column, value in enumerate(values):
                self.bader_table.setItem(row, column, W.QTableWidgetItem(value))
        self.bader_table.resizeColumnsToContents()
        text = (
            f"Atomic sum: {report['atomic_sum_eV_inverse']:.8g} eV⁻¹\n"
            f"Conservation error: {report['conservation_error_eV_inverse']:.2e} eV⁻¹\n"
            f"Saved report, CSV and basins in {self._bader_directory}"
        )
        if report["surface_softness_eV_inverse"] is not None:
            text += f"\nSelected surface: {report['surface_softness_eV_inverse']:.8g} eV⁻¹"
        self.bader_status.setText(text)

    def view_bader_atoms(self):
        try:
            from .bader import select_basins

            if self._bader_source is None:
                raise ValueError("Calculate or load a Bader partition first.")
            ids = [
                int(self.bader_table.item(index.row(), 0).text())
                for index in self.bader_table.selectionModel().selectedRows()
            ]
            selected = select_basins(self._bader_source, self._bader_directory / "basins.npz", ids)
            self.set_field(selected, self.charge, reset_bader=False)
        except Exception as exc:
            self.error(str(exc))

    def view_bader_surface(self):
        if self._bader_source is None or not self._bader_report.get("surface_atom_ids"):
            return self.error(
                "No surface atom IDs were recorded. Select the desired rows in the table."
            )
        ids = set(self._bader_report["surface_atom_ids"])
        self.bader_table.clearSelection()
        selection = self.bader_table.selectionModel()
        for row in range(self.bader_table.rowCount()):
            if int(self.bader_table.item(row, 0).text()) in ids:
                selection.select(
                    self.bader_table.model().index(row, 0),
                    QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows,
                )
        self.view_bader_atoms()

    def restore_bader_field(self):
        if self._bader_source is not None:
            self.set_field(self._bader_source, self.charge, reset_bader=False)

    def error(self, text):
        self.log.appendPlainText(text)
        self.statusBar().showMessage(text)
        W.QMessageBox.warning(self, "Fermi Softness", text)

    def require_field(self):
        if self.field is None:
            raise ValueError("Open or calculate a softness field first.")

    def set_field(self, field, charge=None, reset_bader=True, draw=True):
        self.stop_rotation()
        self.rotate_button.setEnabled(True)
        keep_range = self.field is not None and not self.auto_color.isChecked()
        self.field, self.charge = field, charge
        if reset_bader:
            self._bader_source = None
            self._bader_directory = None
            self.bader_table.setRowCount(0)
            self.bader_status.setText("No Bader partition loaded. Atom IDs are one based.")
        if reset_bader:
            self._drawn = False
        maximum = float(np.max(field.values))
        if reset_bader:
            self.iso.setValue(maximum * 0.4 * self._display_factor)
            self.scene.camera = None
            self.mode.setCurrentIndex(1 if charge is not None else 0)
        if not keep_range:
            self.cmin.setValue(float(np.min(field.values)) * self._display_factor)
            self.cmax.setValue(maximum * self._display_factor)
        label = (
            "Synthetic demo · not a DFT prediction"
            if field.metadata.get("synthetic")
            else field.metadata.get("representation", "Imported softness field")
        )
        if field.metadata.get("diagnostic_only"):
            label += " · DIAGNOSTIC ONLY"
        self.summary.setText(
            f"{label}\nGrid: {' × '.join(map(str, field.values.shape))}\n"
            f"Range: {field.values.min():.5g} – {maximum:.5g} eV⁻¹ Å⁻³\n"
            f"Cell integral: {field.integral:.7g} eV⁻¹"
        )
        if draw:
            self.apply_view()

    def open_field(self):
        path, _ = W.QFileDialog.getOpenFileName(
            self, "Open softness field", "", "Fields (*.npz *.fsz *.cube *.cub)"
        )
        if path:
            try:
                self.set_field(read_field(path))
            except Exception as exc:
                self.error(str(exc))

    def open_charge(self):
        path, _ = W.QFileDialog.getOpenFileName(self, "Load charge density (CHGCAR or Cube)")
        if path:
            try:
                self.charge = read_field(path, density=True)
                self.mode.setCurrentIndex(1)
                self.apply_view()
            except Exception as exc:
                self.error(str(exc))

    def load_demo(self):
        from .demo import demo_fields

        self.set_field(*demo_fields())
        self.tabs.setCurrentIndex(1)

    def load_selected_demo(self):
        from .demos import load_demo

        try:
            field, charge, scene, root = load_demo(self.demo_choice.currentData())
            self.set_field(field, charge, draw=False)
            self.apply_scene(scene)
            if root is not None and root.joinpath("report.json").is_file():
                self._bader_directory = Path(str(root))
                from .field import Field

                source = (
                    Field.load(root.joinpath("softness.npz"))
                    if field.metadata.get("bader_atom_ids")
                    else field
                )
                self.bader_complete(json.loads(root.joinpath("report.json").read_text()), source)
            self.tabs.setCurrentIndex(1)
        except Exception as exc:
            self.error(str(exc))

    def controls_scene(self):
        return Scene(
            mode=("softness", "charge", "slice")[self.mode.currentIndex()],
            isovalue=self.iso.value() / self._display_factor,
            charge_fraction=self.fraction.value(),
            charge_isovalue=float(self.charge_iso.text())
            if self.charge_iso.text().strip()
            else None,
            cmap=self.cmap.currentText(),
            auto_color=self.auto_color.isChecked(),
            color_min=self.cmin.value() / self._display_factor,
            color_max=self.cmax.value() / self._display_factor,
            colorbar_style=self.legend_style.currentData(),
            colorbar_labels=self.legend_labels.value(),
            colorbar_format=self.legend_format.currentText(),
            colorbar_font=self.legend_font.currentText(),
            colorbar_font_size=self.legend_size.value(),
            display_units=self.units.currentText(),
            reverse_cmap=self.reverse.isChecked(),
            background=self.bg.currentData(),
            opacity=self.opacity.value(),
            atom_scale=self.atom_scale.value(),
            repeats=tuple(map(int, self.repeats.text().split())),
            display_offset=tuple(map(float, self.display_offset.text().split())),
            atoms=self.atoms.isChecked(),
            cell_edges=self.edges.isChecked(),
            orthographic=self.ortho.isChecked(),
            plane_axis=self.axis.currentIndex(),
            plane_fraction=self.plane.value(),
            display_stride=self.stride.value(),
        )

    def apply_view(self):
        try:
            self.require_field()
            scene = self.controls_scene()
            draw_scene(self.plotter, self.field, scene, self.charge, preserve_camera=self._drawn)
            self.scene, self._drawn = scene, True
            self.cmin.setValue(scene.color_min * self._display_factor)
            self.cmax.setValue(scene.color_max * self._display_factor)
            self.view_label.setText(self.mode.currentText())
            self.statusBar().showMessage(
                "View updated · Drag to rotate, shift-drag to pan, wheel to zoom"
            )
        except Exception as exc:
            self.error(str(exc))

    def orient(self, method):
        self.stop_rotation()
        getattr(self.plotter, method)()
        self.plotter.render()

    def stop_rotation(self):
        self.rotation_timer.stop()
        self.rotate_button.setChecked(False)
        self.rotate_button.setText("Auto rotate")

    def toggle_rotation(self, enabled):
        if not enabled:
            self.rotation_timer.stop()
            self.rotate_button.setText("Auto rotate")
            return
        if self.field is None or self._exporting_animation:
            self.stop_rotation()
            return
        if self.animation_fit.isChecked():
            try:
                camera = fit_rotation_camera(
                    capture_camera(self.plotter), self.plotter.bounds, *self.plotter.window_size,
                    self.scene.orthographic,
                )
                restore_camera(self.plotter, camera)
            except Exception as exc:
                self.stop_rotation()
                self.error(str(exc))
                return
        self.rotation_clock.start()
        self.rotation_timer.start()
        self.rotate_button.setText("Pause rotation")

    def rotate_step(self):
        if self.field is None or self._exporting_animation:
            self.stop_rotation()
            return
        try:
            seconds = min(self.rotation_clock.restart() / 1000, 0.25)
            camera = capture_camera(self.plotter)
            axis = rotation_axis(self.rotation_axis_choice.currentData(), self.field.cell, camera)
            direction = -1 if self.animation_reverse.isChecked() else 1
            restore_camera(self.plotter, orbit_camera(
                camera, axis, direction * self.rotation_speed.value() * seconds
            ))
            self.plotter.reset_camera_clipping_range()
            self.plotter.render()
        except Exception as exc:
            self.stop_rotation()
            self.error(str(exc))

    def save_scene(self):
        self.stop_rotation()
        if self.field is None:
            return self.error("Load a field first.")
        path, _ = W.QFileDialog.getSaveFileName(self, "Save view", "view.json", "JSON (*.json)")
        if path:
            self.scene.camera = capture_camera(self.plotter)
            self.scene.save(path)

    def load_scene(self):
        path, _ = W.QFileDialog.getOpenFileName(self, "Load view", "", "JSON (*.json)")
        if not path:
            return
        self.load_scene_path(path)

    def load_scene_path(self, path):
        try:
            self.apply_scene(Scene.load(path))
        except Exception as exc:
            self.error(str(exc))

    def apply_scene(self, scene):
        self.stop_rotation()
        try:
            self.require_field()
            draw_scene(self.plotter, self.field, scene, self.charge)
            self.scene, self._drawn = scene, True
            self.mode.setCurrentIndex(("softness", "charge", "slice").index(scene.mode))
            self.units.setCurrentText(scene.display_units)
            self.iso.setValue(scene.isovalue * self._display_factor)
            self.fraction.setValue(scene.charge_fraction)
            self.charge_iso.setText(
                "" if scene.charge_isovalue is None else str(scene.charge_isovalue)
            )
            self.cmap.setCurrentText(scene.cmap)
            self.cmin.setValue(scene.color_min * self._display_factor)
            self.cmax.setValue(scene.color_max * self._display_factor)
            self.legend_style.setCurrentIndex(self.legend_style.findData(scene.colorbar_style))
            self.legend_labels.setValue(scene.colorbar_labels)
            self.legend_format.setCurrentText(scene.colorbar_format)
            self.legend_font.setCurrentText(scene.colorbar_font)
            self.legend_size.setValue(scene.colorbar_font_size)
            self.reverse.setChecked(scene.reverse_cmap)
            if self.bg.findData(scene.background) < 0:
                self.bg.addItem(scene.background, scene.background)
            self.bg.setCurrentIndex(self.bg.findData(scene.background))
            self.opacity.setValue(scene.opacity)
            self.atom_scale.setValue(scene.atom_scale)
            self.repeats.setText(" ".join(map(str, scene.repeats)))
            self.display_offset.setText(" ".join(map(str, scene.display_offset)))
            self.stride.setValue(scene.display_stride)
            self.axis.setCurrentIndex(scene.plane_axis)
            self.plane.setValue(scene.plane_fraction)
            self.atoms.setChecked(scene.atoms)
            self.auto_color.setChecked(scene.auto_color)
            self.edges.setChecked(scene.cell_edges)
            self.ortho.setChecked(scene.orthographic)
        except Exception as exc:
            self.error(str(exc))

    def export_picture(self):
        self.stop_rotation()
        if self.field is None:
            return self.error("Load a field first.")
        path, _ = W.QFileDialog.getSaveFileName(
            self, "Export figure", "softness.png", "Images (*.png *.tif *.tiff)"
        )
        if path:
            try:
                export_image(
                    self.plotter,
                    path,
                    self.width.value(),
                    self.height.value(),
                    self.dpi.value(),
                    self.transparent.isChecked(),
                )
                self.scene.camera = capture_camera(self.plotter)
                self.scene.save(path + ".scene.json")
                self.statusBar().showMessage(
                    f"Exported {self.width.value()} × {self.height.value()} pixels: {path}"
                )
            except Exception as exc:
                self.error(str(exc))

    def export_movie(self):
        if self.field is None:
            return self.error("Load a field first.")
        if self.worker is not None and self.worker.isRunning():
            return self.error("Wait for the current calculation to finish before exporting animation.")
        was_rotating = self.rotation_timer.isActive()
        self.stop_rotation()
        path, selected_filter = W.QFileDialog.getSaveFileName(
            self, "Export rotation animation", "softness.mp4", "MP4 video (*.mp4);;GIF animation (*.gif)"
        )
        if not path:
            if was_rotating:
                self.rotate_button.setChecked(True)
            return
        if not Path(path).suffix:
            path += ".gif" if selected_filter.startswith("GIF") else ".mp4"
        self.export_movie_to(path, resume_rotation=was_rotating)

    def export_movie_to(self, path, *, resume_rotation=False):
        """Keep VTK rendering on the GUI thread while allowing modal cancellation."""
        self.stop_rotation()
        self._exporting_animation = True
        self._animation_cancel_requested = False
        dialog = W.QProgressDialog("Preparing animation…", "Cancel", 0, 1000, self)
        dialog.setWindowTitle("Export animation")
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.show()

        def progress(done, total, label):
            dialog.setLabelText(f"{label} · {done}/{total} frames")
            dialog.setValue(round(950 * done / total))

        try:
            metadata = export_animation(
                self.plotter, path, self.scene, self.field.cell,
                width=self.animation_width.value(), height=self.animation_height.value(),
                fps=self.animation_fps.value(), seconds=self.animation_seconds.value(),
                turns=self.animation_turns.value(), axis=self.rotation_axis_choice.currentData(),
                reverse=self.animation_reverse.isChecked(), progress=progress,
                fit=self.animation_fit.isChecked(),
                cancelled=lambda: dialog.wasCanceled() or self._animation_cancel_requested,
                pulse=W.QApplication.processEvents,
            )
            self.statusBar().showMessage(
                f"Exported {metadata['frames']} frames at {metadata['fps']} fps: {path}"
            )
        except ExportCancelled:
            self.statusBar().showMessage("Animation export cancelled; the original view is restored.")
        except Exception as exc:
            self.error(str(exc))
        finally:
            dialog.close()
            self._exporting_animation = False
            if resume_rotation:
                self.rotate_button.setChecked(True)

    def save_field(self):
        if self.field is None:
            return self.error("Load a field first.")
        path, _ = W.QFileDialog.getSaveFileName(
            self, "Save field", "softness.npz", "Native field (*.npz)"
        )
        if path:
            try:
                self.field.save(path)
            except Exception as exc:
                self.error(str(exc))

    def export_cube(self):
        if self.field is None:
            return self.error("Load a field first.")
        path, _ = W.QFileDialog.getSaveFileName(
            self, "Export Cube", "softness.cube", "Cube (*.cube)"
        )
        if path:
            try:
                write_field_cube(self.field, path)
            except Exception as exc:
                self.error(str(exc))

    def show_metadata(self):
        if self.field is None:
            return self.error("Load a field first.")
        dialog = W.QDialog(self)
        dialog.setWindowTitle("Numerical provenance")
        dialog.resize(700, 600)
        layout = W.QVBoxLayout(dialog)
        text = W.QPlainTextEdit(json.dumps(self.field.metadata, indent=2))
        text.setReadOnly(True)
        layout.addWidget(text)
        dialog.exec()

    def start_calculation(self):
        if self.worker is not None and self.worker.isRunning():
            return
        try:
            grid = (
                tuple(map(int, self.grid_text.text().split()))
                if self.grid_text.text().strip()
                else None
            )
            options = {
                "wavecar": self.wave_path.text(),
                "vasprun": self.xml_path.text(),
                "kt": self.kt.value(),
                "threshold": self.threshold.value(),
                "grid": grid,
            }
            if not all(Path(options[k]).is_file() for k in ("wavecar", "vasprun")):
                raise ValueError("Select existing WAVECAR and vasprun.xml files.")
            self.compute_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress.setRange(0, 0)
            self.log.appendPlainText("Checking input compatibility, bands and FFT grid…")
            self.worker = CalculationWorker(options, self)
            self.worker.progress.connect(self.on_progress)
            self.worker.result.connect(self.on_result)
            self.worker.failed.connect(self.error)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()
        except Exception as exc:
            self.error(str(exc))
            self.on_finished()

    def prepare_native(self):
        if self.worker is not None and self.worker.isRunning():
            return
        directory = W.QFileDialog.getExistingDirectory(self, "Choose parent folder for VASP deck")
        if not directory:
            return
        self._native_output = Path(directory) / "fermi-native-deck"
        options = {
            "wavecar": self.wave_path.text(),
            "vasprun": self.xml_path.text(),
            "output": self._native_output,
            "kt": self.kt.value(),
            "threshold": self.threshold.value(),
        }
        self.compute_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress.setRange(0, 0)
        self.worker = CalculationWorker(
            options,
            self,
            operation="prepare_frozen" if self.native_mode.currentIndex() == 1 else "prepare",
        )
        self.worker.result.connect(self.native_prepared)
        self.worker.failed.connect(self.error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def native_prepared(self, manifest, unused):
        message = (
            f"Prepared native export for {len(manifest['states'])} weighted states in {self._native_output}. "
            "Copy the original WAVECAR and matching POTCAR there, run VASP, then "
            "use Combine native densities to select manifest.json. See RUN.md."
        )
        self.log.appendPlainText(message)
        W.QMessageBox.information(self, "Native density route", message)

    def combine_native(self):
        if self.worker is not None and self.worker.isRunning():
            return
        path, _ = W.QFileDialog.getOpenFileName(
            self, "Select native-density manifest", "", "JSON (*.json)"
        )
        if not path:
            return
        self.compute_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress.setRange(0, 0)
        try:
            schema = json.loads(Path(path).read_text()).get("schema")
        except (ValueError, OSError) as exc:
            self.error(str(exc))
            self.on_finished()
            return
        self.worker = CalculationWorker(
            {"manifest_path": path},
            self,
            operation="frozen" if schema == "fermi-softness-frozen-1" else "parchg",
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.result.connect(self.on_result)
        self.worker.failed.connect(self.error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, done, total):
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        self.statusBar().showMessage(f"Reconstructing wavefunctions · {done} / {total} states")

    def on_result(self, field, channels):
        self.set_field(field)
        self.log.appendPlainText(
            f"Complete. Spectral softness: {field.metadata['spectral_softness_eV_inverse']:.8g} eV⁻¹"
        )
        self.log.appendPlainText(
            "Save the result in the Export tab; the current field is in memory."
        )
        self.tabs.setCurrentIndex(1)

    def on_finished(self):
        self.compute_button.setEnabled(True)
        self.bader_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def cancel_calculation(self):
        if self.worker is not None:
            self.worker.requestInterruption()
            self.statusBar().showMessage("Cancelling after the current wavefunction…")

    def closeEvent(self, event):
        if self._exporting_animation:
            self._animation_cancel_requested = True
            event.ignore()
            return
        self.stop_rotation()
        if self.worker is not None and self.worker.isRunning():
            self.cancel_calculation()
            event.ignore()
            return
        self.plotter.close()
        event.accept()


def launch(field=None, charge=None, demo=False, scene=None, example=None):
    app = W.QApplication.instance() or W.QApplication(sys.argv[:1])
    app.setApplicationName("Fermi Softness Studio")
    app.setApplicationDisplayName("Fermi Softness Studio")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Fermi Softness")
    with as_file(files("fermi_softness").joinpath("assets/fermi-softness.png")) as icon_path:
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    if example:
        index = window.demo_choice.findData(example)
        if index < 0:
            raise ValueError(f"Unknown demo: {example}")
        window.demo_choice.setCurrentIndex(index)
        window.load_selected_demo()
    elif demo:
        window.load_demo()
    elif field:
        window.set_field(read_field(field), read_field(charge, density=True) if charge else None)
    if scene:
        window.load_scene_path(scene)
    return app.exec()
