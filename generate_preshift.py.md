#!/usr/bin/env python3
"""
Generate 16 pre-shifted versions of a sprite for Amiga blitter operations.

Takes a single sprite (16x16, 32x32, etc.) and creates 16 pre-shifted versions
stacked vertically. Each version has the sprite shifted right by 0-15 pixels
with a 16-pixel buffer on the right to catch overflow.

Input: NxM sprite (e.g., 16x16, 32x32)
Output: (N+16) x (M*16) PNG with all 16 pre-shifted versions stacked vertically
"""

from PIL import Image
import sys

def generate_preshift(input_path, output_path, num_shifts=16, buffer_size=16):
    """
    Generate pre-shifted sprite versions for blitter operations.

    Args:
        input_path: Path to input sprite PNG
        output_path: Path to output PNG
        num_shifts: Number of shift versions to generate (0-15 = 16 versions)
        buffer_size: Buffer width in pixels (16 for standard Amiga blitter)
    """
    # Load the input sprite
    img = Image.open(input_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    sprite_width, sprite_height = img.size

    print(f"Input sprite: {sprite_width}x{sprite_height}")
    print(f"Generating {num_shifts} pre-shifted versions (shifts 0-{num_shifts-1})")
    print(f"Buffer size: {buffer_size} pixels")

    # Calculate output dimensions
    # Width: original sprite width + buffer for overflow
    output_width = sprite_width + buffer_size
    # Height: sprite height × number of shift versions (stacked vertically)
    output_height = sprite_height * num_shifts

    print(f"Output image: {output_width}x{output_height}")
    print(f"Each pre-shifted version: {output_width}x{sprite_height}")

    # Create output image with transparency
    output = Image.new('RGBA', (output_width, output_height), (0, 0, 0, 0))

    # Generate each pre-shifted version
    for shift in range(num_shifts):
        # Create a transparent buffer for this shift version
        shift_version = Image.new('RGBA', (output_width, sprite_height), (0, 0, 0, 0))

        # Paste the sprite shifted right by 'shift' pixels
        shift_version.paste(img, (shift, 0), img)

        # Calculate vertical position in output (stack versions vertically)
        y_offset = shift * sprite_height

        # Paste this shift version into the output
        output.paste(shift_version, (0, y_offset))

        print(f"  Shift {shift:2d}: sprite offset {shift} pixels right, row {shift+1}/{num_shifts}")

    # Save the output
    output.save(output_path)
    print(f"\nSaved to: {output_path}")
    print(f"\nEach pre-shifted version is a horizontal band {output_width}x{sprite_height} pixels.")
    print(f"To use: Select the appropriate shift version based on sprite X position % 16")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_preshift.py <input.png> <output.png>")
        print("\nGenerates 16 pre-shifted versions of a sprite for Amiga blitter.")
        print("\nExample:")
        print("  python generate_preshift.py player.png player_preshift.png")
        print("\nInput: 16x16 sprite")
        print("Output: 32x256 PNG (16 versions × 16 rows each)")
        print("\nWorks with any sprite size - automatically adds 16px buffer on right")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    generate_preshift(input_file, output_file)
