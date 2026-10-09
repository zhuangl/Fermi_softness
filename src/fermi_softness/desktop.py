"""A macOS application entry point for an existing Fermi Softness environment."""

import importlib.util
import json
import os
import plistlib
import shlex
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path

from . import __version__

APP_NAME = "Fermi Softness Studio"
BUNDLE_ID = "org.fermisoftness.studio"
SCHEMA = "fermi-softness-macos-launcher-1"
LSREGISTER = Path(
    "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/"
    "Support/lsregister"
)


def default_app_directory():
    """Prefer the usual Applications folder when it is writable by this user."""
    shared = Path("/Applications")
    return shared if os.access(shared, os.W_OK) else Path.home() / "Applications"


def _launcher_script(python):
    # Do not resolve the interpreter symlink: that would bypass the virtualenv.
    return f"""#!/bin/sh
set -eu
python={shlex.quote(str(python))}
resources="$(CDPATH= cd -- "$(dirname "$0")/../Resources" && pwd)"
if [ ! -x "$python" ]; then
  /usr/bin/osascript -e 'on run argv' -e 'display alert "Fermi Softness Studio" message (item 1 of argv) as critical' -e 'end run' "The Python environment is missing. Reinstall the desktop entry with fermi-softness install-app."
  exit 1
fi
log_dir="$HOME/Library/Logs/Fermi Softness Studio"
mkdir -p "$log_dir"
exec "$python" "$resources/launch.py" "$@" >> "$log_dir/studio.log" 2>&1
"""


LAUNCH_PY = '''"""Launch the installed environment without opening a Terminal window."""
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

try:
    resources = Path(__file__).parent
    config = json.loads((resources / "launcher.json").read_text(encoding="utf-8"))
    os.chdir(Path.home())
    if config.get("bader_executable") and Path(config["bader_executable"]).is_file():
        os.environ.setdefault("FERMI_SOFTNESS_BADER", config["bader_executable"])
    from fermi_softness.cli import main
    arguments = [a for a in sys.argv[1:] if not a.startswith("-psn_")]
    code = main(arguments or ["gui", "--example", "pt3y111"])
    if code:
        raise RuntimeError(f"Studio exited with status {code}; see the preceding log messages.")
    raise SystemExit(0)
except Exception:
    traceback.print_exc()
    subprocess.run([
        "/usr/bin/osascript", "-e", "on run argv",
        "-e", 'display alert "Fermi Softness Studio" message (item 1 of argv) as critical',
        "-e", "end run",
        "Could not start Studio. See ~/Library/Logs/Fermi Softness Studio/studio.log. "
        "Check the GUI installation and recreate the app with fermi-softness install-app.",
    ], check=False)
    raise SystemExit(1)
'''


def install_app(directory=None, *, register=True):
    """Install/update our own app bundle; never replace an unrelated application."""
    if sys.platform != "darwin":
        raise ValueError("install-app currently supports macOS. Use fermi-softness gui here.")
    missing = [name for name in ("PySide6", "pyvista", "pyvistaqt")
               if importlib.util.find_spec(name) is None]
    if missing:
        raise ValueError("Install the gui extra first; missing: " + ", ".join(missing))

    parent = Path(directory).expanduser().absolute() if directory else default_app_directory()
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / f"{APP_NAME}.app"
    if target.is_symlink():
        raise ValueError("The destination is a symlink; choose a different Applications directory.")
    if target.exists():
        try:
            info = plistlib.loads((target / "Contents/Info.plist").read_bytes())
            marker = json.loads(
                (target / "Contents/Resources/launcher.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError, plistlib.InvalidFileException) as exc:
            raise ValueError("An unrelated application already exists at the destination.") from exc
        if info.get("CFBundleIdentifier") != BUNDLE_ID or marker.get("schema") != SCHEMA:
            raise ValueError("An unrelated application already exists at the destination.")

    python = Path(os.path.abspath(sys.executable))
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError("The current Python interpreter is not an executable file.")
    config = {"schema": SCHEMA, "python": str(python), "version": __version__}
    try:
        from .bader import resolve_executable

        config["bader_executable"] = str(resolve_executable())
    except ValueError:
        pass
    assets = files("fermi_softness").joinpath("assets")
    with tempfile.TemporaryDirectory(prefix=".fermi-studio-", dir=parent) as temporary:
        stage = Path(temporary) / target.name
        contents = stage / "Contents"
        resources = contents / "Resources"
        executable = contents / "MacOS/FermiSoftness"
        resources.mkdir(parents=True)
        executable.parent.mkdir()
        (resources / "FermiSoftness.icns").write_bytes(
            assets.joinpath("fermi-softness.icns").read_bytes()
        )
        (resources / "launcher.json").write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8"
        )
        (resources / "launch.py").write_text(LAUNCH_PY, encoding="utf-8")
        executable.write_text(_launcher_script(python), encoding="utf-8")
        executable.chmod(0o755)
        (contents / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleIdentifier": BUNDLE_ID,
            "CFBundleExecutable": "FermiSoftness",
            "CFBundlePackageType": "APPL",
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleIconFile": "FermiSoftness.icns",
            "CFBundleShortVersionString": __version__,
            "CFBundleVersion": __version__,
            "NSHighResolutionCapable": True,
        }))
        (contents / "PkgInfo").write_bytes(b"APPL????")
        backup = Path(temporary) / "previous.app"
        if target.exists():
            target.rename(backup)
        try:
            stage.rename(target)
        except OSError:
            if backup.exists():
                backup.rename(target)
            raise

    registered = False
    warning = None
    if register and LSREGISTER.is_file():
        result = subprocess.run(
            [str(LSREGISTER), "-f", str(target)], capture_output=True, text=True, check=False
        )
        registered = result.returncode == 0
        if not registered:
            warning = "The app is installed, but macOS registration failed: " + result.stderr.strip()
    return {"app": str(target), "python": str(python), "registered": registered, "warning": warning}
