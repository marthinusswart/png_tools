import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from png_tools.tui import FormGroup, LogRedirector, PNGToolsTUIApp, main

# Define a mock log widget to test LogRedirector
class MockLogWidget:
    def __init__(self):
        self.lines = []
    def write(self, data):
        self.lines.append(data)

def test_log_redirector():
    widget = MockLogWidget()
    redirector = LogRedirector(widget)
    
    # Test basic writing
    redirector.write("Hello World\n")
    assert widget.lines == ["Hello World"]
    
    # Test ANSI escape code stripping
    widget.lines.clear()
    redirector.write("\033[96mCyan Text\033[0m\n")
    assert widget.lines == ["Cyan Text"]
    
    # Test buffering until newline
    widget.lines.clear()
    redirector.write("Part 1 ")
    assert len(widget.lines) == 0
    redirector.write("Part 2\n")
    assert widget.lines == ["Part 1 Part 2"]
    
    # Test flush (covers line 54)
    redirector.flush()

def test_form_group():
    fg = FormGroup(border_title="My Test Title")
    assert fg.border_title == "My Test Title"

def test_tui_app_scan_files_nonexistent():
    # Covers line 255 (png_dir does not exist)
    with patch('pathlib.Path.exists', return_value=False):
        app = PNGToolsTUIApp()
        assert len(app.png_files) == 0

def test_tui_app_unit_methods():
    app = PNGToolsTUIApp()
    
    # Test parse_px_int
    assert app.parse_px_int(12) == 12
    assert app.parse_px_int("16px") == 16
    assert app.parse_px_int("  32px  ") == 32
    assert app.parse_px_int("invalid") == 0
    
    # Mock some attributes to test auto-configuration guessing logic
    app.input_png = MagicMock()
    app.select_tool = MagicMock()
    app.input_output_dir = MagicMock()
    app.info_label = MagicMock()
    app.analysis_log = MagicMock()
    
    # Guess tool for "sprite"
    app.auto_configure(Path("png/pacman-Sprite-0001.png"))
    assert app.select_tool.value == "preshift"
    assert app.input_output_dir.value == "png"
    
    # Guess tool for "stage"
    app.auto_configure(Path("png/stage-0001.png"))
    assert app.select_tool.value == "pacman-map"
    assert app.input_output_dir.value == "collision"
    
    # Guess tool for "stage-plowman" (use existing plowman_tiles.png but mock name with "plowman" and "stage")
    with patch('pathlib.Path.stem', "plowman_stage"):
        app.auto_configure(Path("png/plowman_tiles.png"))
        assert app.select_tool.value == "plowman-map"
        assert app.input_output_dir.value == "collision"
    
    # Guess tool for "tiles"
    app.auto_configure(Path("png/pacman_tiles.png"))
    assert app.select_tool.value == "mask"
    assert app.input_output_dir.value == "png"

def test_tui_app_list_navigation():
    # Covers lines 409, 417, 424 (on_list_view_selected, handle_list_selection, redundant triggers)
    app = PNGToolsTUIApp()
    app.png_files = [Path("png/pacman_tiles.png")]
    app.input_png = MagicMock()
    app.input_png.value = ""
    app.select_tool = MagicMock()
    app.input_output_dir = MagicMock()
    app.info_label = MagicMock()
    app.analysis_log = MagicMock()
    
    # Message has no item (line 417)
    message_none = MagicMock()
    message_none.item = None
    app.on_list_view_selected(message_none)
    
    # Message has item (line 409)
    item = MagicMock()
    item.id = "png_0"
    message_item = MagicMock()
    message_item.item = item
    app.on_list_view_selected(message_item)
    app.input_png.value = str(app.png_files[0])
    
    # Message has item with redundant path (line 424)
    app.on_list_view_selected(message_item)

def test_tui_app_auto_configure_exception():
    # Covers lines 461-463 (Image open exception in auto_configure)
    app = PNGToolsTUIApp()
    app.input_png = MagicMock()
    app.select_tool = MagicMock()
    app.input_output_dir = MagicMock()
    app.info_label = MagicMock()
    app.analysis_log = MagicMock()
    
    with patch('PIL.Image.open', side_effect=ValueError("Corrupt")):
        app.auto_configure(Path("png/pacman_tiles.png"))
        assert app.info_label.update.called

def test_guess_objects_sheet():
    app = PNGToolsTUIApp()
    app.input_png = MagicMock()
    app.input_objects = MagicMock()
    
    # Test empty input_png (covers line 502)
    app.input_png.value = ""
    app.guess_objects_sheet()
    
    # Test pacman mapping
    app.input_png.value = "png/stage-0001.png"
    app.select_tool = MagicMock()
    app.select_tool.value = "pacman-map"
    app.guess_objects_sheet()
    assert app.input_objects.value == "png/pacman_map_objects.png"
    
    # Test plowman mapping
    app.select_tool.value = "plowman-map"
    app.guess_objects_sheet()
    assert app.input_objects.value == "png/plowman_map_objects.png"
    
    # Test tool not in pacman/plowman, guess path nonexistent (covers lines 512-514)
    app.select_tool.value = "mask"
    app.input_png.value = "png/other.png"
    app.guess_objects_sheet()
    assert app.input_objects.value == "png/pacman_map_objects.png"

def test_on_select_changed_none():
    # Covers line 485 (value is None in on_select_changed)
    app = PNGToolsTUIApp()
    app.select_tool = MagicMock()
    event = MagicMock()
    event.select = app.select_tool
    event.value = None
    app.on_select_changed(event)

def test_action_run_tool_nonexistent():
    # Covers lines 540-541 (PNG target nonexistent in action_run_tool)
    app = PNGToolsTUIApp()
    app.input_png = MagicMock()
    app.input_png.value = "nonexistent.png"
    app.execution_log = MagicMock()
    app.action_run_tool()
    assert app.execution_log.write.called

