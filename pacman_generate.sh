#!/bin/sh
set -e

# Get the directory where the script is located and change to it.
# This makes all relative paths (like for venv and assets) work correctly.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR"

EXE="./dist/png_tools"

if [ ! -f "$EXE" ]; then
    echo "Error: png_tools executable not found at $EXE" >&2
    echo "Please run './build_exe.sh' first to compile the tool." >&2
    exit 1
fi

echo "Generating mask for pacman tiles..."
"$EXE" mask png/pacman_tiles.png png

echo "Generating mask for alphanumeric tiles..."
"$EXE" mask png/alphanumeric.png png

echo "Generating collision map for stage 1..."
"$EXE" pacman-map --tolerance 2px --tile-width 16 --tile-height 16 --scale 3 --objects-sprite png/pacman_map_objects.png png/stage-0001.png collision

echo "✓ Generation complete. Outputs are in the 'png' and 'collision' directories."