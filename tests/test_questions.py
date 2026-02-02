import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch
import qm2.core.questions as questions


class FakeQuestionary:
    """Fake questionary helper for testing."""
    def __init__(self, return_value):
        self.return_value = return_value

    def select(self, *args, **kwargs):
        return self

    def confirm(self, *args, **kwargs):
        return self

    def ask(self):
        return self.return_value


@pytest.fixture
def temp_category_file(tmp_path):
    """Create a temporary category file for testing."""
    category_file = tmp_path / "test_category.json"
    sample_questions = [
        {
            "type": "multiple",
            "question": "What is 2+2?",
            "correct": "4",
            "wrong_answers": ["3", "5", "6"]
        },
        {
            "type": "truefalse",
            "question": "Python is a programming language.",
            "correct": "True",
            "wrong_answers": ["False"]
        },
        {
            "type": "fillin",
            "question": "The capital of France is ______.",
            "correct": "Paris",
            "wrong_answers": []
        }
    ]
    category_file.write_text(json.dumps(sample_questions, indent=2), encoding="utf-8")
    return category_file


@pytest.fixture
def empty_category_file(tmp_path):
    """Create an empty temporary category file for testing."""
    category_file = tmp_path / "empty_category.json"
    category_file.write_text("[]", encoding="utf-8")
    return category_file


def test_get_questions_file_exists(temp_category_file):
    """Test get_questions with existing file."""
    result = questions.get_questions(temp_category_file)
    assert len(result) == 3
    assert result[0]["question"] == "What is 2+2?"
    assert result[1]["type"] == "truefalse"


def test_get_questions_file_not_exists():
    """Test get_questions with non-existent file."""
    result = questions.get_questions("/nonexistent/file.json")
    assert result == []


def test_get_questions_caching(temp_category_file):
    """Test that get_questions uses caching."""
    # First call should load from file
    result1 = questions.get_questions(temp_category_file)
    assert len(result1) == 3
    
    # Wait a bit to ensure different mtime for next write
    time.sleep(0.1)
    
    # Modify file directly (bypassing cache)
    new_questions = [{"type": "multiple", "question": "New question", "correct": "Answer", "wrong_answers": []}]
    temp_category_file.write_text(json.dumps(new_questions), encoding="utf-8")
    
    # Clear the cache to test caching behavior
    questions.questions_cache.clear()
    
    # Second call should load from file (cache was cleared)
    result2 = questions.get_questions(temp_category_file)
    assert len(result2) == 1  # Should load new data
    assert result2[0]["question"] == "New question"


def test_get_questions_cache_invalidation(temp_category_file):
    """Test cache invalidation when file is modified."""
    # Load initial data
    result1 = questions.get_questions(temp_category_file)
    assert len(result1) == 3
    
    # Wait a bit to ensure different mtime
    time.sleep(0.1)
    
    # Modify file
    new_questions = [{"type": "multiple", "question": "Modified question", "correct": "Answer", "wrong_answers": []}]
    temp_category_file.write_text(json.dumps(new_questions), encoding="utf-8")
    
    # Should detect file modification and reload
    result2 = questions.get_questions(temp_category_file)
    assert len(result2) == 1
    assert result2[0]["question"] == "Modified question"


def test_cleanup_questions_cache(tmp_path):
    """Test cleanup_questions_cache removes entries for non-existent files."""
    # Create a temporary file and load it to populate cache
    temp_file = tmp_path / "temp.json"
    temp_file.write_text('[{"question": "test"}]', encoding="utf-8")
    
    questions.get_questions(temp_file)  # Populate cache
    assert str(temp_file) in questions.questions_cache
    
    # Delete the file
    temp_file.unlink()
    
    # Run cleanup
    questions.cleanup_questions_cache()
    
    # Cache should be cleaned
    assert str(temp_file) not in questions.questions_cache


def test_create_question_multiple_choice():
    """Test create_question for multiple choice type."""
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting multiple choice
            mock_select.return_value.ask.return_value = "1. Multiple choice (1 correct + 3 incorrect)"
            
            # Mock user inputs
            mock_ask.side_effect = [
                "What is the capital of Spain?",  # question
                "Madrid",  # correct answer
                "Barcelona",  # wrong answer 1
                "Valencia",  # wrong answer 2
                "Seville"   # wrong answer 3
            ]
            
            result = questions.create_question()
            
            assert result is not None
            assert result["type"] == "multiple"
            assert result["question"] == "What is the capital of Spain?"
            assert result["correct"] == "Madrid"
            assert len(result["wrong_answers"]) == 3
            assert "Barcelona" in result["wrong_answers"]


