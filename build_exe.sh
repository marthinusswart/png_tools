#!/bin/sh
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR"

VENV_PYTHON="./.venv/bin/python"
VENV_PIP="./.venv/bin/pip"
VENV_PYINSTALLER="./.venv/bin/pyinstaller"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Python virtual environment not found at $(pwd)/.venv" >&2
    echo "Please run 'python3 -m venv .venv' in the project root first." >&2
    exit 1
fi

echo "Installing PyInstaller..."
"$VENV_PIP" install pyinstaller

echo "Building executable..."
"$VENV_PYINSTALLER" --name png_tools --paths src --onefile src/png_tools/cli.py

echo "✓ Build complete. The executable is located at ./dist/png_tools"