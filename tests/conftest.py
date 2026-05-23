import pytest
from PIL import Image
import os

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture returning the tmp_path directory as a string."""
    return str(tmp_path)

@pytest.fixture
def create_indexed_png(tmp_path):
    """Factory fixture to create an indexed ('P' mode) PNG image."""
    def _create(filename="test_p.png", size=(16, 16), transparent_color=(0, 0, 0), opaque_color=(255, 255, 255)):
        img = Image.new('P', size, color=0)
        
        # Setup simple palette: 0 is black/transparent, 1 is white, 2 is red
        palette = [
            transparent_color[0], transparent_color[1], transparent_color[2],  # Index 0
            opaque_color[0], opaque_color[1], opaque_color[2],                # Index 1
            255, 0, 0,                                                         # Index 2 (Red)
        ]
        palette.extend([0] * (768 - len(palette)))
        img.putpalette(palette)
        
        # Put some pixels: draw a simple pattern
        pixels = img.load()
        for y in range(size[1]):
            for x in range(size[0]):
                if (x + y) % 2 == 0:
                    pixels[x, y] = 0  # index 0 (transparent)
                elif x == y:
                    pixels[x, y] = 2  # index 2 (red)
                else:
                    pixels[x, y] = 1  # index 1 (white)
                    
        file_path = tmp_path / filename
        img.save(file_path, bits=8)
        return str(file_path)
    return _create

@pytest.fixture
def create_rgba_png(tmp_path):
    """Factory fixture to create an RGBA mode PNG image."""
    def _create(filename="test_rgba.png", size=(16, 16)):
        img = Image.new('RGBA', size, (0, 0, 0, 0)) # transparent background
        pixels = img.load()
        for y in range(size[1]):
            for x in range(size[0]):
                if (x + y) % 2 == 0:
                    pixels[x, y] = (255, 255, 255, 255)  # opaque white
                else:
                    pixels[x, y] = (0, 0, 0, 0)          # transparent
                    
        file_path = tmp_path / filename
        img.save(file_path)
        return str(file_path)
    return _create

@pytest.fixture
def create_rgb_png(tmp_path):
    """Factory fixture to create an RGB mode PNG image."""
    def _create(filename="test_rgb.png", size=(16, 16)):
        img = Image.new('RGB', size, (0, 0, 0)) # black background
        pixels = img.load()
        for y in range(size[1]):
            for x in range(size[0]):
                if (x + y) % 2 == 0:
                    pixels[x, y] = (255, 255, 255)  # white
                else:
                    pixels[x, y] = (0, 0, 0)        # black
                    
        file_path = tmp_path / filename
        img.save(file_path)
        return str(file_path)
    return _create

@pytest.fixture
def create_object_sprite_sheet(tmp_path):
    """Factory fixture to create an objects sprite sheet PNG for collision mapping."""
    def _create(filename="test_objects.png", tile_size=(16, 16)):
        # 3 tiles horizontally (index 0: Power Pill, index 1: Ghost Base, index 2: Generic Blocker)
        width = tile_size[0] * 3
        height = tile_size[1]
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Draw some distinct pixel patterns in each tile to identify them
        # Let's say:
        # Tile 0 (Power Pill): a yellow pixel in the center (8,8)
        # Tile 1 (Ghost Base): a blue pixel in the center (8,8)
        # Tile 2 (Generic Blocker): a red pixel in the center (8,8)
        pixels = img.load()
        
        # Tile 0
        pixels[tile_size[0] // 2, tile_size[1] // 2] = (255, 255, 0, 255) # Yellow
        # Tile 1
        pixels[tile_size[0] + tile_size[0] // 2, tile_size[1] // 2] = (0, 0, 255, 255) # Blue
        # Tile 2
        pixels[2 * tile_size[0] + tile_size[0] // 2, tile_size[1] // 2] = (255, 0, 0, 255) # Red
        
        file_path = tmp_path / filename
        img.save(file_path)
        return str(file_path)
    return _create
