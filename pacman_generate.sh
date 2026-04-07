#!/bin/sh
set -e

# Get the directory where the script is located and change to it.
# This makes all relative paths (like for venv and assets) work correctly.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR"

# Per README.md, the virtual environment is named 'venv'.
# If yours is named '.venv', change the path below.
VENV_PYTHON="./.venv/bin/python"

# Check if the python executable exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Python virtual environment not found at $(pwd)/.venv" >&2
    echo "Please run 'python3 -m venv .venv' in the project root first." >&2
    exit 1
fi

echo "Generating mask for pacman tiles..."
"$VENV_PYTHON" generate_mask.py png/pacman_tiles.png png

echo "Generating collision map for stage 1..."
"$VENV_PYTHON" generate_collision_map.py --tile-width 16 --tile-height 16 --scale 3 png/stage-0001.png collision

echo "✓ Generation complete. Outputs are in the 'png' and 'collision' directories."