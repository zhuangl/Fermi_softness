#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Install the project first: python3 -m venv .venv && .venv/bin/python -m pip install ".[gui]"'
  exit 1
fi
exec .venv/bin/python -m fermi_softness gui "$@"
