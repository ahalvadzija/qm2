# tests/test_app_questions_logic.py
from unittest.mock import patch
from qm2.app import _handle_questions_submenu

def test_questions_submenu_display_and_back():
    """Covers lines 163-184: Testing 'Show all questions' and 'Back' loop."""
    filename = "dummy.json"
    questions = [{"question": "Test?", "options": ["Yes", "No"], "answer": "Yes"}]
    
    with patch('questionary.select') as mock_select, \
         patch('qm2.app.show_questions_paginated') as mock_show, \
         patch('rich.console.Console.print'):
        
        # Simulating: 1. User wants to see questions, 2. User wants to go back
        mock_select.return_value.ask.side_effect = ["📚 Show all questions", "↩ Back"]
        
        result = _handle_questions_submenu(filename, questions)
        
        assert mock_show.called
        assert result == questions
        assert mock_select.call_count == 2