import pytest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import qm2.core.engine as engine


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
def sample_multiple_choice_question():
    """Sample multiple choice question for testing."""
    return {
        "type": "multiple",
        "question": "What is the capital of France?",
        "correct": "Paris",
        "wrong_answers": ["Rome", "Berlin", "Madrid"]
    }


@pytest.fixture
def sample_true_false_question():
    """Sample true/false question for testing."""
    return {
        "type": "truefalse",
        "question": "Python is a programming language.",
        "correct": "True",
        "wrong_answers": ["False"]
    }


@pytest.fixture
def sample_fill_in_question():
    """Sample fill-in question for testing."""
    return {
        "type": "fillin",
        "question": "The capital of Japan is ______.",
        "correct": "Tokyo",
        "wrong_answers": []
    }


@pytest.fixture
def sample_matching_question():
    """Sample matching question for testing."""
    return {
        "type": "match",
        "question": "Match programming languages with their types",
        "pairs": {
            "left": ["Python", "JavaScript", "C++"],
            "right": ["Interpreted", "Web scripting", "Compiled"],
            "answers": {"a": "1", "b": "2", "c": "3"}
        }
    }


@pytest.fixture
def temp_score_file(tmp_path):
    """Create a temporary score file for testing."""
    score_file = tmp_path / "test_scores.json"
    score_file.write_text("[]", encoding="utf-8")
    return score_file


def test_is_valid_question_valid():
    """Test _is_valid_question with valid questions."""
    valid_q = {
        "type": "multiple",
        "question": "Test?",
        "correct": "Answer"
    }
    assert engine._is_valid_question(valid_q) is True


def test_is_valid_question_invalid():
    """Test _is_valid_question with invalid questions."""
    # Missing required fields
    invalid_q1 = {"type": "multiple"}
    invalid_q2 = {"question": "Test?"}
    invalid_q3 = {"correct": "Answer"}
    
    assert engine._is_valid_question(invalid_q1) is False
    assert engine._is_valid_question(invalid_q2) is False
    assert engine._is_valid_question(invalid_q3) is False
    
    # Invalid type
    assert engine._is_valid_question("not a dict") is False


def test_is_valid_question_matching_valid():
    """Test _is_valid_question with valid matching question."""
    valid_match = {
        "type": "match",
        "question": "Match items",
        "pairs": {
            "left": ["A", "B"],
            "right": ["1", "2"],
            "answers": {"a": "1", "b": "2"}
        }
    }
    assert engine._is_valid_question(valid_match) is True


