import argparse
import sys
import os
from PIL import Image, ImageDraw, ImageFont

def generate_tilemap(input_path: str, output_folder: str, tile_width: int, tile_height: int, scale: int) -> None:
    """
    Generate a C array tilemap and an annotated PNG from an image.
    """
    try:
        img = Image.open(input_path).convert("RGB")
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        sys.exit(1)

    width, height = img.size
    cols = width // tile_width
    rows = height // tile_height

    if cols == 0 or rows == 0:
        print("Error: Image is smaller than the specified tile size.", file=sys.stderr)
        sys.exit(1)

    # Assume background color is the top-left pixel
    bg_color = img.getpixel((0, 0))

    tile_map = []
    
    for r in range(rows):
        row_data = []
        for c in range(cols):
            is_bg_only = True
            for y in range(tile_height):
                for x in range(tile_width):
                    pixel = img.getpixel((c * tile_width + x, r * tile_height + y))
                    if pixel != bg_color:
                        is_bg_only = False
                        break
                if not is_bg_only:
                    break
            
            # 0 = Path (background only), 1 = Wall (has other colors)
            row_data.append(0 if is_bg_only else 1)
        tile_map.append(row_data)

    # Generate scaled image with text
    scaled_img = img.resize((width * scale, height * scale), Image.NEAREST)
    draw = ImageDraw.Draw(scaled_img)
    
    font = ImageFont.load_default()
        
    for r in range(rows):
        for c in range(cols):
            x0 = c * tile_width * scale
            y0 = r * tile_height * scale
            x1 = x0 + tile_width * scale
            y1 = y0 + tile_height * scale
            
            draw.rectangle([x0, y0, x1, y1], outline=(128, 128, 128))
            
            text = f"{r},{c}"
            draw.text((x0 + 2, y0 + 2), text, fill=(255, 0, 0), font=font)

    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    out_png = os.path.join(output_folder, f"{base_name}_tilemap.png")
    scaled_img.save(out_png)

    c_var_name = base_name.replace('-', '_')
    
    c_code = "// clang-format off\n"
    c_code += "// Example: 0 = Path, 1 = Wall\n"
    c_code += f"UBYTE mapping_{c_var_name}[{rows * cols}] = {{\n"
    
    for r in range(rows):
        line = "    " + ", ".join(str(val) for val in tile_map[r])
        if r < rows - 1:
            line += ","
        c_code += line + "\n"
        
    c_code += "};\n// clang-format on\n"
    
    out_c = os.path.join(output_folder, f"{base_name}.c")
    with open(out_c, "w") as f:
        f.write(c_code)
        
    # Terminal formatting for summary table
    C_CYAN = "\033[96m"
    C_GREEN = "\033[92m"
    C_YELLOW = "\033[93m"
    C_MAGENTA = "\033[95m"
    C_BOLD = "\033[1m"
    C_RESET = "\033[0m"

    val_img = f"{width}x{height}"
    val_tile = f"{tile_width}x{tile_height}"
    val_grid = f"{cols} columns x {rows} rows"
    
    # Dynamically adjust table width based on path lengths
    max_val_len = max(len(val_img), len(val_tile), len(val_grid), len(out_png), len(out_c))
    right_width = max(max_val_len + 2, 20)
    left_width = 18

    def print_row(label, value, color):
        print(f"{C_MAGENTA}│{C_RESET} {C_YELLOW}{label:<{left_width}}{C_RESET} {C_MAGENTA}│{C_RESET} {color}{value:<{right_width}}{C_RESET} {C_MAGENTA}│{C_RESET}")

    print(f"\n{C_MAGENTA}┌{'─' * (left_width + 2)}┬{'─' * (right_width + 2)}┐{C_RESET}")
    print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{C_BOLD}{'Collision Map Generation Summary':<{left_width + right_width + 3}}{C_RESET} {C_MAGENTA}│{C_RESET}")
    print(f"{C_MAGENTA}├{'─' * (left_width + 2)}┼{'─' * (right_width + 2)}┤{C_RESET}")
    print_row("Input image", val_img, C_GREEN)
    print_row("Tile size", val_tile, C_GREEN)
    print_row("Grid", val_grid, C_GREEN)
    print(f"{C_MAGENTA}├{'─' * (left_width + 2)}┼{'─' * (right_width + 2)}┤{C_RESET}")
    print_row("Annotated tilemap", out_png, C_CYAN)
    print_row("C array", out_c, C_CYAN)
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

        print(f"\n{C_CYAN}{C_BOLD}Generates a C array and annotated tilemap PNG from an image map.{C_RESET}")
        print(f"{C_MAGENTA}┌{'─' * 16}┬{'─' * 58}┐{C_RESET}")
        print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{C_BOLD}{'Collision Map Generator Usage':<74}{C_RESET} {C_MAGENTA}│{C_RESET}")
        print(f"{C_MAGENTA}├{'─' * 16}┼{'─' * 58}┤{C_RESET}")
        print(f"{C_MAGENTA}│{C_RESET} {C_YELLOW}{'Argument':<14}{C_RESET} {C_MAGENTA}│{C_RESET} {C_YELLOW}{'Description':<56}{C_RESET} {C_MAGENTA}│{C_RESET}")
        print(f"{C_MAGENTA}├{'─' * 16}┼{'─' * 58}┤{C_RESET}")

        def print_arg(arg, desc, required=False):
            if required:
                desc_str = f"{C_RED}(Required){C_RESET} {C_GREEN}{desc:<45}{C_RESET}"
            else:
                desc_str = f"{C_GREEN}{desc:<56}{C_RESET}"
            print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{arg:<14}{C_RESET} {C_MAGENTA}│{C_RESET} {desc_str} {C_MAGENTA}│{C_RESET}")

        print_arg("input_png", "Path to input sprite PNG", True)
        print_arg("output_dir", "Path to output dir for generated files", True)
        print_arg("-h, --help", "Show this help message and exit")
        print_arg("--tile-width", "Tile width for tilemap (default: 16)")
        print_arg("--tile-height", "Tile height for tilemap (default: 16)")
        print_arg("--scale", "Scale factor for tilemap output PNG (default: 3)")
        print(f"{C_MAGENTA}└{'─' * 16}┴{'─' * 58}┘{C_RESET}\n")
        print(f"  {C_CYAN}Example:{C_RESET} python generate_collision_map.py level.png ./output --tile-width 16\n")

    def error(self, message):
        C_RED = "\033[91m"
        C_RESET = "\033[0m"
        print(f"\n{C_RED}Error: {message}{C_RESET}")
        self.print_help()
        sys.exit(2)

if __name__ == "__main__":
    parser = TableHelpParser(description="Generates a C array and annotated tilemap PNG from an image map.")
    parser.add_argument("input_png", help="Path to input sprite PNG")
    parser.add_argument("output_dir", help="Path to output directory for the generated files")
    parser.add_argument("--tile-width", type=int, default=16, help="Tile width for tilemap (default: 16)")
    parser.add_argument("--tile-height", type=int, default=16, help="Tile height for tilemap (default: 16)")
    parser.add_argument("--scale", type=int, default=3, help="Scale factor for tilemap output PNG (default: 3)")

    args = parser.parse_args()
    generate_tilemap(args.input_png, args.output_dir, args.tile_width, args.tile_height, args.scale)