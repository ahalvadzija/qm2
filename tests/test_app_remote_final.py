# tests/test_app_remote_final.py
import pytest
from unittest.mock import patch
from qm2.app import import_remote_file

def test_import_remote_file_invalid_name():
    """Targets line 84-85: Invalid filename check."""
    with patch('rich.prompt.Prompt.ask', side_effect=["http://url.com/q.json", "!!!invalid!!!"]), \
         patch('rich.console.Console.print') as mock_print:
        
        import_remote_file()
        mock_print.assert_any_call("[red]⚠️ Invalid file name.")

def test_import_remote_file_detection_failure():
    """Targets file type detection failure branch."""
    with patch('rich.prompt.Prompt.ask', side_effect=["http://url.com/unknown", "my_file"]), \
         patch('requests.head', side_effect=Exception("Connection Error")), \
         patch('questionary.select') as mock_select:
        
        # Simulate user choosing JSON manually when detection fails
        mock_select.return_value.ask.return_value = "JSON"
        # Force exit after detection to avoid deeper logic
        with patch('qm2.app.core_download_remote', side_effect=FileExistsError):
             import_remote_file()
             
        assert mock_select.called