def test_action_run_tool_exception():
    # Covers lines 588-592 (Exception print inside action_run_tool)
    app = PNGToolsTUIApp()
    app.input_png = MagicMock()
    app.input_png.value = "png/pacman_tiles.png"
    app.select_tool = MagicMock()
    app.select_tool.value = "mask"
    app.input_output_dir = MagicMock()
    app.input_output_dir.value = "png"
    app.execution_log = MagicMock()
    
    with patch('png_tools.tui.generate_mask', side_effect=ValueError("Test crash")):
        app.action_run_tool()
        assert app.execution_log.write.called

def test_action_analyze_file_nonexistent():
    # Covers lines 601-602 (PNG target nonexistent in action_analyze_file)
    app = PNGToolsTUIApp()
    app.input_png = MagicMock()
    app.input_png.value = "nonexistent.png"
    app.execution_log = MagicMock()
    app.action_analyze_file()
    assert app.execution_log.write.called

def test_on_button_pressed():
    # Covers lines 519-522 (on_button_pressed)
    app = PNGToolsTUIApp()
    event = MagicMock()
    
    event.button.id = "btn-run"
    with patch.object(app, 'action_run_tool') as mock_run:
        app.on_button_pressed(event)
        assert mock_run.called
        
    event.button.id = "btn-analyze"
    with patch.object(app, 'action_analyze_file') as mock_analyze:
        app.on_button_pressed(event)
        assert mock_analyze.called

def test_action_quit():
    # Covers line 675 (action_quit)
    app = PNGToolsTUIApp()
    with patch.object(app, 'exit') as mock_exit:
        app.action_quit()
        assert mock_exit.called

def test_tui_main():
    # Covers lines 679-680 (main run loop)
    with patch('png_tools.tui.PNGToolsTUIApp.run') as mock_run:
        main()
        assert mock_run.called

@pytest.mark.asyncio
async def test_tui_integration():
    # Run a full integration test of the textual app in a virtual terminal
    app = PNGToolsTUIApp()
    async with app.run_test() as pilot:
        # Check that TUI initialized successfully
        assert app.title == "PNG Tools Suite TUI"
        assert app.query_one("#file-list") is not None
        assert app.query_one("#info-panel") is not None
        
        # Test default tool choice
        assert app.select_tool.value == "mask"
        
        # Test switching tool selection
        app.select_tool.value = "preshift"
        await pilot.pause()
        assert app.content_switcher.current == "switch-preshift"
        assert app.input_output_dir.value == "png"
        
        app.select_tool.value = "plowman-map"
        await pilot.pause()
        assert app.content_switcher.current == "switch-collision"
        assert app.input_output_dir.value == "collision"
        
        # Test mock execution triggers
        with patch('png_tools.tui.generate_mask') as mock_mask, \
             patch('png_tools.tui.generate_preshift') as mock_preshift, \
             patch('png_tools.tui.plowman_generate_tilemap') as mock_plowman_tilemap, \
             patch('png_tools.tui.pacman_generate_tilemap') as mock_pacman_tilemap:
             
             # Set input PNG and run tool
             app.input_png.value = "png/pacman_tiles.png"
             app.select_tool.value = "mask"
             
             # Click run button or press key R
             await pilot.press("r")
             assert mock_mask.called
             
             # Switch to preshift and click run button
             app.select_tool.value = "preshift"
             await pilot.press("r")
             assert mock_preshift.called
             
             # Switch to plowman and click run button
             app.select_tool.value = "plowman-map"
             await pilot.press("r")
             assert mock_plowman_tilemap.called
             
             # Switch to pacman and click run button (covers line 584)
             app.select_tool.value = "pacman-map"
             await pilot.press("r")
             assert mock_pacman_tilemap.called
             
        # Test analyze action (non-destructive)
        # Mock PIL Image.open to avoid actual file read errors if any issues
        with patch('png_tools.tui.Image.open') as mock_image_open:
            mock_img = MagicMock()
            mock_img.size = (16, 16)
            mock_img.mode = "P"
            mock_img.info = {"transparency": 0}
            mock_image_open.return_value.__enter__.return_value = mock_img
            
            app.input_png.value = "png/pacman_tiles.png"
            
            # Analyze mask tool (covers mode P transparency output)
            app.select_tool.value = "mask"
            await pilot.press("a")
            assert len(app.analysis_log.lines) > 0
            
            # Analyze mask (RGBA mode) (covers line 627)
            mock_img.mode = "RGBA"
            await pilot.press("a")
            
            # Analyze mask (RGB mode) (covers line 630)
            mock_img.mode = "RGB"
            await pilot.press("a")
            
            # Analyze preshift (indexed mode P) (covers line 635)
            app.select_tool.value = "preshift"
            mock_img.mode = "P"
            await pilot.press("a")
            
            # Analyze preshift (non-indexed mode RGBA) (covers line 639)
            mock_img.mode = "RGBA"
            await pilot.press("a")
            
            # Analyze pacman-map (perfect fit dimensions) (covers line 659)
            app.select_tool.value = "pacman-map"
            mock_img.size = (16, 16)
            app.input_objects.value = ""
            await pilot.press("a")
            
            # Analyze pacman-map (Size warning, objects sheet not found warning) (covers lines 656-657, 665)
            mock_img.size = (17, 17) # Leftover spaces
            app.input_objects.value = "nonexistent.png"
            await pilot.press("a")
            
            # Test exceptions inside analyze_file (covers lines 671-672)
            mock_image_open.side_effect = ValueError("Corrupt file")
            await pilot.press("a")
