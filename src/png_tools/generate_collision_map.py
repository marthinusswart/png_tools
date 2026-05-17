import argparse
import sys
import os
from PIL import Image, ImageDraw, ImageFont

def parse_px_int(val) -> int:
    if isinstance(val, int):
        return val
    val_str = str(val).strip().lower()
    if val_str.endswith('px'):
        val_str = val_str[:-2]
    return int(val_str)

def extract_sprites(objects_sprite, tile_width, tile_height):
    obj_sprites = {}
    obj_sprite_bg = None
    
    if not objects_sprite or not os.path.exists(objects_sprite):
        return obj_sprites, obj_sprite_bg

    try:
        obj_sheet = Image.open(objects_sprite).convert("RGBA")
        
        # Find background color by finding the most common color
        sheet_colors = obj_sheet.getcolors(maxcolors=256000)
        if sheet_colors:
            obj_sprite_bg = max(sheet_colors, key=lambda x: x[0])[1]
        else:
            obj_sprite_bg = obj_sheet.getpixel((0, 0))
        
        def extract_sprite(index):
            sx = (index * tile_width) % obj_sheet.width
            sy = ((index * tile_width) // obj_sheet.width) * tile_height
            return obj_sheet.crop((sx, sy, sx + tile_width, sy + tile_height))
            
        obj_sprites[0] = extract_sprite(0) # Power Pill
        obj_sprites[1] = extract_sprite(1) # Ghost Base
        obj_sprites[2] = extract_sprite(2) # Generic Blocker
    except Exception as e:
        print(f"Error loading objects sprites: {e}", file=sys.stderr)

    return obj_sprites, obj_sprite_bg

def generate_base_map(img, tile_width, tile_height, rows, cols, tolerance):
    tile_map = []
    # Assume background color is the top-left pixel
    bg_color = img.getpixel((0, 0))

    for r in range(rows):
        row_data = []
        for c in range(cols):
            non_bg_count = 0
            for y in range(tile_height):
                for x in range(tile_width):
                    pixel = img.getpixel((c * tile_width + x, r * tile_height + y))
                    if pixel != bg_color:
                        non_bg_count += 1
            
            # 0 = Path, 1 = Wall
            cell_val = 0 if non_bg_count <= tolerance else 1
            row_data.append(cell_val)
        tile_map.append(row_data)
        
    return tile_map

def overlay_objects(tile_map, obj_img, obj_sprites, obj_sprite_bg, tile_width, tile_height, rows, cols):
    sprite_to_map_val = {
        0: 2,  # Power Pill
        1: 3,  # Ghost Base
        2: 9   # Generic Blocker
    }

    for r in range(rows):
        for c in range(cols):
            cell_box = (c * tile_width, r * tile_height, (c + 1) * tile_width, (r + 1) * tile_height)
            cell_img = obj_img.crop(cell_box)
            
            for sprite_idx, sprite_img in obj_sprites.items():
                if is_exact_match(cell_img, sprite_img, obj_sprite_bg, tile_width, tile_height):
                    tile_map[r][c] = sprite_to_map_val[sprite_idx]
                    break

def generate_annotated_preview(img, tile_width, tile_height, rows, cols, scale, output_folder, base_name):
    scaled_img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
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
    
    out_png = os.path.join(output_folder, f"{base_name}_tilemap.png")
    scaled_img.save(out_png)
    return out_png

def export_c_and_bin(tile_map, rows, cols, output_folder, base_name):
    c_var_name = base_name.replace('-', '_')
    
    c_code = "// clang-format off\n"
    c_code += "// Legend:\n"
    c_code += "// +------+------------+\n"
    c_code += "// | Code | Type       |\n"
    c_code += "// +------+------------+\n"
    c_code += "// |   0  | Path       |\n"
    c_code += "// |   1  | Wall       |\n"
    c_code += "// |   2  | Power Pill |\n"
    c_code += "// |   3  | Ghost Base |\n"
    c_code += "// |   9  | Other      |\n"
    c_code += "// +------+------------+\n"
    c_code += f"UBYTE mapping_{c_var_name}[{rows * cols}] = {{\n"
    
    for r in range(rows):
        line = "    " + ", ".join(str(val) for val in tile_map[r])
        if r < rows - 1:
            line += ","
        c_code += line + "\n"
        
    c_code += "};\n// clang-format on\n"
    
    bin_path = f"{output_folder}/{base_name}.bin".replace('\\', '/').replace('//', '/')
    c_code += "\n/*\n"
    c_code += " * Runtime Binary Loading Example\n"
    c_code += " * ------------------------------\n"
    c_code += " * #include <stdio.h>\n"
    c_code += " * \n"
    c_code += f" * // Allocate the array once ({rows * cols} bytes)\n"
    c_code += f" * UBYTE current_stage_map[{rows * cols}];\n"
    c_code += " * \n"
    c_code += " * // Call this when you want to load a level\n"
    c_code += " * void load_stage(const char* filepath) {\n"
    c_code += " *     FILE *file = fopen(filepath, \"rb\");\n"
    c_code += " *     if (file != NULL) {\n"
    c_code += f" *         // Read {rows * cols} bytes directly into the array\n"
    c_code += f" *         fread(current_stage_map, sizeof(UBYTE), {rows * cols}, file);\n"
    c_code += " *         fclose(file);\n"
    c_code += " *     } else {\n"
    c_code += " *         printf(\"Failed to load stage map: %s\\n\", filepath);\n"
    c_code += " *     }\n"
    c_code += " * }\n"
    c_code += " * \n"
    c_code += " * // Usage Example:\n"
    c_code += f" * // load_stage(\"{bin_path}\");\n"
    c_code += " */\n"

    out_c = os.path.join(output_folder, f"{base_name}.c")
    with open(out_c, "w") as f:
        f.write(c_code)
        
    # Generate raw binary file
    out_bin = os.path.join(output_folder, f"{base_name}.bin")
    with open(out_bin, "wb") as f:
        flat_map = [val for row in tile_map for val in row]
        f.write(bytes(flat_map))

    return out_c, out_bin

def generate_tilemap(input_path: str, output_folder: str, tile_width: int, tile_height: int, scale: int, tolerance: int, objects_sprite: str = None) -> None:
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

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    objects_path = os.path.join(os.path.dirname(input_path), f"{base_name}-objects.png")
    
    # Phase 1: Base Map (0 = Path, 1 = Wall) from the main stage image
    tile_map = generate_base_map(img, tile_width, tile_height, rows, cols, tolerance)

    # Phase 2: Object Mapping from the -objects.png image
    obj_sprites, obj_sprite_bg = extract_sprites(objects_sprite, tile_width, tile_height)
    if obj_sprites:
        if os.path.exists(objects_path):
            try:
                obj_img = Image.open(objects_path).convert("RGBA")
                overlay_objects(tile_map, obj_img, obj_sprites, obj_sprite_bg, tile_width, tile_height, rows, cols)
            except Exception as e:
                print(f"Error opening objects image '{objects_path}': {e}", file=sys.stderr)
        else:
            print(f"Warning: Objects sprite provided but '{objects_path}' not found.", file=sys.stderr)

    # Generate Outputs
    out_png = generate_annotated_preview(img, tile_width, tile_height, rows, cols, scale, output_folder, base_name)
    out_c, out_bin = export_c_and_bin(tile_map, rows, cols, output_folder, base_name)

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
    val_tol = f"{tolerance} px"
    
    # Dynamically adjust table width based on path lengths
    max_val_len = max(len(val_img), len(val_tile), len(val_grid), len(val_tol), len(out_png), len(out_c), len(out_bin))
    right_width = max(max_val_len + 2, 20)
    left_width = 18

    def print_row(label, value, color):
        print(f"{C_MAGENTA}│{C_RESET} {C_YELLOW}{label:<{left_width}}{C_RESET} {C_MAGENTA}│{C_RESET} {color}{value:<{right_width}}{C_RESET} {C_MAGENTA}│{C_RESET}")

    print(f"\n{C_MAGENTA}┌{'─' * (left_width + right_width + 5)}┐{C_RESET}")
    print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{C_BOLD}{'Collision Map Generation Summary':<{left_width + right_width + 3}}{C_RESET} {C_MAGENTA}│{C_RESET}")
    print(f"{C_MAGENTA}├{'─' * (left_width + 2)}┬{'─' * (right_width + 2)}┤{C_RESET}")
    print_row("Input image", val_img, C_GREEN)
    print_row("Tile size", val_tile, C_GREEN)
    print_row("Grid", val_grid, C_GREEN)
    print_row("Tolerance", val_tol, C_GREEN)
    print(f"{C_MAGENTA}├{'─' * (left_width + 2)}┼{'─' * (right_width + 2)}┤{C_RESET}")
    print_row("Annotated tilemap", out_png, C_CYAN)
    print_row("C array", out_c, C_CYAN)
    print_row("Binary map", out_bin, C_CYAN)
    print(f"{C_MAGENTA}└{'─' * (left_width + 2)}┴{'─' * (right_width + 2)}┘{C_RESET}\n")

def is_exact_match(cell_img, sprite_img, sprite_bg, width, height):
    # 1. Determine the foreground color(s) of the sprite and count their pixels
    sprite_color_counts = {}
    
    for y in range(height):
        for x in range(width):
            sp = sprite_img.getpixel((x, y))
            
            # Check for background (transparent or matches bg color)
            # Use exact 4-channel tuple match to prevent treating opaque black as transparent black
            sp_is_bg = (len(sp) == 4 and sp[3] == 0) or (sp == sprite_bg)
            
            if not sp_is_bg:
                color = sp[:3]
                sprite_color_counts[color] = sprite_color_counts.get(color, 0) + 1
                
    if not sprite_color_counts:
        return False

    # 2. Count ALL non-transparent colors in the cell for accurate debugging
    cell_color_counts = {}
    
    for y in range(height):
        for x in range(width):
            cp = cell_img.getpixel((x, y))
            
            # Ignore fully transparent pixels. Everything else is evaluated against sprite colors.
            if not (len(cp) == 4 and cp[3] == 0):
                color = cp[:3]
                cell_color_counts[color] = cell_color_counts.get(color, 0) + 1
                
    # 3. Compare the counts. If the cell has extra pixels of this color (like an 'X'), it fails.
    is_match = True
    for color, count in sprite_color_counts.items():
        if cell_color_counts.get(color, 0) != count:
            is_match = False
            break
            
    return is_match

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
        print(f"{C_MAGENTA}┌{'─' * 75}┐{C_RESET}")
        print(f"{C_MAGENTA}│{C_RESET} {C_CYAN}{C_BOLD}{'Collision Map Generator Usage':<73}{C_RESET} {C_MAGENTA}│{C_RESET}")
        print(f"{C_MAGENTA}├{'─' * 16}┬{'─' * 58}┤{C_RESET}")
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
        print_arg("--tolerance", "Max non-bg pixels to still be a path (default: 0)")
        print_arg("--objects-sprite", "Path to objects sprite sheet PNG")
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
    parser.add_argument("--tolerance", type=parse_px_int, default=0, help="Max non-bg pixels to still be a path (default: 0)")
    parser.add_argument("--objects-sprite", type=str, default=None, help="Path to objects sprite sheet PNG (e.g., pacman_map_objects.png)")

    args = parser.parse_args()
    generate_tilemap(args.input_png, args.output_dir, args.tile_width, args.tile_height, args.scale, args.tolerance, args.objects_sprite)