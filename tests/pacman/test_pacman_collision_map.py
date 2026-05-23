import pytest
import os
import sys
from PIL import Image
from unittest.mock import patch, MagicMock

from png_tools.pacman.generate_collision_map import (
    parse_px_int,
    extract_sprites,
    generate_base_map,
    is_exact_match,
    overlay_objects,
    generate_annotated_preview,
    export_c_and_bin,
    generate_tilemap,
    main,
    TableHelpParser
)

def test_parse_px_int():
    assert parse_px_int(16) == 16
    assert parse_px_int("16px") == 16
    assert parse_px_int("  32px  ") == 32
    assert parse_px_int("8") == 8

def test_extract_sprites_nonexistent():
    sprites, bg = extract_sprites("nonexistent.png", 16, 16)
    assert sprites == {}
    assert bg is None
    
    sprites, bg = extract_sprites(None, 16, 16)
    assert sprites == {}
    assert bg is None

def test_extract_sprites_valid(create_object_sprite_sheet):
    sheet_path = create_object_sprite_sheet("objects.png", tile_size=(16, 16))
    sprites, bg = extract_sprites(sheet_path, 16, 16)
    
    assert len(sprites) == 3
    assert 0 in sprites
    assert 1 in sprites
    assert 2 in sprites
    assert bg == (0, 0, 0, 0) # transparent black is background

def test_extract_sprites_getpixel_bg(create_object_sprite_sheet):
    # Covers line 29: getcolors() returns None, falls back to getpixel((0,0))
    sheet_path = create_object_sprite_sheet("objects_bg.png", tile_size=(16, 16))
    
    with patch('PIL.Image.Image.getcolors', return_value=None):
        sprites, bg = extract_sprites(sheet_path, 16, 16)
        assert bg == (0, 0, 0, 0)

def test_extract_sprites_exception(create_object_sprite_sheet):
    # Covers lines 39-40: exception raised during extract_sprites
    sheet_path = create_object_sprite_sheet("corrupt.png")
    with patch('PIL.Image.open', side_effect=ValueError("Corrupt sheet")):
        sprites, bg = extract_sprites(sheet_path, 16, 16)
        assert sprites == {}
        assert bg is None

def test_generate_base_map(create_rgb_png):
    img_path = create_rgb_png("stage.png", size=(32, 32))
    
    with Image.open(img_path) as img:
        tile_map = generate_base_map(img, 16, 16, 2, 2, tolerance=100)
        assert tile_map == [[1, 1], [1, 1]]
        
        tile_map_high_tol = generate_base_map(img, 16, 16, 2, 2, tolerance=130)
        assert tile_map_high_tol == [[0, 0], [0, 0]]

def test_is_exact_match(create_object_sprite_sheet):
    sheet_path = create_object_sprite_sheet("objects.png", tile_size=(16, 16))
    sprites, bg = extract_sprites(sheet_path, 16, 16)
    sprite0 = sprites[0]
    
    cell_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    cell_pixels = cell_img.load()
    cell_pixels[8, 8] = (255, 255, 0, 255)
    
    assert is_exact_match(cell_img, sprite0, bg, 16, 16) is True
    
    cell_bad = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    assert is_exact_match(cell_bad, sprite0, bg, 16, 16) is False

def test_is_exact_match_empty_sprite():
    # Covers line 272: sprite_color_counts is empty (transparent sprite)
    cell_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    sprite_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    bg = (0, 0, 0, 0)
    
    assert is_exact_match(cell_img, sprite_img, bg, 16, 16) is False

def test_overlay_objects(create_object_sprite_sheet):
    sheet_path = create_object_sprite_sheet("objects.png", tile_size=(16, 16))
    sprites, bg = extract_sprites(sheet_path, 16, 16)
    
    obj_img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    pixels = obj_img.load()
    
    pixels[8, 8] = (255, 255, 0, 255)
    pixels[16 + 8, 16 + 8] = (0, 0, 255, 255)
    
    tile_map = [[0, 0], [0, 0]]
    overlay_objects(tile_map, obj_img, sprites, bg, 16, 16, 2, 2)
    
    assert tile_map == [[2, 0], [0, 3]]

