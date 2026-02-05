"""
Simple tests for ui/display.py to improve coverage.
"""

import json
from unittest.mock import patch, mock_open

from qm2.ui.display import show_logo, show_help


class TestUIDisplay:
    """Test UI display functions."""
    
    @patch('qm2.ui.display.console.print')
    def test_show_logo(self, mock_print):
        """Test show_logo function."""
        show_logo()
        mock_print.assert_called_once()
        
        # Check that Panel was created (Panel object passed to print)
        call_args = mock_print.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(call_args, Panel)
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_success(self, mock_select, mock_print, mock_files):
        """Test show_help function with valid help.json."""
        # Mock help.json content
        help_data = {
            "instructions": [
                "Use arrow keys to navigate",
                "Press Enter to select",
                "Press Ctrl+C to quit"
            ]
        }
        
        # Mock file reading with proper context manager
        mock_file = mock_open(read_data=json.dumps(help_data))
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        # Mock questionary select
        mock_select.return_value.ask.return_value = "↩ Back"
        
        show_help()
        
        # Verify help was displayed
        mock_print.assert_called()
        mock_select.assert_called_once()
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    def test_show_help_file_not_found(self, mock_print, mock_files):
        """Test show_help function when help.json is not found."""
        # Mock FileNotFoundError
        mock_files.return_value.joinpath.return_value.open.side_effect = FileNotFoundError("Help file not found")
        
        show_help()
        
        # Verify error message was printed
        mock_print.assert_called_with("[red]⚠️ Help instructions unavailable or invalid.")
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    def test_show_help_invalid_json(self, mock_print, mock_files):
        """Test show_help function with invalid JSON."""
        # Mock invalid JSON
        mock_file = mock_open(read_data="invalid json")
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        show_help()
        
        # Verify error message was printed
        mock_print.assert_called_with("[red]⚠️ Help instructions unavailable or invalid.")
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    def test_show_help_empty_data(self, mock_print, mock_files):
        """Test show_help function with empty help data."""
        # Mock empty JSON
        mock_file = mock_open(read_data="{}")
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        show_help()
        
        # Verify error message was printed
        mock_print.assert_called_with("[red]⚠️ Help instructions unavailable or invalid.")
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    def test_show_help_missing_instructions(self, mock_print, mock_files):
        """Test show_help function when instructions key is missing."""
        # Mock JSON without instructions
        help_data = {"title": "Help", "version": "1.0"}
        
        mock_file = mock_open(read_data=json.dumps(help_data))
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        show_help()
        
        # Verify error message was printed
        mock_print.assert_called_with("[red]⚠️ Help instructions unavailable or invalid.")
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_with_instructions(self, mock_select, mock_print, mock_files):
        """Test show_help function displays instructions correctly."""
        # Mock help.json with instructions
        help_data = {
            "instructions": [
                "First instruction",
                "Second instruction",
                "Third instruction"
            ]
        }
        
        # Mock file reading with proper context manager
        mock_file = mock_open(read_data=json.dumps(help_data))
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        mock_select.return_value.ask.return_value = "↩ Back"
        
        show_help()
        
        # Verify instructions were printed (at least rule + instructions)
        assert mock_print.call_count >= 4  # rule + 3 instructions
        
        # Verify questionary was called
        mock_select.assert_called_once()
    
    @patch('qm2.ui.display.pkg_resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_general_exception(self, mock_select, mock_print, mock_files):
        """Test show_help function with general exception."""
        # Mock general exception
        mock_files.return_value.joinpath.return_value.open.side_effect = Exception("General error")
        
        show_help()
        
        # Verify error message was printed
        mock_print.assert_called_with("[red]⚠️ Help instructions unavailable or invalid.")
        mock_select.assert_not_called()