def test_is_valid_question_matching_invalid():
    """Test _is_valid_question with invalid matching question."""
    # Missing pairs
    invalid_match1 = {
        "type": "match",
        "question": "Match items"
    }
    
    # Missing required pair fields
    invalid_match2 = {
        "type": "match",
        "question": "Match items",
        "pairs": {
            "left": ["A"],
            "right": ["1"]
        }
    }
    
    assert engine._is_valid_question(invalid_match1) is False
    assert engine._is_valid_question(invalid_match2) is False


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_choice_question_correct(mock_confirm, mock_input, sample_multiple_choice_question):
    """Test _handle_choice_question with correct answer."""
    # Mock user selects correct option - we need to determine which letter is correct
    # Since options are shuffled, we'll mock the shuffle to be predictable
    with patch('qm2.core.engine.random.shuffle') as mock_shuffle:
        # Force a predictable order: [correct, wrong1, wrong2, wrong3]
        mock_shuffle.side_effect = lambda x: None  # Don't shuffle
        
        # Now 'a' should be the correct answer
        mock_input.return_value = "a"
        mock_confirm.return_value.ask.return_value = False
        
        with patch('qm2.core.engine.console') as mock_console:
            result = engine._handle_choice_question(sample_multiple_choice_question)
            assert result == "correct"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_choice_question_wrong(mock_confirm, mock_input, sample_multiple_choice_question):
    """Test _handle_choice_question with wrong answer."""
    # Mock user selects wrong option
    with patch('qm2.core.engine.random.shuffle') as mock_shuffle:
        # Force a predictable order: [correct, wrong1, wrong2, wrong3]
        mock_shuffle.side_effect = lambda x: None  # Don't shuffle
        
        # Now 'b' should be a wrong answer
        mock_input.return_value = "b"
        mock_confirm.return_value.ask.return_value = False
        
        with patch('qm2.core.engine.console') as mock_console:
            result = engine._handle_choice_question(sample_multiple_choice_question)
            assert result == "wrong"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_choice_question_timeout(mock_confirm, mock_input, sample_multiple_choice_question):
    """Test _handle_choice_question with timeout."""
    # Mock timeout (None return from input_with_timeout)
    mock_input.return_value = None
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_choice_question(sample_multiple_choice_question)
        assert result == "timeout"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_choice_question_quit(mock_confirm, mock_input, sample_multiple_choice_question):
    """Test _handle_choice_question with quit."""
    # Mock user wants to quit
    mock_input.return_value = "x"
    mock_confirm.return_value.ask.return_value = True  # Confirms quit
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_choice_question(sample_multiple_choice_question)
        assert result == "quit"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_fillin_question_correct(mock_confirm, mock_input, sample_fill_in_question):
    """Test _handle_fillin_question with correct answer."""
    mock_input.return_value = "Tokyo"
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_fillin_question(sample_fill_in_question)
        assert result == "correct"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_fillin_question_case_insensitive(mock_confirm, mock_input, sample_fill_in_question):
    """Test _handle_fillin_question with case insensitive matching."""
    mock_input.return_value = "tokyo"  # lowercase
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_fillin_question(sample_fill_in_question)
        assert result == "correct"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_fillin_question_wrong(mock_confirm, mock_input, sample_fill_in_question):
    """Test _handle_fillin_question with wrong answer."""
    mock_input.return_value = "Osaka"
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_fillin_question(sample_fill_in_question)
        assert result == "wrong"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_match_question_correct(mock_confirm, mock_input, sample_matching_question):
    """Test _handle_match_question with correct answers."""
    # Mock correct matching: a-1, b-2, c-3
    mock_input.side_effect = ["1", "2", "3"]
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_match_question(sample_matching_question)
        assert result == "correct"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_match_question_wrong(mock_confirm, mock_input, sample_matching_question):
    """Test _handle_match_question with wrong answers."""
    # Mock wrong matching: a-2, b-1, c-3
    mock_input.side_effect = ["2", "1", "3"]
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_match_question(sample_matching_question)
        assert result == "wrong"


@patch('qm2.core.engine.input_with_timeout')
@patch('qm2.core.engine.questionary.confirm')
def test_handle_match_question_timeout(mock_confirm, mock_input, sample_matching_question):
    """Test _handle_match_question with timeout."""
    # Mock timeout on first input
    mock_input.return_value = None
    mock_confirm.return_value.ask.return_value = False
    
    with patch('qm2.core.engine.console') as mock_console:
        result = engine._handle_match_question(sample_matching_question)
        assert result == "timeout"


def test_quiz_session_empty_questions(temp_score_file):
    """Test quiz_session with empty questions list."""
    with patch('qm2.core.engine.console') as mock_console:
        engine.quiz_session([], temp_score_file)
        mock_console.print.assert_called_with("[red]⚠️ No available questions.")


def test_quiz_session_no_valid_questions(temp_score_file):
    """Test quiz_session with no valid questions."""
    invalid_questions = [
        {"type": "invalid"},  # Missing required fields
        {"question": "test"}  # Missing type
    ]
    
    with patch('qm2.core.engine.console') as mock_console:
        engine.quiz_session(invalid_questions, temp_score_file)
        mock_console.print.assert_called_with("[red]⚠️ No valid questions available.")


