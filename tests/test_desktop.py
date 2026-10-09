import json
import os
import plistlib
import shlex
import sys
from pathlib import Path

import pytest

from fermi_softness import desktop


@pytest.fixture
def mac_environment(monkeypatch):
    monkeypatch.setattr(desktop.sys, "platform", "darwin")
    monkeypatch.setattr(desktop.importlib.util, "find_spec", lambda name: object())
    # The test needs no external Bader executable or graphical desktop.
    from fermi_softness import bader

    monkeypatch.setattr(bader, "resolve_executable", lambda: Path("/optional/bader"))


def test_bundle_preserves_environment_path_and_updates_owned_app(tmp_path, monkeypatch, mac_environment):
    python = tmp_path / "my environment's $folder" / ("python.exe" if os.name == "nt" else "python")
    python.parent.mkdir()
    # Copying is unnecessary; a symlink demonstrates why resolve() must not be used.
    if os.name == "nt":
        python.write_bytes(Path(sys.executable).read_bytes())
    else:
        python.symlink_to(sys.executable)
    monkeypatch.setattr(desktop.sys, "executable", str(python))
    parent = tmp_path / "Applications folder"
    result = desktop.install_app(parent, register=False)
    app = Path(result["app"])
    config = json.loads((app / "Contents/Resources/launcher.json").read_text())
    assert config["python"] == str(python)
    shell = (app / "Contents/MacOS/FermiSoftness").read_text()
    assert f"python={shlex.quote(str(python))}" in shell
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    assert info["CFBundleIdentifier"] == desktop.BUNDLE_ID
    assert (app / "Contents/Resources" / info["CFBundleIconFile"]).read_bytes().startswith(b"icns")
    if os.name != "nt":
        assert (app / "Contents/MacOS/FermiSoftness").stat().st_mode & 0o100
    # Updating our entry point keeps the existing app intact until replacement.
    assert desktop.install_app(parent, register=False)["app"] == str(app)
    assert not list(parent.glob(".fermi-studio-*"))


def test_installer_does_not_replace_unrelated_app(tmp_path, mac_environment):
    app = tmp_path / f"{desktop.APP_NAME}.app"
    app.mkdir()
    keep = app / "important.txt"
    keep.write_text("unrelated user application")
    with pytest.raises(ValueError, match="unrelated application"):
        desktop.install_app(tmp_path, register=False)
    assert keep.read_text() == "unrelated user application"


def test_installer_reports_platform_and_gui_requirements(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop.sys, "platform", "linux")
    with pytest.raises(ValueError, match="macOS"):
        desktop.install_app(tmp_path, register=False)
    monkeypatch.setattr(desktop.sys, "platform", "darwin")
    monkeypatch.setattr(desktop.importlib.util, "find_spec", lambda name: None)
    with pytest.raises(ValueError, match="gui extra"):
        desktop.install_app(tmp_path, register=False)
    assert not (tmp_path / f"{desktop.APP_NAME}.app").exists()
