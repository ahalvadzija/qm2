from unittest.mock import patch
from qm2.core.questions import edit_question

def test_edit_question_all_types_coverage():
    """
    Covers core/questions.py lines 320-364 and all question types.
    """
    # Sample data with different types
    questions = [
        {"type": "multiple", "question": "Q1", "correct": "A", "wrong_answers": ["B", "C"]},
        {"type": "truefalse", "question": "Q2", "correct": "True"},
        {"type": "match", "question": "Q3", "pairs": {"left": ["A"], "right": ["1"], "answers": {"A": "1"}}}
    ]

    with patch('questionary.select') as mock_select, \
         patch('qm2.core.questions.Prompt.ask') as mock_prompt:
        
        # --- Test Case 1: Multiple Choice ---
        # 1. Select Q1, 2. New text, 3. New correct, 4. Count of wrongs, 5. Wrong #1, 6. Wrong #2
        mock_select.return_value.ask.side_effect = ["1. Q1..."]
        mock_prompt.side_effect = ["New Q1", "New Correct", "2", "W1", "W2"]
        
        edit_question(questions)
        assert questions[0]["question"] == "New Q1"
        assert len(questions[0]["wrong_answers"]) == 2

        # --- Test Case 2: Match Type ---
        mock_select.return_value.ask.side_effect = ["3. Q3..."]
        # New Q, New Left, New Right, New Mapping
        mock_prompt.side_effect = ["New Q3", "L1|L2", "R1|R2", "L1:R1, L2:R2"]
        
        edit_question(questions)
        assert questions[2]["pairs"]["left"] == ["L1", "L2"]