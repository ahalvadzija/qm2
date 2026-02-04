import pytest
from unittest.mock import patch, MagicMock
import qm2.app as app

def test_questions_submenu_full_path():
    """Targets app.py lines 163-184: Navigation through ALL branches."""
    questions = [{"question": "Q1", "options": ["A"], "answer": "A"}]
    
    with patch('questionary.select') as mock_select, \
         patch('qm2.app.show_questions_paginated'), \
         patch('qm2.app.edit_question_by_index'), \
         patch('qm2.app.delete_question_by_index'), \
         patch('qm2.app.get_questions', return_value=questions), \
         patch('qm2.app.save_json'), \
         patch('qm2.app.create_question', return_value={"q": "new"}), \
         patch('rich.prompt.Prompt.ask', return_value="1"), \
         patch('rich.console.Console.print'):
        
        # We MUST end with '↩ Back' to close the while loop
        mock_select.return_value.ask.side_effect = [
            "📚 Show all questions",
            "🔢 Edit by number",
            "🔢 Delete by number",
            "➕ Add question",
            "💾 Save questions",
            "↩ Back" 
        ]
        
        app._handle_questions_submenu("dummy.json", questions)
        assert mock_select.call_count == 6

def test_handle_tools_menu_branches():
    """Targets app.py tools and conversion logic (336-364)."""
    with patch('questionary.select') as mock_select, \
         patch('os.listdir', return_value=["test.csv"]), \
         patch('qm2.app.is_file_valid', return_value=True), \
         patch('qm2.app._handle_csv_to_json'), \
         patch('qm2.app._handle_json_to_csv'), \
         patch('qm2.app.import_remote_file'):
        
        # Navigate through tools menu and then back
        mock_select.return_value.ask.side_effect = [
            "🧾 Convert CSV to JSON",
            "📤 Export JSON to CSV",
            "🌐 Import remote CSV/JSON",
            "↩ Back"
        ]
        
        app._handle_tools_menu()
        assert mock_select.call_count == 4