"""Fetch pinned public VASP fixtures; no VASP binaries or POTCARs are downloaded."""

import hashlib
import json
import urllib.request
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "public-fixtures.json").read_text())
    target = root / "data"
    target.mkdir(exist_ok=True)
    for entry in manifest["files"]:
        path = target / entry["name"]
        if path.exists():
            content = path.read_bytes()
        else:
            with urllib.request.urlopen(entry["url"], timeout=60) as source:
                content = source.read()
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch for {entry['name']}")
        if not path.exists():
            path.write_bytes(content)
        print(f"Verified {path.name}: {len(content)} bytes")


if __name__ == "__main__":
    main()
