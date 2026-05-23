# png_tools

PNG processing and collision map generation tools for Amiga game development projects.

## Usage

Run the tools via the command line or start the interactive TUI!

### Launching the TUI

To launch the interactive terminal user interface, run `png_tools` without any arguments:

```bash
./dist/png_tools
```

### CLI Subcommands

Alternatively, run specific tools directly from the CLI:

```bash
# Generate a 2-bit mask
png_tools mask png/pacman_tiles.png png

# Generate blitter-preshifted sprites
png_tools preshift png/sprite.png png --shifts 16

# Generate a Pac-man collision map
png_tools pacman-map --tolerance 2px --tile-width 16 png/stage-0001.png collision

# Generate a Plowman collision map
png_tools plowman-map --tolerance 2px --tile-width 16 png/stage-0001.png collision
```
