#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo 'Python 3.10+ is required. Install Python, then run this installer again.'
    exit 1
  fi
  python3 -m venv .venv
fi

if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
  .venv/bin/python -m ensurepip --upgrade
fi
.venv/bin/python -m pip install --upgrade ".[gui]"
.venv/bin/python -m fermi_softness install-app --open