def test_export_c_and_bin(temp_dir):
    tile_map = [[1, 0], [2, 3]]
    out_c, out_bin = export_c_and_bin(tile_map, 2, 2, temp_dir, "test_level")
    
    assert os.path.exists(out_c)
    assert os.path.exists(out_bin)
    
    assert os.path.getsize(out_bin) == 4
    with open(out_bin, "rb") as bf:
        assert list(bf.read()) == [1, 0, 2, 3]
        
    with open(out_c, "r") as cf:
        c_content = cf.read()
        assert "UBYTE mapping_test_level[4]" in c_content
        assert "1, 0" in c_content
        assert "2, 3" in c_content

def test_generate_tilemap_full(create_rgb_png, create_object_sprite_sheet, temp_dir):
    img_path = create_rgb_png("stage.png", size=(32, 32))
    sheet_path = create_object_sprite_sheet("objects.png", tile_size=(16, 16))
    
    obj_stage_path = os.path.join(os.path.dirname(img_path), "stage-objects.png")
    obj_img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    obj_img.save(obj_stage_path)
    
    generate_tilemap(img_path, temp_dir, tile_width=16, tile_height=16, scale=2, tolerance=100, objects_sprite=sheet_path)
    
    expected_png = os.path.join(temp_dir, "stage_tilemap.png")
    expected_c = os.path.join(temp_dir, "stage.c")
    expected_bin = os.path.join(temp_dir, "stage.bin")
    
    assert os.path.exists(expected_png)
    assert os.path.exists(expected_c)
    assert os.path.exists(expected_bin)

def test_generate_tilemap_objects_exception(create_rgb_png, create_object_sprite_sheet, temp_dir):
    # Covers lines 208-211: exception raised when opening objects stage image
    img_path = create_rgb_png("stage_err.png", size=(32, 32))
    sheet_path = create_object_sprite_sheet("objects_err.png", tile_size=(16, 16))
    
    obj_stage_path = os.path.join(os.path.dirname(img_path), "stage_err-objects.png")
    obj_img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    obj_img.save(obj_stage_path)
    
    # We mock Image.open to fail only when opening the -objects image
    original_open = Image.open
    def mock_open(fp, *args, **kwargs):
        if "-objects.png" in str(fp):
            raise ValueError("Corrupted objects stage image")
        return original_open(fp, *args, **kwargs)
        
    with patch('PIL.Image.open', side_effect=mock_open), \
         patch('builtins.print') as mock_print:
        generate_tilemap(img_path, temp_dir, tile_width=16, tile_height=16, scale=2, tolerance=100, objects_sprite=sheet_path)
        assert mock_print.called

def test_generate_tilemap_small_image(create_rgb_png, temp_dir):
    img_path = create_rgb_png("small.png", size=(8, 8))
    with pytest.raises(SystemExit) as exc_info:
        generate_tilemap(img_path, temp_dir, tile_width=16, tile_height=16, scale=1, tolerance=0)
    assert exc_info.value.code == 1

def test_generate_tilemap_file_not_found(temp_dir):
    with pytest.raises(SystemExit) as exc_info:
        generate_tilemap("nonexistent.png", temp_dir, 16, 16, 1, 0)
    assert exc_info.value.code == 1

def test_generate_tilemap_generic_exception(temp_dir, monkeypatch):
    def mock_open(*args, **kwargs):
        raise ValueError("Simulated failure")
    monkeypatch.setattr(Image, "open", mock_open)
    
    with pytest.raises(SystemExit) as exc_info:
        generate_tilemap("stage.png", temp_dir, 16, 16, 1, 0)
    assert exc_info.value.code == 1

def test_parser_error():
    parser = TableHelpParser()
    with patch('builtins.print'), pytest.raises(SystemExit) as exc_info:
        parser.error("Simulated error")
    assert exc_info.value.code == 2
    
def test_parser_help():
    parser = TableHelpParser()
    with patch('builtins.print') as mock_print:
        parser.print_help()
        assert mock_print.called

def test_collision_main(create_rgb_png, temp_dir):
    img_path = create_rgb_png("stage.png", size=(32, 32))
    
    test_args = ["generate_collision_map.py", img_path, temp_dir, "--tile-width", "16", "--tile-height", "16", "--tolerance", "100"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    expected_c = os.path.join(temp_dir, "stage.c")
    assert os.path.exists(expected_c)
