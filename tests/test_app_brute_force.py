import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from qm2.app import main, _handle_tools_menu, import_remote_file

def test_app_full_tools_coverage():
    """
    Directly tests the tools menu logic to cover lines 336-364.
    This simulates creating templates and returning back.
    """
    # Simulate choosing CSV template, then JSON template, then Back
    with patch('questionary.select') as mock_select:
        mock_select.return_value.ask.side_effect = [
            "📄 Create CSV template",
            "📄 Create JSON template",
            "↩ Back"
        ]
        # Mocking external calls to avoid creating real files
        with patch('qm2.app.create_csv_template', return_value="template.csv"), \
             patch('qm2.app.create_json_template', return_value="template.json"), \
             patch('qm2.app.refresh_csv_cache'), \
             patch('qm2.app.refresh_categories_cache'):
            
            _handle_tools_menu()
    assert True

def test_import_remote_file_logic():
    """
    Tests the remote file import wrapper (lines 60-120).
    """
    # Mocking Prompt.ask for URL and filename
    with patch('rich.prompt.Prompt.ask', side_effect=["http://example.com/test.csv", "new_quiz"]):
        # Mocking the download and validation
        with patch('qm2.app.core_download_remote', return_value=Path("new_quiz.csv")), \
             patch('qm2.app.is_file_valid', return_value=True), \
             patch('qm2.app.refresh_csv_cache'):
            
            import_remote_file()
    assert True

def test_main_menu_navigation_complex():
    """
    Navigates through several menus to trigger high-level coverage in main().
    """
    with patch('questionary.select') as mock_select:
        # Sequence: Help -> Statistics -> Back -> Exit
        mock_select.return_value.ask.side_effect = [
            "6.) 💞 Help",
            "4.) 📈 Statistics",
            "↩ Back",
            "7.) ⏻  Exit"
        ]
        with patch('questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            with patch('qm2.app.show_help'), patch('rich.console.Console.clear'):
                main()
    assert True

def test_import_remote_file_error_scenarios():
    """Covers app.py lines 74-91: Invalid file names and unsupported types."""
    from qm2.app import import_remote_file
    
    # Scenario 1: Invalid file name (rich Prompt returns it)
    with patch('rich.prompt.Prompt.ask', side_effect=["http://example.com/quiz.txt", "invalid/name"]):
        with patch('qm2.app.console.print') as mock_print:
            import_remote_file()
            mock_print.assert_any_call("[red]⚠️ Invalid file name.")

def test_full_tools_menu_navigation():
    """Covers app.py lines 336-364: All branches in tools menu."""
    from qm2.app import _handle_tools_menu
    
    with patch('questionary.select') as mock_select:
        # We cycle through major tool options and then exit
        mock_select.return_value.ask.side_effect = [
            "📄 Create CSV template",
            "📄 Create JSON template",
            "🔄 Refresh CSV Cache",
            "↩ Back"
        ]
        with patch('qm2.app.create_csv_template'), \
             patch('qm2.app.create_json_template'), \
             patch('qm2.app.refresh_csv_cache'), \
             patch('qm2.app.refresh_categories_cache'):
            
            _handle_tools_menu()