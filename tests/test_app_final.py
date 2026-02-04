# tests/test_app_loops_final.py
import pytest
from unittest.mock import patch, MagicMock
from qm2.app import _handle_questions_submenu

def test_handle_questions_submenu_full_coverage():
    """Targets app.py lines 163-184: All branches in the submenu."""
    questions = [{"question": "Q1", "options": ["A"], "answer": "A"}]
    
    with patch('questionary.select') as mock_select, \
         patch('qm2.app.show_questions_paginated'), \
         patch('rich.prompt.Prompt.ask', side_effect=["1", "1"]), \
         patch('qm2.app.edit_question_by_index'), \
         patch('qm2.app.delete_question_by_index'), \
         patch('qm2.app.get_questions', return_value=questions), \
         patch('qm2.app.save_json'), \
         patch('rich.console.Console.print'):
        
        # Sequence of user choices to hit different branches
        mock_select.return_value.ask.side_effect = [
            "📚 Show all questions", 
            "🔢 Edit by number",
            "🔢 Delete by number",
            "💾 Save questions",
            "↩ Back"
        ]
        
        _handle_questions_submenu("dummy.json", questions)
        assert mock_select.call_count == 5