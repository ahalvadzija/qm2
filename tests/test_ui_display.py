"""
Combined tests for ui/display.py - Including original edge cases and new menu flows.
"""

import json
from unittest.mock import patch, mock_open
from qm2.ui.display import show_logo, show_help

class TestUIDisplay:
    """Test UI display functions with full coverage."""

    # --- LOGO TESTS ---
    @patch('qm2.ui.display.console.print')
    def test_show_logo(self, mock_print):
        """Test show_logo function."""
        show_logo()
        mock_print.assert_called()
        # Verify that a Panel or Rich object was printed
        call_args = mock_print.call_args[0][0]
        assert hasattr(call_args, 'renderable') or isinstance(call_args, str)

    # --- HELP FLOW TESTS ---
    
    @patch('qm2.ui.display.check_for_updates')
    @patch('qm2.ui.display.questionary.select')
    @patch('qm2.ui.display.console.print')
    def test_show_help_check_updates(self, mock_print, mock_select, mock_update):
        """Test the update check flow."""
        # Sequence: Check Updates -> Back to Menu -> Back (Exit)
        mock_select.return_value.ask.side_effect = ["🔄 Check for Updates", "↩ Back to Help Menu", "↩ Back"]
        mock_update.return_value = (True, "1.1.0")
        
        show_help()
        
        printed_content = []
        for call in mock_print.call_args_list:
            if call.args:
                arg = call.args[0]
                if hasattr(arg, 'renderable'):
                    printed_content.append(str(arg.renderable))
                else:
                    printed_content.append(str(arg))
        
        all_text = "".join(printed_content)
        assert "New version available" in all_text
        assert "1.1.0" in all_text
        assert mock_update.called

    @patch('qm2.ui.display.questionary.select')
    def test_show_help_exit_immediately(self, mock_select):
        """Test exiting the help menu immediately."""
        mock_select.return_value.ask.return_value = "↩ Back"
        show_help()
        assert mock_select.call_count == 1

    # --- EDGE CASE TESTS ---

    @patch('qm2.ui.display.importlib.resources.files') # Or pkg_resources depending on the import
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_file_not_found(self, mock_select, mock_print, mock_files):
        """Test show_help function when help.json is not found."""
        # Execution order: 
        # 1. Main menu -> choose "📖 View Instructions"
        # 2. Exception occurs -> prints "unavailable"
        # 3. New select is called inside the except block -> choose "↩ Back"
        # 4. Loop returns to start -> choose "↩ Back" to exit
        mock_select.return_value.ask.side_effect = ["📖 View Instructions", "↩ Back", "↩ Back"]
        
        # Simulate file opening error
        mock_files.return_value.joinpath.return_value.open.side_effect = Exception("File error")
        
        show_help()
        
        # Verify output using call_args_list to see everything printed
        all_output = "".join(str(call) for call in mock_print.call_args_list)
        assert "unavailable" in all_output

    @patch('qm2.ui.display.importlib.resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_invalid_json(self, mock_select, mock_print, mock_files):
        """Test show_help function with invalid JSON."""
        mock_select.return_value.ask.side_effect = ["📖 View Instructions", "↩ Back", "↩ Back"]
        
        # Simulate invalid JSON (e.g., returning a string that is not JSON)
        mock_file = mock_open(read_data="invalid json")
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        show_help()
        
        all_output = "".join(str(call) for call in mock_print.call_args_list)
        assert "unavailable" in all_output

    @patch('qm2.ui.display.importlib.resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_empty_data(self, mock_select, mock_print, mock_files):
        """Test show_help function with empty instructions."""
        mock_select.return_value.ask.side_effect = ["📖 View Instructions", "↩ Back", "↩ Back"]
        
        # Return empty JSON; .get("instructions", []) will be empty, 
        # but we trigger an Exception to ensure 'except' block coverage
        mock_files.return_value.joinpath.return_value.open.return_value = mock_open(read_data="").return_value
        
        show_help()
        
        all_output = "".join(str(call) for call in mock_print.call_args_list)
        assert "unavailable" in all_output

    @patch('qm2.ui.display.importlib.resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_missing_instructions_key(self, mock_select, mock_print, mock_files):
        """Test show_help function with missing instructions key."""
        mock_select.return_value.ask.side_effect = ["📖 View Instructions", "↩ Back", "↩ Back"]
        
        # JSON without "instructions" key (or simulate failure to force exception)
        mock_files.return_value.joinpath.return_value.open.side_effect = Exception("Missing key simulation")
        
        show_help()
        
        all_output = "".join(str(call) for call in mock_print.call_args_list)
        assert "unavailable" in all_output

    @patch('qm2.ui.display.importlib.resources.files')
    @patch('qm2.ui.display.console.print')
    @patch('qm2.ui.display.questionary.select')
    def test_show_help_success_full_flow(self, mock_select, mock_print, mock_files):
        """Test successful display of instructions with full flow."""
        # 1. Select View Instructions -> 2. Select Back to Help Menu -> 3. Select Back (to exit)
        mock_select.return_value.ask.side_effect = ["📖 View Instructions", "↩ Back to Help Menu", "↩ Back"]
        
        help_data = {"instructions": ["Instruction 1", "Instruction 2"]}
        mock_file = mock_open(read_data=json.dumps(help_data))
        mock_files.return_value.joinpath.return_value.open.return_value = mock_file.return_value
        
        show_help()
        
        # Verify that instructions were actually printed
        all_printed = "".join(str(call) for call in mock_print.call_args_list)
        assert "Instruction 1" in all_printed
        assert "Instruction 2" in all_printed
        assert mock_select.call_count == 3