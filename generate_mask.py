import argparse
import sys
import os
from PIL import Image

def generate_mask(input_path: str, output_dir: str) -> None:
    """
    Generate a 2-bit mask from an input PNG.
    Index 0: Transparent (Original index 0)
    Index 1: White (Mask color)
    Index 2: Black
    """
    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        sys.exit(1)

    width, height = img.size

    # Create a new indexed image ('P' mode) for the mask
    mask_img = Image.new('P', (width, height), color=0)

    # Set up the palette for 2-bit color (indices 0-3):
    # Index 0: Black / Transparent (0, 0, 0)
    # Index 1: White (255, 255, 255) - Used for the mask
    # Index 2: Black (0, 0, 0)
    palette = [
        0, 0, 0,       # 0: Transparent/Black
        255, 255, 255, # 1: White
        0, 0, 0,       # 2: Black
    ]
    # Pad the palette out to 256 colors as expected by PIL
    palette.extend([0] * (768 - len(palette)))
    mask_img.putpalette(palette)

    original_pixels = img.load()
    mask_pixels = mask_img.load()

    for y in range(height):
        for x in range(width):
            pixel = original_pixels[x, y]
            
            # Determine if the pixel is index 0 (transparent)
            is_transparent = False
            if img.mode == 'P':
                is_transparent = (pixel == 0)
            elif img.mode == 'RGBA':
                is_transparent = (pixel[3] == 0) # Alpha channel is 0
            elif isinstance(pixel, int):
                is_transparent = (pixel == 0)
            else:
                # Fallback for RGB: Assume pure black is index 0
                is_transparent = (pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0)

            if is_transparent:
                mask_pixels[x, y] = 0  # Keep as index 0
            else:
                mask_pixels[x, y] = 1  # Make output white (index 1)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(input_path)
    name_only, ext = os.path.splitext(base_name)
    
    # Call the result the same name as the input png but add _mask
    output_filename = f"{name_only}_mask{ext}"
    output_path = os.path.join(output_dir, output_filename)

    # Save with 2-bit color depth and strictly set index 0 as transparent
    mask_img.save(output_path, bits=2, transparency=0)
    
    # Terminal formatting for summary table
    C_CYAN = "\033[96m"
    C_GREEN = "\033[92m"
    C_YELLOW = "\033[93m"
    C_MAGENTA = "\033[95m"
    C_BOLD = "\033[1m"
    C_RESET = "\033[0m"

    val_img = f"{width}x{height}"
    val_colors = "2-bit (Index 0=Trans, 1=White)"
    
    # Dynamically adjust table width based on path lengths
    max_val_len = max(len(val_img), len(val_colors), len(output_path))
    right_width = max(max_val_len + 2, 30)
    left_width = 16

    def print_row(label, value, color):
        print(f"{C_MAGENTA}│{C_RESET} {C_YELLOW}{label:<{left_width}}{C_RESET} {C_MAGENTA}│{C_RESET} {color}{value:<{right_width}}{C_RESET} {C_MAGENTA}│{C_RESET}")

    print(f"\n{C_MAGENTA}┌{'─' * (left_width + 2)}┬{'─' * (right_width + 2)}┐{C_RESET}")
    print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{C_BOLD}{'Mask Generation Summary':<{left_width + right_width + 3}}{C_RESET} {C_MAGENTA}│{C_RESET}")
    print(f"{C_MAGENTA}├{'─' * (left_width + 2)}┼{'─' * (right_width + 2)}┤{C_RESET}")
    print_row("Input image", val_img, C_GREEN)
    print_row("Color depth", val_colors, C_GREEN)
    print(f"{C_MAGENTA}├{'─' * (left_width + 2)}┼{'─' * (right_width + 2)}┤{C_RESET}")
    print_row("Output mask", output_path, C_CYAN)
    print(f"{C_MAGENTA}└{'─' * (left_width + 2)}┴{'─' * (right_width + 2)}┘{C_RESET}\n")

class TableHelpParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        C_CYAN = "\033[96m"
        C_GREEN = "\033[92m"
        C_YELLOW = "\033[93m"
        C_MAGENTA = "\033[95m"
        C_BOLD = "\033[1m"
        C_RESET = "\033[0m"
        C_RED = "\033[91m"

        print(f"\n{C_CYAN}{C_BOLD}Generate a 2-bit mask from a PNG image.{C_RESET}")
        print(f"{C_MAGENTA}┌{'─' * 16}┬{'─' * 58}┐{C_RESET}")
        print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{C_BOLD}{'Mask Generator Usage':<74}{C_RESET} {C_MAGENTA}│{C_RESET}")
        print(f"{C_MAGENTA}├{'─' * 16}┼{'─' * 58}┤{C_RESET}")
        print(f"{C_MAGENTA}│{C_RESET} {C_YELLOW}{'Argument':<14}{C_RESET} {C_MAGENTA}│{C_RESET} {C_YELLOW}{'Description':<56}{C_RESET} {C_MAGENTA}│{C_RESET}")
        print(f"{C_MAGENTA}├{'─' * 16}┼{'─' * 58}┤{C_RESET}")

        def print_arg(arg, desc, required=False):
            if required:
                desc_str = f"{C_RED}(Required){C_RESET} {C_GREEN}{desc:<45}{C_RESET}"
            else:
                desc_str = f"{C_GREEN}{desc:<56}{C_RESET}"
            print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{arg:<14}{C_RESET} {C_MAGENTA}│{C_RESET} {desc_str} {C_MAGENTA}│{C_RESET}")

        print_arg("input_png", "Path to the input PNG file", True)
        print_arg("output_dir", "Path to the output directory", True)
        print_arg("-h, --help", "Show this help message and exit")
        print(f"{C_MAGENTA}└{'─' * 16}┴{'─' * 58}┘{C_RESET}\n")
        print(f"  {C_CYAN}Example:{C_RESET} python generate_mask.py sprite.png ./output\n")

    def error(self, message):
        C_RED = "\033[91m"
        C_RESET = "\033[0m"
        print(f"\n{C_RED}Error: {message}{C_RESET}")
        self.print_help()
        sys.exit(2)

if __name__ == "__main__":
    parser = TableHelpParser(description="Generate a 2-bit mask from a PNG image.")
    parser.add_argument("input_png", help="Path to the input PNG file")
    parser.add_argument("output_dir", help="Path to the output directory")

    args = parser.parse_args()
    generate_mask(args.input_png, args.output_dir)