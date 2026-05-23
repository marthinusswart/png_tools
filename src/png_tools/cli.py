import sys

from png_tools.generate_mask import main as mask_main
from png_tools.generate_preshift import main as preshift_main
from png_tools.plowman.generate_collision_map import main as plowman_main
from png_tools.pacman.generate_collision_map import main as pacman_main
from png_tools.rich_coverage import main as cov_main

def main():
    if len(sys.argv) < 2:
        try:
            from png_tools.tui import main as tui_main
            tui_main()
            sys.exit(0)
        except ImportError as e:
            print(f"Error importing TUI: {e}", file=sys.stderr)
            print("Usage: png_tools <command> [args]")
            print("Commands:")
            print("  mask         - Generate 2-bit mask")
            print("  preshift     - Generate preshifted sprites")
            print("  plowman-map  - Generate Plowman collision map")
            print("  pacman-map   - Generate Pac-Man collision map")
            print("  cov          - Show beautiful test coverage report")
            sys.exit(1)

    command = sys.argv[1]
    # Remove the command so the sub-scripts parse arguments correctly
    sys.argv.pop(1)
    # Update sys.argv[0] to reflect the command being run for accurate help text
    sys.argv[0] = f"png_tools {command}"

    if command == "mask":
        mask_main()
    elif command == "preshift":
        preshift_main()
    elif command == "plowman-map":
        plowman_main()
    elif command == "pacman-map":
        pacman_main()
    elif command in ["cov", "coverage"]:
        cov_main()
    else:
        print(f"Unknown command: '{command}'")
        print("Available commands: mask, preshift, plowman-map, pacman-map, cov")
        sys.exit(1)

if __name__ == "__main__":
    main()