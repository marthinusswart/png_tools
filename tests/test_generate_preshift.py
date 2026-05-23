import pytest
import os
import sys
from PIL import Image
from unittest.mock import patch

from png_tools.generate_preshift import generate_preshift, main

def test_generate_preshift_valid_indexed(create_indexed_png, temp_dir):
    input_path = create_indexed_png("sprite.png", size=(16, 16))
    output_path = os.path.join(temp_dir, "sprite_shifted.png")
    
    # Run generator with 4 shifts and a 16-pixel buffer
    generate_preshift(input_path, output_path, num_shifts=4, buffer_size=16, reverse_shift=False)
    
    assert os.path.exists(output_path)
    
    with Image.open(output_path) as out_img:
        # Width: 16 (original) + 16 (buffer) = 32
        # Height: 16 (original) * 4 (shifts) = 64
        assert out_img.size == (32, 64)
        assert out_img.mode == 'P'
        
        # Load palette of original and output
        with Image.open(input_path) as orig_img:
            assert out_img.getpalette()[:9] == orig_img.getpalette()[:9]

def test_generate_preshift_reverse(create_indexed_png, temp_dir):
    input_path = create_indexed_png("sprite_rev.png", size=(16, 16))
    output_path = os.path.join(temp_dir, "sprite_shifted_reverse.png")
    
    # Run generator in reverse shift mode
    generate_preshift(input_path, output_path, num_shifts=4, buffer_size=16, reverse_shift=True)
    
    assert os.path.exists(output_path)
    
    with Image.open(output_path) as out_img:
        assert out_img.size == (32, 64)
        assert out_img.mode == 'P'

def test_generate_preshift_reject_non_indexed(create_rgba_png, temp_dir):
    input_path = create_rgba_png("sprite_rgba.png")
    output_path = os.path.join(temp_dir, "sprite_rgba_shifted.png")
    
    # Must exit(1) when loading non-'P' mode image
    with pytest.raises(SystemExit) as exc_info:
        generate_preshift(input_path, output_path)
    assert exc_info.value.code == 1

def test_generate_preshift_file_not_found(temp_dir):
    with pytest.raises(SystemExit) as exc_info:
        generate_preshift("nonexistent.png", os.path.join(temp_dir, "out.png"))
    assert exc_info.value.code == 1

def test_generate_preshift_generic_exception(temp_dir, monkeypatch):
    def mock_open(*args, **kwargs):
        raise ValueError("Simulated open exception")
        
    monkeypatch.setattr(Image, "open", mock_open)
    
    with pytest.raises(SystemExit) as exc_info:
        generate_preshift("sprite.png", os.path.join(temp_dir, "out.png"))
    assert exc_info.value.code == 1

def test_generate_preshift_main_forward(create_indexed_png, temp_dir):
    input_path = create_indexed_png("main_sprite.png")
    
    test_args = ["generate_preshift.py", input_path, temp_dir, "--shifts", "4", "--buffer", "16"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    expected_output = os.path.join(temp_dir, "main_sprite_shifted.png")
    assert os.path.exists(expected_output)

def test_generate_preshift_main_reverse(create_indexed_png, temp_dir):
    input_path = create_indexed_png("main_sprite_rev.png")
    
    test_args = ["generate_preshift.py", input_path, temp_dir, "--shifts", "4", "--buffer", "16", "--reverse"]
    with patch.object(sys, 'argv', test_args):
        main()
        
    expected_output = os.path.join(temp_dir, "main_sprite_rev_shifted_reverse.png")
    assert os.path.exists(expected_output)
