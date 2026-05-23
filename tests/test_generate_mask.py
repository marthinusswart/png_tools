import pytest
import os
import sys
from PIL import Image
from unittest.mock import patch, MagicMock

from png_tools.generate_mask import generate_mask, main, TableHelpParser

def test_generate_mask_indexed(create_indexed_png, temp_dir):
    input_path = create_indexed_png("test_p.png")
    
    # Run the generator
    generate_mask(input_path, temp_dir)
    
    # Check that mask was generated
    expected_output_path = os.path.join(temp_dir, "test_p_mask.png")
    assert os.path.exists(expected_output_path)
    
    # Verify contents of the generated mask
    with Image.open(expected_output_path) as mask_img:
        assert mask_img.size == (16, 16)
        assert mask_img.mode == 'P'
        
        # Load pixels of original and mask
        with Image.open(input_path) as orig_img:
            orig_pix = orig_img.load()
            mask_pix = mask_img.load()
            
            for y in range(16):
                for x in range(16):
                    # In conftest: index 0 (transparent), 1 (white), 2 (red)
                    # If index 0 -> mask should be 0
                    # If index 1 or 2 -> mask should be 1
                    if orig_pix[x, y] == 0:
                        assert mask_pix[x, y] == 0
                    else:
                        assert mask_pix[x, y] == 1

def test_generate_mask_rgba(create_rgba_png, temp_dir):
    input_path = create_rgba_png("test_rgba.png")
    
    # Run the generator
    generate_mask(input_path, temp_dir)
    
    # Check output
    expected_output_path = os.path.join(temp_dir, "test_rgba_mask.png")
    assert os.path.exists(expected_output_path)
    
    with Image.open(expected_output_path) as mask_img:
        assert mask_img.mode == 'P'
        mask_pix = mask_img.load()
        
        with Image.open(input_path) as orig_img:
            orig_pix = orig_img.load()
            for y in range(16):
                for x in range(16):
                    # Check alpha channel (index 3)
                    # If alpha is 0 -> mask 0, else mask 1
                    if orig_pix[x, y][3] == 0:
                        assert mask_pix[x, y] == 0
                    else:
                        assert mask_pix[x, y] == 1

def test_generate_mask_rgb(create_rgb_png, temp_dir):
    input_path = create_rgb_png("test_rgb.png")
    
    # Run the generator
    generate_mask(input_path, temp_dir)
    
    expected_output_path = os.path.join(temp_dir, "test_rgb_mask.png")
    assert os.path.exists(expected_output_path)
    
    with Image.open(expected_output_path) as mask_img:
        mask_pix = mask_img.load()
        with Image.open(input_path) as orig_img:
            orig_pix = orig_img.load()
            for y in range(16):
                for x in range(16):
                    # Pure black (0,0,0) -> mask 0, else mask 1
                    if orig_pix[x, y] == (0, 0, 0):
                        assert mask_pix[x, y] == 0
                    else:
                        assert mask_pix[x, y] == 1

def test_generate_mask_grayscale_int(tmp_path, temp_dir):
    # Grayscale image (mode 'L') will return integer pixels
    img = Image.new('L', (8, 8), color=0)
    pixels = img.load()
    pixels[2, 2] = 255
    input_path = str(tmp_path / "test_gray.png")
    img.save(input_path)
    
    generate_mask(input_path, temp_dir)
    
    expected_output_path = os.path.join(temp_dir, "test_gray_mask.png")
    assert os.path.exists(expected_output_path)
    
    with Image.open(expected_output_path) as mask_img:
        mask_pix = mask_img.load()
        assert mask_pix[2, 2] == 1
        assert mask_pix[0, 0] == 0

def test_generate_mask_file_not_found(temp_dir):
    # Should call sys.exit(1) on FileNotFoundError
    with pytest.raises(SystemExit) as exc_info:
        generate_mask("nonexistent_file.png", temp_dir)
    assert exc_info.value.code == 1

def test_generate_mask_generic_exception(temp_dir, monkeypatch):
    # Mock Image.open to raise a generic Exception
    def mock_open(*args, **kwargs):
        raise ValueError("Simulated image corruption")
    
    monkeypatch.setattr(Image, "open", mock_open)
    
    with pytest.raises(SystemExit) as exc_info:
        generate_mask("some_file.png", temp_dir)
    assert exc_info.value.code == 1

def test_parser_help():
    parser = TableHelpParser()
    # Mock print to verify it runs without errors
    with patch('builtins.print') as mock_print:
        parser.print_help()
        assert mock_print.called

def test_parser_error():
    parser = TableHelpParser()
    with patch('builtins.print'), pytest.raises(SystemExit) as exc_info:
        parser.error("Test error message")
    assert exc_info.value.code == 2

def test_generate_mask_main(create_indexed_png, temp_dir):
    input_path = create_indexed_png("main_test.png")
    
    test_args = ["generate_mask.py", input_path, temp_dir]
    with patch.object(sys, 'argv', test_args):
        main()
        
    expected_output_path = os.path.join(temp_dir, "main_test_mask.png")
    assert os.path.exists(expected_output_path)
