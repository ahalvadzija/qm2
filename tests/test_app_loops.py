from unittest.mock import patch 
from qm2.app import _handle_questions_submenu, _handle_csv_to_json

def test_handle_questions_submenu_full_loop():
    """Covers the loop in the questions submenu (Lines 163-184)."""
    questions = [{"question": "Q1", "options": ["A"], "answer": "A"}]
    
    with patch('questionary.select') as mock_select, \
         patch('qm2.app.show_questions_paginated') as mock_show:
        
        # Simulate: User clicks 'Show all', then 'Back' to exit the while loop
        mock_select.return_value.ask.side_effect = ["📚 Show all questions", "↩ Back"]
        
        result = _handle_questions_submenu("test_file.json", questions)
        
        # Verify result and call counts
        assert result == questions
        assert mock_show.call_count == 1
        assert mock_select.call_count == 2

def test_handle_csv_to_json_full_process():
    """Covers lines 336-364: CSV to JSON tool process loop."""
    # Mock os.listdir to simulate the presence of a CSV file
    with patch('os.listdir', return_value=["data.csv"]), \
         patch('questionary.select') as mock_select, \
         patch('rich.prompt.Prompt.ask', return_value="New Category"), \
         patch('qm2.app.core_csv_to_json') as mock_conv, \
         patch('qm2.app.categories_add') as mock_add, \
         patch('qm2.app.is_file_valid', return_value=True), \
         patch('rich.console.Console.print'):
        
        # side_effect ensures we trigger the logic and then exit the while loop
        mock_select.return_value.ask.side_effect = ["data.csv", "↩ Back"]
        
        _handle_csv_to_json()
        
        # Verify that internal functions within the loop were called
        assert mock_select.called
        assert mock_conv.called
        assert mock_add.called