def test_quiz_session_skips_invalid_questions(temp_score_file):
    """Test quiz_session skips invalid questions."""
    questions = [
        {
            "type": "multiple",
            "question": "Valid question",
            "correct": "Answer",
            "wrong_answers": ["Wrong1", "Wrong2", "Wrong3"]
        },
        {"type": "invalid"},  # Invalid question
        {
            "type": "truefalse",
            "question": "Another valid question",
            "correct": "True",
            "wrong_answers": ["False"]
        }
    ]
    
    with patch('qm2.core.engine.console') as mock_console:
        with patch('qm2.core.engine._handle_choice_question') as mock_handler:
            mock_handler.return_value = "correct"
            engine.quiz_session(questions, temp_score_file)
            
            # Should call handler twice (for 2 valid questions)
            assert mock_handler.call_count == 2


def test_flashcards_mode_empty_questions():
    """Test flashcards_mode with empty questions list."""
    with patch('qm2.core.engine.console') as mock_console:
        engine.flashcards_mode([])
        mock_console.print.assert_called_with("[red]⚠️ No questions for flashcards.")


def test_flashcards_mode_no_valid_questions():
    """Test flashcards_mode with no valid questions."""
    invalid_questions = [
        {"type": "invalid"},
        {"question": "test"}
    ]
    
    with patch('qm2.core.engine.console') as mock_console:
        engine.flashcards_mode(invalid_questions)
        mock_console.print.assert_called_with("[red]⚠️ No valid questions available.")


@patch('qm2.core.engine.Prompt.ask')
def test_flashcards_mode_normal_flow(mock_ask, sample_multiple_choice_question):
    """Test flashcards_mode normal flow."""
    # Mock user pressing Enter to continue, then 'x' to exit
    mock_ask.side_effect = ["", "x"]
    
    with patch('qm2.core.engine.questionary.confirm') as mock_confirm:
        mock_confirm.return_value.ask.return_value = True  # Confirm exit
        
        with patch('qm2.core.engine.console') as mock_console:
            engine.flashcards_mode([sample_multiple_choice_question])
            
            # Should show question and answer
            assert mock_console.rule.called
            assert mock_console.print.called


def test_save_quiz_result(temp_score_file):
    """Test _save_quiz_result function."""
    with patch('qm2.core.engine.load_json') as mock_load:
        with patch('qm2.core.engine.save_json') as mock_save:
            mock_load.return_value = [{"old": "score"}]
            mock_save.return_value = True
            
            engine._save_quiz_result(
                temp_score_file, 5, 3, 2, 10, 120
            )
            
            # Verify save was called with updated data
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0]
            assert call_args[0] == str(temp_score_file)
            
            # Check that new score was added
            saved_data = call_args[1]
            assert len(saved_data) == 2  # Old + new
            assert saved_data[1]["correct"] == 5
            assert saved_data[1]["wrong"] == 3
            assert saved_data[1]["unanswered"] == 2
            assert saved_data[1]["total"] == 10
            assert saved_data[1]["duration_s"] == 120


def test_save_quiz_result_save_failure(temp_score_file):
    """Test _save_quiz_result when save fails."""
    with patch('qm2.core.engine.load_json') as mock_load:
        with patch('qm2.core.engine.save_json') as mock_save:
            with patch('qm2.core.engine.console') as mock_console:
                mock_load.return_value = []
                mock_save.return_value = False  # Save fails
                
                engine._save_quiz_result(
                    temp_score_file, 1, 0, 0, 1, 60
                )
                
                # Should print error message
                mock_console.print.assert_called_with("[red]⚠️ Failed to save quiz results.")


def test_show_quiz_statistics():
    """Test _show_quiz_statistics function."""
    with patch('qm2.core.engine.console') as mock_console:
        engine._show_quiz_statistics(5, 3, 2, 10, 120)
        
        # Verify all statistics are displayed
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("5" in call and "correct" in call.lower() for call in calls)
        assert any("3" in call and "wrong" in call.lower() for call in calls)
        assert any("2" in call and "unanswered" in call.lower() for call in calls)
        assert any("120" in call and "time" in call.lower() for call in calls)
        assert any("5/10" in call for call in calls)
