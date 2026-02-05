"""
Additional tests for engine.py to improve coverage to 85%+.
Focus on timeout scenarios, empty categories, shuffle verification, and match questions.
"""

from unittest.mock import patch, MagicMock, Mock
import random

from qm2.core.engine import (
    quiz_session, flashcards_mode, _handle_choice_question, 
    _handle_fillin_question, _handle_match_question, input_with_timeout,
    _is_valid_question
)


class TestEngineCoverage:
    """Additional tests for engine.py coverage improvement."""
    
    def test_input_with_timeout_windows_none(self):
        """Test input_with_timeout returns None on timeout (Windows path)."""
        with patch('qm2.core.engine.platform.system', return_value='Windows'):
            with patch('qm2.core.engine.threading.Thread') as mock_thread:
                # Mock thread that stays alive (timeout)
                mock_thread_instance = MagicMock()
                mock_thread_instance.is_alive.return_value = True
                mock_thread.return_value = mock_thread_instance
                
                result = input_with_timeout("Test prompt", timeout=1)
                
                assert result is None
                mock_thread.return_value.start.assert_called_once()
                mock_thread_instance.join.assert_called_once_with(1)
    
    def test_input_with_timeout_unix_timeout(self):
        """Test input_with_timeout returns None on timeout (Unix path)."""
        with patch('qm2.core.engine.platform.system', return_value='Linux'):
            with patch('qm2.core.engine.select.select') as mock_select:
                with patch('qm2.core.engine.sys.stdin.readline'):
                    # Simulate timeout (no ready input)
                    mock_select.return_value = ([], [], [])
                    
                    result = input_with_timeout("Test prompt", timeout=1)
                    
                    assert result is None
                    mock_select.assert_called_once()
    
    def test_input_with_timeout_unix_success(self):
        """Test input_with_timeout returns input on success (Unix path)."""
        with patch('qm2.core.engine.platform.system', return_value='Linux'):
            with patch('qm2.core.engine.select.select') as mock_select:
                with patch('qm2.core.engine.sys.stdin.readline') as mock_readline:
                    # Simulate successful input
                    mock_select.return_value = ([Mock()], [], [])
                    mock_readline.return_value = "test input\n"
                    
                    result = input_with_timeout("Test prompt", timeout=60)
                    
                    assert result == "test input"
                    mock_select.assert_called_once()
    
    def test_quiz_session_empty_questions(self, tmp_path):
        """Test quiz_session with empty questions list."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        with patch('qm2.core.engine.console.print') as mock_print:
            quiz_session([], score_file)
            mock_print.assert_called_with("[red]⚠️ No available questions.")
    
    def test_quiz_session_no_valid_questions(self, tmp_path):
        """Test quiz_session with no valid questions."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        invalid_questions = [
            {"type": "invalid", "question": "Test"},  # Invalid type
            {"question": "Test"},  # Missing type
            {"type": "multiple"}  # Missing required fields
        ]
        
        with patch('qm2.core.engine.console.print') as mock_print:
            quiz_session(invalid_questions, score_file)
            # Should print about skipped invalid questions and no valid questions
            assert mock_print.call_count >= 2
    
    def test_quiz_session_with_invalid_questions_mixed(self, tmp_path):
        """Test quiz_session with mix of valid and invalid questions."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        questions = [
            {"type": "invalid", "question": "Test"},  # Invalid
            {
                "type": "multiple",
                "question": "Valid question",
                "correct": "Answer",
                "wrong_answers": ["Wrong1", "Wrong2"]
            }  # Valid
        ]
        
        # Track order of questions passed to handler
        handled_questions = []
        
        def mock_handler(q):
            handled_questions.append(q["question"])
            return "correct"
        
        with patch('qm2.core.engine._handle_choice_question', side_effect=mock_handler):
            with patch('qm2.core.engine.console.print') as mock_print:
                with patch('qm2.core.engine._show_quiz_statistics'):
                    with patch('qm2.core.engine._save_quiz_result'):
                        quiz_session(questions, score_file)
                
                # Should skip invalid question and handle valid one
                mock_print.assert_any_call("[yellow]⚠️ Skipped 1 invalid question(s).[/yellow]")
                assert len(handled_questions) == 1
    
    def test_quiz_session_shuffle_changes_order(self, tmp_path):
        """Test that quiz_session shuffles questions order."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        questions = [
            {
                "type": "multiple",
                "question": f"Question {i}",
                "correct": f"Answer {i}",
                "wrong_answers": [f"Wrong {i}"]
            }
            for i in range(3)
        ]
        
        # Track order of questions passed to handler
        handled_questions = []
        
        def mock_handler(q):
            handled_questions.append(q["question"])
            return "correct"
        
        # We use a fixed seed to ensure shuffle results in a different order
        # With seed 42 and 3 elements, the order will definitely change.
        random.seed(42)

        with patch('qm2.core.engine._handle_choice_question', side_effect=mock_handler):
            with patch('qm2.core.engine._show_quiz_statistics'):
                with patch('qm2.core.engine._save_quiz_result'):
                    quiz_session(questions, score_file)
        
        # Questions should be processed in shuffled order (not original order)
        assert len(handled_questions) == 3
        assert handled_questions != ["Question 0", "Question 1", "Question 2"]
    
    def test_handle_match_question_success(self):
        """Test _handle_match_question with correct mapping."""
        question = {
            "type": "match",
            "question": "Match test",
            "pairs": {
                "left": ["A", "B"],
                "right": ["1", "2"],
                "answers": {"a": "1", "b": "2"}
            }
        }
        
        with patch('qm2.core.engine.input_with_timeout') as mock_input:
            with patch('qm2.core.engine.console.print'):
                # Mock correct inputs: a-1, b-2
                mock_input.side_effect = ["1", "2"]
                
                result = _handle_match_question(question)
                
                assert result == "correct"
    
    def test_handle_match_question_wrong_mapping(self):
        """Test _handle_match_question with incorrect mapping."""
        question = {
            "type": "match",
            "question": "Match test",
            "pairs": {
                "left": ["A", "B"],
                "right": ["1", "2"],
                "answers": {"a": "1", "b": "2"}
            }
        }
        
        with patch('qm2.core.engine.input_with_timeout') as mock_input:
            with patch('qm2.core.engine.console.print'):
                # Mock incorrect inputs: a-2, b-1
                mock_input.side_effect = ["2", "1"]
                
                result = _handle_match_question(question)
                
                assert result == "wrong"
    
    def test_handle_match_question_invalid_pairs_format(self):
        """Test _handle_match_question with invalid pairs format."""
        question = {
            "type": "match",
            "question": "Match test",
            "pairs": '{"invalid": "json"}'  # Invalid JSON string
        }
        
        with patch('qm2.core.engine.console.print') as mock_print:
            result = _handle_match_question(question)
            
            assert result == "wrong"
            mock_print.assert_any_call("[red]⚠️ Matching question is not properly defined.")
    
    def test_quiz_session_complete_successful_quiz(self, tmp_path):
        """Test complete successful quiz session with multiple question types."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        questions = [
            {
                "type": "multiple",
                "question": "What is 2+2?",
                "correct": "4",
                "wrong_answers": ["3", "5"]
            },
            {
                "type": "fillin",
                "question": "Capital of France?",
                "correct": "Paris",
                "wrong_answers": []
            },
            {
                "type": "match",
                "question": "Match test",
                "pairs": {
                    "left": ["A"],
                    "right": ["1"],
                    "answers": {"a": "1"}
                }
            }
        ]
        
        # Mock all user inputs to be correct
        with patch('qm2.core.engine.random.shuffle') as mock_shuffle:
            with patch('qm2.core.engine.input_with_timeout'):
                with patch('qm2.core.engine._show_quiz_statistics') as mock_stats:
                    with patch('qm2.core.engine._save_quiz_result') as mock_save:
                        # Don't shuffle questions to maintain predictable order
                        mock_shuffle.side_effect = lambda x: None
                        
                        # Mock the choice question handler to return correct without needing to know shuffled order
                        with patch('qm2.core.engine._handle_choice_question') as mock_choice:
                            with patch('qm2.core.engine._handle_fillin_question') as mock_fillin:
                                with patch('qm2.core.engine._handle_match_question') as mock_match:
                                    # All handlers return correct
                                    mock_choice.return_value = "correct"
                                    mock_fillin.return_value = "correct"
                                    mock_match.return_value = "correct"
                                    
                                    quiz_session(questions, score_file)
                                    
                                    # Verify all question handlers were called
                                    mock_choice.assert_called_once()
                                    mock_fillin.assert_called_once()
                                    mock_match.assert_called_once()
                                    
                                    # Verify statistics and save were called
                                    mock_stats.assert_called_once()
                                    mock_save.assert_called_once()
    
    def test_quiz_session_fillin_wrong_answer(self, tmp_path):
        """Test quiz session with wrong fill-in answer."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        questions = [
            {
                "type": "fillin",
                "question": "Capital of France?",
                "correct": "Paris",
                "wrong_answers": []
            }
        ]
        
        with patch('qm2.core.engine.input_with_timeout') as mock_input:
            with patch('qm2.core.engine._show_quiz_statistics') as mock_stats:
                with patch('qm2.core.engine._save_quiz_result') as mock_save:
                    with patch('qm2.core.engine.console.print') as mock_print:
                        # Wrong answer: 'London'
                        mock_input.side_effect = ["London", ""]
                        
                        quiz_session(questions, score_file)
                        
                        # Verify wrong answer was handled
                        mock_print.assert_any_call("[red]❌ Wrong. The correct answer is: [bold]Paris[/]")
                        mock_stats.assert_called_once()
                        mock_save.assert_called_once()
    
    def test_quiz_session_user_quit_mid_session(self, tmp_path):
        """Test quiz session when user quits mid-session."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        questions = [
            {
                "type": "multiple",
                "question": "Question 1",
                "correct": "A",
                "wrong_answers": ["B", "C"]
            },
            {
                "type": "multiple",
                "question": "Question 2",
                "correct": "X",
                "wrong_answers": ["Y", "Z"]
            }
        ]
        
        with patch('qm2.core.engine.input_with_timeout') as mock_input:
            with patch('qm2.core.engine._check_quit_confirmation') as mock_confirm:
                with patch('qm2.core.engine.console.print') as mock_print:
                    # First question: quit
                    # Second question: should not be reached
                    mock_input.side_effect = ["x"]
                    mock_confirm.return_value = True  # Confirm quit
                    
                    quiz_session(questions, score_file)
                    
                    # Verify quit was handled
                    mock_confirm.assert_called_once()
                    mock_print.assert_any_call("[yellow]⏹️ Quiz stopped by the user.")
    
    def test_quiz_session_user_quit_then_continue(self, tmp_path):
        """Test quiz session when user tries to quit but then continues."""
        score_file = tmp_path / "test_scores.json"
        score_file.write_text("[]", encoding="utf-8")
        
        questions = [
            {
                "type": "multiple",
                "question": "Question 1",
                "correct": "A",
                "wrong_answers": ["B", "C"]
            }
        ]
        
        with patch('qm2.core.engine.input_with_timeout') as mock_input:
            with patch('qm2.core.engine._check_quit_confirmation') as mock_confirm:
                with patch('qm2.core.engine._show_quiz_statistics') as mock_stats:
                    with patch('qm2.core.engine._save_quiz_result') as mock_save:
                        # Try to quit, but cancel, then answer correctly
                        mock_input.side_effect = ["x", "a"]  # quit, then correct answer
                        mock_confirm.return_value = False  # Don't confirm quit
                        
                        quiz_session(questions, score_file)
                        
                        # Verify quiz continued and completed
                        assert mock_input.call_count == 2
                        mock_stats.assert_called_once()
                        mock_save.assert_called_once()
    
    def test_handle_match_question_incomplete_pairs(self):
        """Test _handle_match_question with incomplete pairs."""
        question = {
            "type": "match",
            "question": "Match test",
            "pairs": {
                "left": ["A"],  # Missing right and answers
                "right": [],
                "answers": {}
            }
        }
        
        with patch('qm2.core.engine.console.print') as mock_print:
            result = _handle_match_question(question)
            
            assert result == "wrong"
            mock_print.assert_any_call("[red]⚠️ Matching question is not properly defined.")
    
    def test_handle_choice_question_timeout(self):
        """Test _handle_choice_question timeout scenario."""
        question = {
            "type": "multiple",
            "question": "Test question",
            "correct": "A",
            "wrong_answers": ["B", "C"]
        }
        
        with patch('qm2.core.engine.input_with_timeout', return_value=None):
            with patch('qm2.core.engine.console.print') as mock_print:
                result = _handle_choice_question(question)
                
                assert result == "timeout"
                mock_print.assert_any_call("[red]❌ Time is up. Correct answer: [bold]A[/]")
    
    def test_handle_fillin_question_timeout(self):
        """Test _handle_fillin_question timeout scenario."""
        question = {
            "type": "fillin",
            "question": "Fill in test",
            "correct": "Answer"
        }
        
        with patch('qm2.core.engine.input_with_timeout', return_value=None):
            with patch('qm2.core.engine.console.print') as mock_print:
                result = _handle_fillin_question(question)
                
                assert result == "timeout"
                mock_print.assert_any_call("[red]❌ Time is up. Correct answer: [bold]Answer[/]")
    
    def test_flashcards_mode_empty_questions(self):
        """Test flashcards_mode with empty questions list."""
        with patch('qm2.core.engine.console.print') as mock_print:
            flashcards_mode([])
            mock_print.assert_called_with("[red]⚠️ No questions for flashcards.")
    
    def test_flashcards_mode_no_valid_questions(self):
        """Test flashcards_mode with no valid questions."""
        invalid_questions = [{"type": "invalid"}]
        
        with patch('qm2.core.engine.console.print') as mock_print:
            flashcards_mode(invalid_questions)
            mock_print.assert_any_call("[red]⚠️ No valid questions available.")
    
    def test_flashcards_mode_with_match_question(self):
        """Test flashcards_mode with match question."""
        question = {
            "type": "match",
            "question": "Match test",
            "pairs": {
                "left": ["A"],
                "right": ["1"],
                "answers": {"a": "1"}
            }
        }
        
        with patch('qm2.core.engine.Prompt.ask') as mock_prompt:
            with patch('qm2.core.engine.questionary.confirm') as mock_confirm:
                with patch('qm2.core.engine.console.print') as mock_print:
                    mock_prompt.side_effect = ["", ""]  # Reveal, continue (don't exit)
                    mock_confirm.return_value.ask.return_value = False  # Don't confirm exit
                    
                    flashcards_mode([question])
                    
                    # Should show correct matching table
                    mock_print.assert_any_call("[green]✅ Correct matching:")
    
    def test_flashcards_mode_exit_confirmation(self):
        """Test flashcards_mode exit confirmation flow."""
        question = {
            "type": "multiple",
            "question": "Test",
            "correct": "Answer",
            "wrong_answers": []
        }
        
        with patch('qm2.core.engine.Prompt.ask') as mock_prompt:
            with patch('qm2.core.engine.questionary.confirm') as mock_confirm:
                with patch('qm2.core.engine.console.print') as mock_print:
                    mock_prompt.side_effect = ["x", ""]  # Exit command
                    mock_confirm.return_value.ask.return_value = True  # Confirm exit
                    
                    flashcards_mode([question])
                    
                    mock_confirm.assert_called_once()
                    mock_print.assert_any_call("[yellow]⏹️ Exited flashcards mode.")
    
    def test_is_valid_question_match_type(self):
        """Test _is_valid_question with match type question."""
        valid_match = {
            "type": "match",
            "question": "Match test",
            "pairs": {"left": ["A"], "right": ["1"], "answers": {"a": "1"}}
        }
        assert _is_valid_question(valid_match) is True
    
    def test_is_valid_question_match_invalid_pairs(self):
        """Test _is_valid_question with match type but invalid pairs."""
        invalid_match = {
            "type": "match",
            "question": "Match test",
            "pairs": "invalid"  # Not a dict
        }
        assert _is_valid_question(invalid_match) is False