import pytest
import sys
from unittest.mock import patch, MagicMock

from png_tools.rich_coverage import generate_rich_report, main

def test_rich_report_success():
    # Mock the coverage object and numbers to test the reporting logic and table generation
    mock_cov = MagicMock()
    
    mock_data = MagicMock()
    # Add: 100% file, 95% file, 70% file, a duplicate path, a broken path, and a non-src path (triggers line 78 continue)
    mock_data.measured_files.return_value = [
        "src/png_tools/cli.py",
        "src/png_tools/cli.py", # Duplicate
        "src/png_tools/generate_mask.py", # 95%
        "src/png_tools/tui.py", # 70%
        "src/png_tools/broken.py", # Raises exception
        "tests/test_cli.py" # Triggers line 78 continue
    ]
    mock_cov.get_data.return_value = mock_data
    
    # Setup number objects for each path
    mock_numbers_100 = MagicMock()
    mock_numbers_100.n_statements = 34
    mock_numbers_100.n_missing = 0
    mock_numbers_100.n_branches = 10
    mock_numbers_100.n_missing_branches = 0
    mock_numbers_100.n_partial_branches = 0
    mock_numbers_100.pc_covered = 100.0
    
    mock_numbers_95 = MagicMock()
    mock_numbers_95.n_statements = 100
    mock_numbers_95.n_missing = 5
    mock_numbers_95.n_branches = 10
    mock_numbers_95.n_missing_branches = 0
    mock_numbers_95.n_partial_branches = 0
    mock_numbers_95.pc_covered = 95.0
    
    mock_numbers_70 = MagicMock()
    mock_numbers_70.n_statements = 100
    mock_numbers_70.n_missing = 30
    mock_numbers_70.n_branches = 10
    mock_numbers_70.n_missing_branches = 0
    mock_numbers_70.n_partial_branches = 0
    mock_numbers_70.pc_covered = 70.0
    
    def mock_analyze(f):
        analysis = MagicMock()
        if "cli.py" in f:
            analysis.numbers = mock_numbers_100
        elif "generate_mask.py" in f:
            analysis.numbers = mock_numbers_95
        elif "tui.py" in f:
            analysis.numbers = mock_numbers_70
        elif "broken.py" in f:
            raise ValueError("Corrupt file metadata")
        return analysis
        
    mock_cov._analyze.side_effect = mock_analyze
    mock_cov.analysis2.return_value = ("some_file.py", [1, 2], [], [], "1-2")
    
    with patch('coverage.Coverage', return_value=mock_cov), \
         patch('rich.console.Console.print') as mock_print:
        generate_rich_report()
        assert mock_print.called

def test_rich_report_success_100_percent():
    # Mock single file at 100% coverage (triggers line 146 total cover green style)
    mock_cov = MagicMock()
    mock_data = MagicMock()
    mock_data.measured_files.return_value = ["src/png_tools/cli.py"]
    mock_cov.get_data.return_value = mock_data
    
    mock_numbers = MagicMock()
    mock_numbers.n_statements = 10
    mock_numbers.n_missing = 0
    mock_numbers.n_branches = 0
    mock_numbers.n_missing_branches = 0
    mock_numbers.n_partial_branches = 0
    mock_numbers.pc_covered = 100.0
    
    mock_analysis = MagicMock()
    mock_analysis.numbers = mock_numbers
    mock_cov._analyze.return_value = mock_analysis
    mock_cov.analysis2.return_value = ("src/png_tools/cli.py", [1], [], [], "")
    
    with patch('coverage.Coverage', return_value=mock_cov), \
         patch('rich.console.Console.print') as mock_print:
        generate_rich_report()
        assert mock_print.called

def test_rich_report_success_95_percent():
    # Mock single file at 95% coverage (triggers line 148 total cover yellow style)
    mock_cov = MagicMock()
    mock_data = MagicMock()
    mock_data.measured_files.return_value = ["src/png_tools/cli.py"]
    mock_cov.get_data.return_value = mock_data
    
    mock_numbers = MagicMock()
    mock_numbers.n_statements = 20
    mock_numbers.n_missing = 1
    mock_numbers.n_branches = 0
    mock_numbers.n_missing_branches = 0
    mock_numbers.n_partial_branches = 0
    mock_numbers.pc_covered = 95.0
    
    mock_analysis = MagicMock()
    mock_analysis.numbers = mock_numbers
    mock_cov._analyze.return_value = mock_analysis
    mock_cov.analysis2.return_value = ("src/png_tools/cli.py", [1], [], [], "")
    
    with patch('coverage.Coverage', return_value=mock_cov), \
         patch('rich.console.Console.print') as mock_print:
        generate_rich_report()
        assert mock_print.called

def test_rich_report_no_matched_files():
    # Mock only non-src files (triggers line 143 overall_cover = 100.0)
    mock_cov = MagicMock()
    mock_data = MagicMock()
    mock_data.measured_files.return_value = ["tests/test_cli.py"]
    mock_cov.get_data.return_value = mock_data
    
    with patch('coverage.Coverage', return_value=mock_cov), \
         patch('rich.console.Console.print') as mock_print:
        generate_rich_report()
        assert mock_print.called

def test_rich_report_no_data():
    # Mock coverage database having no data
    mock_cov = MagicMock()
    mock_cov.get_data.return_value = None
    
    with patch('coverage.Coverage', return_value=mock_cov), \
         patch('builtins.print'), \
         patch('rich.console.Console.print'):
         
        with pytest.raises(SystemExit) as exc_info:
            generate_rich_report()
            
        assert exc_info.value.code == 1

def test_rich_report_exception():
    # Mock coverage load throwing exception
    with patch('coverage.Coverage', side_effect=ValueError("Load failed")), \
         patch('builtins.print'), \
         patch('rich.console.Console.print'):
         
        with pytest.raises(SystemExit) as exc_info:
            generate_rich_report()
            
        assert exc_info.value.code == 1

def test_rich_report_main():
    with patch('png_tools.rich_coverage.generate_rich_report') as mock_report:
        main()
        assert mock_report.called