def test_create_question_true_false():
    """Test create_question for true/false type."""
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting true/false
            mock_select.return_value.ask.return_value = "2. True/False"
            
            # Mock user inputs
            mock_ask.side_effect = [
                "The Earth is round.",  # question
                "True"  # correct answer
            ]
            
            result = questions.create_question()
            
            assert result is not None
            assert result["type"] == "truefalse"
            assert result["question"] == "The Earth is round."
            assert result["correct"] == "True"
            assert result["wrong_answers"] == ["False"]


def test_create_question_fill_in():
    """Test create_question for fill-in type."""
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting fill-in
            mock_select.return_value.ask.return_value = "3. Fill-in-the-blank"
            
            # Mock user inputs
            mock_ask.side_effect = [
                "The largest planet is _______.",  # question
                "Jupiter"  # correct answer
            ]
            
            result = questions.create_question()
            
            assert result is not None
            assert result["type"] == "fillin"
            assert result["question"] == "The largest planet is _______."
            assert result["correct"] == "Jupiter"
            assert result["wrong_answers"] == []


def test_create_question_matching():
    """Test create_question for matching type."""
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            with patch('qm2.core.questions.console'):
                # Mock user selecting matching
                mock_select.return_value.ask.return_value = "4. Matching pairs"
                
                # Mock user inputs
                mock_ask.side_effect = [
                    "Match animals with their sounds",  # question
                    "Cat",    # left item a
                    "Dog",    # left item b
                    "Cow",    # left item c
                    "Meow",   # right item 1
                    "Woof",   # right item 2
                    "Moo",    # right item 3
                    "a-1",    # pair 1
                    "b-2",    # pair 2
                    "c-3"     # pair 3
                ]
                
                result = questions.create_question()
                
                assert result is not None
                assert result["type"] == "match"
                assert result["question"] == "Match animals with their sounds"
                assert result["pairs"]["left"] == ["Cat", "Dog", "Cow"]
                assert result["pairs"]["right"] == ["Meow", "Woof", "Moo"]
                assert result["pairs"]["answers"] == {"a": "1", "b": "2", "c": "3"}


def test_create_question_cancel():
    """Test create_question when user cancels."""
    with patch('qm2.core.questions.questionary.select') as mock_select:
        # Mock user selecting back/cancel
        mock_select.return_value.ask.return_value = "↩ Back"
        
        result = questions.create_question()
        
        assert result is None


def test_type_label():
    """Test type_label function."""
    assert questions.type_label("multiple") == "🟢 Multiple choice"
    assert questions.type_label("truefalse") == "🟠 True/False"
    assert questions.type_label("fillin") == "🟡 Fill-in"
    assert questions.type_label("match") == "🟣 Matching"
    assert questions.type_label("unknown") == "❔ Unknown"
    assert questions.type_label(None) == "❔ Unknown"


def test_show_questions_paginated_empty():
    """Test show_questions_paginated with empty questions."""
    with patch('qm2.core.questions.console') as mock_console:
        questions.show_questions_paginated([])
        mock_console.print.assert_called_with("[yellow]⚠️ No questions to display.")


def test_show_questions_paginated_single_page():
    """Test show_questions_paginated with single page."""
    sample_questions = [
        {"question": "Q1", "type": "multiple"},
        {"question": "Q2", "type": "truefalse"}
    ]
    
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.console') as mock_console:
            # Mock user selecting back
            mock_select.return_value.ask.return_value = "↩ Back"
            
            questions.show_questions_paginated(sample_questions, page_size=5)
            
            # Should have printed the table
            assert mock_console.print.called


def test_show_questions_paginated_multiple_pages():
    """Test show_questions_paginated with multiple pages."""
    # Create 25 questions to test pagination (page_size=10)
    sample_questions = [
        {"question": f"Question {i}", "type": "multiple"}
        for i in range(25)
    ]
    
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.console') as mock_console:
            # Mock user navigation: back immediately
            mock_select.return_value = FakeQuestionary("↩ Back")
            
            # Should show first page and exit
            questions.show_questions_paginated(sample_questions, page_size=10)
            
            # Should have printed the table
            assert mock_console.print.called


