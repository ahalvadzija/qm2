import json
from unittest.mock import patch
from qm2.core.questions import delete_question_by_index, edit_question_by_index

def test_delete_by_index_logic(tmp_path):
    """
    Test deletion logic to hit coverage and verify 1-based to 0-based conversion.
    Targets delete_question_by_index and _delete_question_core.
    """
    # 1. Create a temporary JSON file
    test_file = tmp_path / "questions.json"
    initial_data = [
        {"question": "Q1", "type": "multiple"},
        {"question": "Q2", "type": "multiple"}
    ]
    test_file.write_text(json.dumps(initial_data))

    # 2. Patch save_json to actually update our temp file during the test
    # and patch console to avoid cluttering the output
    with patch('qm2.core.questions.save_json', side_effect=lambda p, d: test_file.write_text(json.dumps(d)) or True), \
         patch('qm2.core.questions.console'):
        
        # Test valid deletion (User inputs 1 to delete Q1)
        delete_question_by_index(str(test_file), 1)
        
        # Verify result
        updated_data = json.loads(test_file.read_text())
        assert len(updated_data) == 1
        assert updated_data[0]["question"] == "Q2"

        # Test invalid index (out of range) to hit error branches
        delete_question_by_index(str(test_file), 99)
        delete_question_by_index(str(test_file), 0)

def test_questions_index_errors_multiple():
    """
    Targets edit_question_by_index for 'multiple' type.
    Provides all 6 required prompts to avoid StopIteration/AssertionError.
    """
    sample_list = [{
        "type": "multiple", 
        "question": "Old 1", 
        "correct": "A", 
        "wrong_answers": ["B", "C", "D"]
    }]
    
    # Input sequence: New Question, New Correct, Count(3), Wrong1, Wrong2, Wrong3
    prompts = ["New Q", "New A", "3", "W1", "W2", "W3"]
    
    with patch('rich.prompt.Prompt.ask', side_effect=prompts), \
         patch('qm2.core.questions.save_json'), \
         patch('qm2.core.questions.console'):
        
        edit_question_by_index(sample_list, 1)
    
    assert sample_list[0]["question"] == "New Q"
    assert sample_list[0]["correct"] == "New A"
    assert len(sample_list[0]["wrong_answers"]) == 3

def test_questions_edit_invalid_index():
    """Hits the branch where an invalid index is provided to edit_question_by_index."""
    sample_list = [{"question": "Q1"}]
    
    with patch('qm2.core.questions.console') as mock_console:
        # Test non-numeric input
        edit_question_by_index(sample_list, "invalid")
        mock_console.print.assert_called_with("[yellow]⚠️ Invalid number.")
        
        # Test out of bounds
        edit_question_by_index(sample_list, 5)
        mock_console.print.assert_called_with("[yellow]⚠️ Number out of range. Allowed 1-1.")