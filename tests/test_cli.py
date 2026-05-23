import pytest
import sys
from unittest.mock import patch, MagicMock

from png_tools.cli import main

def test_cli_no_args_tui_success():
    # If len(sys.argv) < 2, should import tui and run main
    test_args = ["png_tools"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('png_tools.tui.main') as mock_tui_main:
         
        with pytest.raises(SystemExit) as exc_info:
            main()
            
        assert exc_info.value.code == 0
        assert mock_tui_main.called

def test_cli_no_args_tui_import_error():
    # If len(sys.argv) < 2 and TUI cannot be imported (or fails to import), should write usage and exit(1)
    test_args = ["png_tools"]
    
    original_import = __import__
    def mock_import(name, *args, **kwargs):
        if "png_tools.tui" in name or name == "png_tools.tui":
            raise ImportError("No module named 'png_tools.tui'")
        return original_import(name, *args, **kwargs)
    
    with patch.object(sys, 'argv', test_args), \
         patch('builtins.__import__', side_effect=mock_import), \
         patch('builtins.print') as mock_print:
         
        with pytest.raises(SystemExit) as exc_info:
            main()
            
        assert exc_info.value.code == 1
        assert mock_print.called

def test_cli_command_mask():
    test_args = ["png_tools", "mask", "input.png", "output_dir"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('png_tools.cli.mask_main') as mock_mask_main:
         
        main()
        
        assert mock_mask_main.called
        # Check that 'mask' was popped and sys.argv was updated correctly
        assert sys.argv == ["png_tools mask", "input.png", "output_dir"]

def test_cli_command_preshift():
    test_args = ["png_tools", "preshift", "input.png", "output_dir"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('png_tools.cli.preshift_main') as mock_preshift_main:
         
        main()
        
        assert mock_preshift_main.called
        assert sys.argv == ["png_tools preshift", "input.png", "output_dir"]

def test_cli_command_plowman_map():
    test_args = ["png_tools", "plowman-map", "input.png", "output_dir"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('png_tools.cli.plowman_main') as mock_plowman_main:
         
        main()
        
        assert mock_plowman_main.called
        assert sys.argv == ["png_tools plowman-map", "input.png", "output_dir"]

def test_cli_command_pacman_map():
    test_args = ["png_tools", "pacman-map", "input.png", "output_dir"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('png_tools.cli.pacman_main') as mock_pacman_main:
         
        main()
        
        assert mock_pacman_main.called
        assert sys.argv == ["png_tools pacman-map", "input.png", "output_dir"]

def test_cli_command_cov():
    test_args = ["png_tools", "cov"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('png_tools.cli.cov_main') as mock_cov_main:
         
        main()
        
        assert mock_cov_main.called
        assert sys.argv == ["png_tools cov"]

def test_cli_command_unknown():
    test_args = ["png_tools", "unknown-cmd"]
    
    with patch.object(sys, 'argv', test_args), \
         patch('builtins.print') as mock_print:
         
        with pytest.raises(SystemExit) as exc_info:
            main()
            
        assert exc_info.value.code == 1
        assert mock_print.called