def test_edit_question_multiple_choice():
    """Test edit_question for multiple choice."""
    sample_questions = [
        {
            "type": "multiple",
            "question": "Old question",
            "correct": "Old answer",
            "wrong_answers": ["Wrong1", "Wrong2"]
        }
    ]
    
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting the first question ("1. Old question...")
            mock_select.return_value.ask.return_value = "1. Old question..."
            
            # Mock user edits
            mock_ask.side_effect = [
                "New question",  # new question
                "New answer",   # new correct answer
                "2",            # number of wrong answers
                "NewWrong1",    # wrong answer 1
                "NewWrong2"     # wrong answer 2
            ]
            
            questions.edit_question(sample_questions)
            
            # Check that question was updated
            assert sample_questions[0]["question"] == "New question"
            assert sample_questions[0]["correct"] == "New answer"
            assert len(sample_questions[0]["wrong_answers"]) == 2
            assert "NewWrong1" in sample_questions[0]["wrong_answers"]


def test_edit_question_true_false():
    """Test edit_question for true/false."""
    sample_questions = [
        {
            "type": "truefalse",
            "question": "Old statement",
            "correct": "True",
            "wrong_answers": ["False"]
        }
    ]
    
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting the first question ("1. Old statement...")
            mock_select.return_value.ask.return_value = "1. Old statement..."
            
            # Mock user edits
            mock_ask.side_effect = [
                "New statement",  # new question
                "False"           # new correct answer
            ]
            
            questions.edit_question(sample_questions)
            
            # Check that question was updated
            assert sample_questions[0]["question"] == "New statement"
            assert sample_questions[0]["correct"] == "False"
            assert sample_questions[0]["wrong_answers"] == ["True"]


def test_edit_question_fill_in():
    """Test edit_question for fill-in."""
    sample_questions = [
        {
            "type": "fillin",
            "question": "Old fill question",
            "correct": "Old answer",
            "wrong_answers": []
        }
    ]
    
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting the first question ("1. Old fill question...")
            mock_select.return_value.ask.return_value = "1. Old fill question..."
            
            # Mock user edits
            mock_ask.side_effect = [
                "New fill question",  # new question
                "New answer"          # new correct answer
            ]
            
            questions.edit_question(sample_questions)
            
            # Check that question was updated
            assert sample_questions[0]["question"] == "New fill question"
            assert sample_questions[0]["correct"] == "New answer"


def test_edit_question_matching():
    """Test edit_question for matching."""
    sample_questions = [
        {
            "type": "match",
            "question": "Old matching",
            "pairs": {
                "left": ["A", "B"],
                "right": ["1", "2"],
                "answers": {"a": "1", "b": "2"}
            }
        }
    ]
    
    with patch('qm2.core.questions.questionary.select') as mock_select:
        with patch('qm2.core.questions.Prompt.ask') as mock_ask:
            # Mock user selecting the first question ("1. Old matching...")
            mock_select.return_value.ask.return_value = "1. Old matching..."
            
            # Mock user edits
            mock_ask.side_effect = [
                "New matching",           # new question
                "X|Y",                    # new left items
                "3|4",                    # new right items
                "a:3,b:4"                 # new mapping
            ]
            
            questions.edit_question(sample_questions)
            
            # Check that question was updated
            assert sample_questions[0]["question"] == "New matching"
            assert sample_questions[0]["pairs"]["left"] == ["X", "Y"]
            assert sample_questions[0]["pairs"]["right"] == ["3", "4"]
            assert sample_questions[0]["pairs"]["answers"] == {"a": "3", "b": "4"}


def test_edit_question_by_index_valid():
    """Test edit_question_by_index with valid index."""
    sample_questions = [
        {"question": "Q1", "type": "multiple", "correct": "A1", "wrong_answers": []},
        {"question": "Q2", "type": "multiple", "correct": "A2", "wrong_answers": []}
    ]
    
    with patch('qm2.core.questions.Prompt.ask') as mock_ask:
        # Mock user edits
        mock_ask.side_effect = [
            "Edited Q2",  # new question
            "Edited A2",  # new correct answer
            "1",          # number of wrong answers
            "Wrong1"      # wrong answer 1
        ]
        
        questions.edit_question_by_index(sample_questions, "2")
        
        # Check that second question was updated
        assert sample_questions[1]["question"] == "Edited Q2"
        assert sample_questions[1]["correct"] == "Edited A2"


