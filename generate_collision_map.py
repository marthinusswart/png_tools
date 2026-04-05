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

    print(f"Input image: {width}x{height}")
    print(f"Tile size: {tile_width}x{tile_height}")
    print(f"Grid: {cols} columns x {rows} rows")

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
    print(f"Saved annotated tilemap image to: {out_png}")

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
        
    print(f"Saved C array map to: {out_c}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates a C array and annotated tilemap PNG from an image map.")
    parser.add_argument("input_png", help="Path to input sprite PNG")
    parser.add_argument("output_dir", help="Path to output directory for the generated files")
    parser.add_argument("--tile-width", type=int, default=16, help="Tile width for tilemap (default: 16)")
    parser.add_argument("--tile-height", type=int, default=16, help="Tile height for tilemap (default: 16)")
    parser.add_argument("--scale", type=int, default=3, help="Scale factor for tilemap output PNG (default: 3)")

    args = parser.parse_args()
    generate_tilemap(args.input_png, args.output_dir, args.tile_width, args.tile_height, args.scale)