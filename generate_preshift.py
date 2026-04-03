"""
Generate 16 pre-shifted versions of a sprite for Amiga blitter operations.

Takes a single sprite (16x16, 32x32, etc.) and creates 16 pre-shifted versions
stacked vertically. Each version has the sprite shifted right by 0-15 pixels
with a 16-pixel buffer on the right to catch overflow.

Input: NxM sprite (e.g., 16x16, 32x32)
Output: (N+16) x (M*16) PNG with all 16 pre-shifted versions stacked vertically
"""

import argparse
import sys
import os
from PIL import Image

def generate_preshift(input_path: str, output_path: str, num_shifts: int = 16, buffer_size: int = 16, reverse_shift: bool = False) -> None:
    """
    Generate pre-shifted sprite versions for blitter operations.

    Args:
        input_path: Path to input sprite PNG
        output_path: Path to output PNG
        num_shifts: Number of shift versions to generate (0-15 = 16 versions)
        buffer_size: Buffer width in pixels (16 for standard Amiga blitter)
    """
    try:
        # Load the input sprite
        img_p = Image.open(input_path)
    except FileNotFoundError:
        print(f"Error: Could not find input file '{input_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        sys.exit(1)

    if img_p.mode != 'P':
        print(f"Error: Input image '{input_path}' is not an indexed palette ('P' mode) image.", file=sys.stderr)
        print("This script requires an 8-bit indexed color PNG to preserve the palette.", file=sys.stderr)
        sys.exit(1)

    # Convert to RGBA for processing, will be quantized back to original palette later.
    # This correctly handles transparency during the shift-and-paste operations.
    img = img_p.convert('RGBA')

    sprite_width, sprite_height = img.size

    print(f"Input sprite: {sprite_width}x{sprite_height} (Indexed Color)")
    print(f"Generating {num_shifts} pre-shifted versions (shifts 0-{num_shifts-1})")
    print(f"Buffer size: {buffer_size} pixels")

    # Calculate output dimensions
    # Width: original sprite width + buffer for overflow
    output_width = sprite_width + buffer_size
    # Height: sprite height × number of shift versions (stacked vertically)
    output_height = sprite_height * num_shifts

    print(f"Output image: {output_width}x{output_height}")
    print(f"Each pre-shifted version: {output_width}x{sprite_height}")

    # Create RGBA output image for manipulation; will be quantized at the end.
    output_rgba = Image.new('RGBA', (output_width, output_height), (0, 0, 0, 0))

    # Generate each pre-shifted version
    for shift in range(num_shifts):
        # Calculate vertical position in output (stack versions vertically)
        y_offset = shift * sprite_height

        if reverse_shift:
            # For left shift, the sprite moves from the right edge of the buffer towards the left
            # shift=0: sprite starts at buffer_size (rightmost position in the buffer area)
            # shift=N: sprite starts at buffer_size - N
            x_offset = buffer_size - shift
            print(f"  Shift {shift:2d}: sprite offset {shift} pixels left, row {shift+1}/{num_shifts}")
        else:
            # For right shift, the sprite moves from the left edge of the buffer towards the right
            x_offset = shift
            print(f"  Shift {shift:2d}: sprite offset {shift} pixels right, row {shift+1}/{num_shifts}")

        output_rgba.paste(img, (x_offset, y_offset), img)

    # Quantize the final image back to the original palette without dithering
    print("\nConverting final image back to original indexed palette...")
    # The quantize method requires an RGB or L mode image when using a palette from another image.
    output = output_rgba.convert('RGB').quantize(palette=img_p, dither=Image.Dither.NONE)

    # Save the output
    # Ensure the output directory exists before saving
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    output.save(output_path)
    print(f"\nSaved to: {output_path}")
    print(f"\nEach pre-shifted version is a horizontal band {output_width}x{sprite_height} pixels.")
    print(f"To use: Select the appropriate shift version based on sprite X position % 16")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates 16 pre-shifted versions of a sprite for Amiga blitter.",
        epilog="Examples:\n"
               "  python generate_preshift.py player.png ./shifted_sprites\n"
               "    This will create 'player_shifted.png' inside the 'shifted_sprites' directory (right-shifted).\n\n"
               "  python generate_preshift.py player.png ./shifted_sprites --reverse\n"
               "    This will create 'player_shifted_reverse.png' inside the 'shifted_sprites' directory (left-shifted).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_png", help="Path to input sprite PNG")
    parser.add_argument("output_dir", help="Path to output directory for the generated file")
    parser.add_argument("--shifts", type=int, default=16, help="Number of shift versions (default: 16)")
    parser.add_argument("--buffer", type=int, default=16, help="Buffer size in pixels (default: 16)")
    parser.add_argument("--reverse", action="store_true", help="Generate left-shifted versions instead of right-shifted.")

    args = parser.parse_args()

    # Construct the full output path from the input filename and output directory
    # Get base name of input file, e.g., 'player.png'
    base_name = os.path.basename(args.input_png)
    # Get file name without extension, e.g., 'player'
    name_only = os.path.splitext(base_name)[0]
    # Create the new filename based on whether it's reversed or not
    output_filename = f"{name_only}_shifted_reverse.png" if args.reverse else f"{name_only}_shifted.png"
    # Create the full output path, e.g., './shifted_sprites/player_shifted.png'
    final_output_path = os.path.join(args.output_dir, output_filename)

    generate_preshift(args.input_png, final_output_path, num_shifts=args.shifts, buffer_size=args.buffer, reverse_shift=args.reverse)