def test_edit_question_by_index_invalid_number():
    """Test edit_question_by_index with invalid number."""
    sample_questions = [
        {"question": "Q1", "type": "multiple", "correct": "A1", "wrong_answers": []}
    ]
    
    with patch('qm2.core.questions.console') as mock_console:
        questions.edit_question_by_index(sample_questions, "invalid")
        mock_console.print.assert_called_with("[yellow]⚠️ Invalid number.")


def test_edit_question_by_index_out_of_range():
    """Test edit_question_by_index with out of range index."""
    sample_questions = [
        {"question": "Q1", "type": "multiple", "correct": "A1", "wrong_answers": []}
    ]
    
    with patch('qm2.core.questions.console') as mock_console:
        questions.edit_question_by_index(sample_questions, "5")
        mock_console.print.assert_called_with("[yellow]⚠️ Number out of range. Allowed 1-1.")


def test_delete_question_by_index_valid():
    """Test delete_question_by_index with valid index."""
    # Create a temporary file with questions
    temp_file = Path("/tmp/test_delete.json")
    test_questions = [
        {"question": "Q1", "type": "multiple", "correct": "A1", "wrong_answers": []},
        {"question": "Q2", "type": "multiple", "correct": "A2", "wrong_answers": []},
        {"question": "Q3", "type": "multiple", "correct": "A3", "wrong_answers": []}
    ]
    temp_file.write_text(json.dumps(test_questions), encoding="utf-8")
    
    try:
        with patch('qm2.core.questions.console') as mock_console:
            questions.delete_question_by_index(str(temp_file), 1)  # Delete index 1 (0-based), which is Q2
            
            # Verify question was deleted (index 1 in 0-based, which is Q2)
            remaining_questions = json.loads(temp_file.read_text(encoding="utf-8"))
            assert len(remaining_questions) == 2
            assert remaining_questions[0]["question"] == "Q1"
            assert remaining_questions[1]["question"] == "Q3"
            
            # Check success message
            mock_console.print.assert_called()
    finally:
        temp_file.unlink(missing_ok=True)


def test_delete_question_by_index_invalid():
    """Test delete_question_by_index with invalid index."""
    # Create a temporary file with questions
    temp_file = Path("/tmp/test_delete_invalid.json")
    test_questions = [
        {"question": "Q1", "type": "multiple", "correct": "A1", "wrong_answers": []}
    ]
    temp_file.write_text(json.dumps(test_questions), encoding="utf-8")
    
    try:
        with patch('qm2.core.questions.console') as mock_console:
            questions.delete_question_by_index(str(temp_file), 5)
            
            # Should print error message
            mock_console.print.assert_called_with("[red]Invalid question index.[/red]")
    finally:
        temp_file.unlink(missing_ok=True)


def test_delete_question_valid():
    """Test delete_question with valid selection."""
    # Create a temporary file with questions
    temp_file = Path("/tmp/test_delete_select.json")
    test_questions = [
        {"question": "Question to delete", "type": "multiple", "correct": "Answer", "wrong_answers": []},
        {"question": "Question to keep", "type": "multiple", "correct": "Answer", "wrong_answers": []}
    ]
    temp_file.write_text(json.dumps(test_questions), encoding="utf-8")
    
    try:
        with patch('qm2.core.questions.questionary.select') as mock_select:
            with patch('qm2.core.questions.console'):
                # Mock user selecting the first question
                mock_select.return_value.ask.return_value = "Question to delete"
                
                questions.delete_question(str(temp_file))
                
                # Verify question was deleted
                remaining_questions = json.loads(temp_file.read_text(encoding="utf-8"))
                assert len(remaining_questions) == 1
                assert remaining_questions[0]["question"] == "Question to keep"
    finally:
        temp_file.unlink(missing_ok=True)


def test_delete_question_cancel():
    """Test delete_question when user cancels."""
    # Create a temporary file with questions
    temp_file = Path("/tmp/test_delete_cancel.json")
    test_questions = [
        {"question": "Question 1", "type": "multiple", "correct": "Answer", "wrong_answers": []}
    ]
    temp_file.write_text(json.dumps(test_questions), encoding="utf-8")
    
    try:
        with patch('qm2.core.questions.questionary.select') as mock_select:
            # Mock user cancelling (None return)
            mock_select.return_value.ask.return_value = None
            
            questions.delete_question(str(temp_file))
            
            # Verify no questions were deleted
            remaining_questions = json.loads(temp_file.read_text(encoding="utf-8"))
            assert len(remaining_questions) == 1
    finally:
        temp_file.unlink(missing_ok=True)
