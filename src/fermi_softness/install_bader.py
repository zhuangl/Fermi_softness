"""Install a pinned official Bader executable into a user-selected directory."""

import hashlib
import io
import platform
import subprocess
import tarfile
import urllib.request
from pathlib import Path

from .bader import runtime_environment

ASSETS = {
    ("Darwin", "arm64"): (
        "bader_osx_gfortran.tar.gz",
        "a0410efbecb94606ab0e6b433aa5e16db08a2b6e6d854e156de3561974406deb",
    ),
    ("Linux", "x86_64"): (
        "bader_lnx_64.tar.gz",
        "e30ab0c803fc73638c3e9e87321cf03b48b54d639e231e7f181f5ce8491bfa31",
    ),
}


def install(output=".tools/bader"):
    key = (platform.system(), platform.machine())
    if key not in ASSETS:
        raise ValueError(
            "Automatic Bader installation supports macOS arm64 and Linux x86_64. "
            "For this platform, compile the official source and select that executable."
        )
    name, expected = ASSETS[key]
    url = f"https://github.com/henkelmangroup/bader/releases/download/v1.05/{name}"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != expected:
        raise ValueError("Official Bader archive checksum differs from the validated release.")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as source:
        members = [m for m in source.getmembers() if m.isfile() and Path(m.name).name == "bader"]
        if len(members) != 1 or members[0].size > 50_000_000:
            raise ValueError("Unexpected Bader archive contents.")
        binary = source.extractfile(members[0]).read()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    executable = output / "bader"
    if executable.exists() and executable.read_bytes() != binary:
        raise ValueError("A different executable already exists. Choose another output directory.")
    executable.write_bytes(binary)
    executable.chmod(0o755)
    check = subprocess.run(
        [str(executable.resolve()), "-h"],
        capture_output=True,
        text=True,
        env=runtime_environment(),
        timeout=10,
    )
    if check.returncode != 0 or "BADER" not in check.stdout:
        raise ValueError(
            f"Bader could not start. Install its compiler runtime. {check.stderr[:300]}"
        )
    return executable.resolve()
