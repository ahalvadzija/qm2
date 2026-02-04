import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from qm2.app import import_remote_file
from qm2.core.questions import delete_question_by_index, edit_question_by_index

def test_import_remote_file_network_failure():
    """Covers app.py lines 77-85: Scenario where the download fails due to network issues."""
    # Mocking user input for URL and target filename
    with patch('rich.prompt.Prompt.ask', side_effect=["http://nonexistent-url.com/q.json", "target_quiz"]), \
         patch('qm2.app.core_download_remote', side_effect=Exception("Connection Timeout")), \
         patch('rich.console.Console.print') as mock_print:
        
        import_remote_file()
        
        # Verify the error message was printed to the console
        mock_print.assert_any_call("[red]⚠️ Download failed: Connection Timeout")

def test_import_remote_file_invalid_json_after_download():
    """Covers app.py lines 125-131: Scenario where file is downloaded but fails JSON validation."""
    with patch('rich.prompt.Prompt.ask', side_effect=["http://test.com/q.json", "target_quiz"]), \
         patch('qm2.app.core_download_remote', return_value=Path("dummy.json")), \
         patch('qm2.app.is_file_valid', return_value=False), \
         patch('rich.console.Console.print') as mock_print:
        
        import_remote_file()
        
        # Verify that the invalid JSON message was displayed
        mock_print.assert_any_call("[red]❌ Downloaded JSON file is invalid. The file was not added.[/red]")

def test_questions_index_out_of_bounds_handling():
    """Covers questions.py lines 320-364: Handling invalid indices for deletion and editing."""
    questions = [{"question": "Is this a test?", "correct": "Yes", "wrong_answers": ["No"]}]
    
    # Mocking console to avoid cluttering output
    with patch('rich.console.Console.print'):
        # Test out of range deletion
        delete_question_by_index(questions, 99)
        
        # Corrected: Now passing only 2 arguments as expected by your function signature
        # We mock input inside if the function asks for data
        with patch('rich.prompt.Prompt.ask', return_value="Modified"):
            edit_question_by_index(questions, 10)
        
    # The list should remain unchanged because index 10 or 99 don't exist
    assert len(questions) == 1
    assert questions[0]["question"] == "Is this a test?"

def test_import_remote_file_user_cancellation():
    """Covers edge case where user might provide empty inputs for remote import."""
    with patch('rich.prompt.Prompt.ask', side_effect=["", ""]):
        # Test if function handles empty inputs gracefully
        try:
            import_remote_file()
        except Exception:
            pytest.fail("import_remote_file crashed on empty input")