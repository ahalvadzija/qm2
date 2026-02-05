"""
Tests for validation module to improve coverage.
"""

import tempfile
import json
import csv
from pathlib import Path

from qm2.core.validation import (
    validate_csv_file, validate_json_file, validate_csv_row, 
    validate_json_question, show_validation_errors, is_file_valid,
    VALID_TYPES, CSV_HEADERS
)


class TestCSVValidation:
    """Test CSV validation functions."""
    
    def test_validate_csv_file_valid(self):
        """Test validation of valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            writer.writerow(["multiple", "What is 2+2?", "4", "3,5,6", "", "", ""])
            writer.writerow(["truefalse", "The sky is blue", "True", "False", "", "", ""])
            f.flush()
            
            is_valid, errors = validate_csv_file(Path(f.name))
            assert is_valid
            assert len(errors) == 0
    
    def test_validate_csv_file_empty(self):
        """Test validation of empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            f.flush()
            
            is_valid, errors = validate_csv_file(Path(f.name))
            assert not is_valid
            assert any("empty" in error.lower() for error in errors)
    
    def test_validate_csv_file_missing_headers(self):
        """Test CSV with missing required headers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["wrong", "headers"])
            writer.writerow(["data", "more"])
            f.flush()
            
            is_valid, errors = validate_csv_file(Path(f.name))
            assert not is_valid
            assert any("missing required headers" in error.lower() for error in errors)
    
    def test_validate_csv_row_valid_multiple(self):
        """Test validation of valid multiple choice row."""
        row = {
            "type": "multiple",
            "question": "What is 2+2?",
            "correct": "4",
            "wrong_answers": "3,5,6",
            "left": "",
            "right": "",
            "answers": ""
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) == 0
    
    def test_validate_csv_row_valid_truefalse(self):
        """Test validation of valid true/false row."""
        row = {
            "type": "truefalse",
            "question": "The sky is blue",
            "correct": "True",
            "wrong_answers": "False",
            "left": "",
            "right": "",
            "answers": ""
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) == 0
    
    def test_validate_csv_row_valid_fillin(self):
        """Test validation of valid fill-in row."""
        row = {
            "type": "fillin",
            "question": "The capital of France is ______.",
            "correct": "Paris",
            "wrong_answers": "",
            "left": "",
            "right": "",
            "answers": ""
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) == 0
    
    def test_validate_csv_row_valid_match(self):
        """Test validation of valid matching row."""
        row = {
            "type": "match",
            "question": "Match capitals",
            "correct": "",
            "wrong_answers": "",
            "left": "Paris|London",
            "right": "France|England",
            "answers": "a:1,b:2"
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) == 0
    
    def test_validate_csv_row_invalid_type(self):
        """Test validation of row with invalid type."""
        row = {
            "type": "invalid_type",
            "question": "Test question",
            "correct": "4",
            "wrong_answers": "3,5,6",
            "left": "",
            "right": "",
            "answers": ""
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) > 0
        assert any("invalid question type" in error.lower() for error in errors)
    
    def test_validate_csv_row_missing_required(self):
        """Test validation of row missing required fields."""
        row = {
            "type": "",
            "question": "",
            "correct": "4",
            "wrong_answers": "3,5,6",
            "left": "",
            "right": "",
            "answers": ""
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) > 0
        assert any("'type' field is required" in error.lower() for error in errors)
    
    def test_validate_csv_row_invalid_truefalse(self):
        """Test validation of true/false row with invalid correct answer."""
        row = {
            "type": "truefalse",
            "question": "Test question",
            "correct": "Maybe",
            "wrong_answers": "True",
            "left": "",
            "right": "",
            "answers": ""
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) > 0
        assert any("must be 'True' or 'False'" in error for error in errors)
    
    def test_validate_csv_row_invalid_match_answers(self):
        """Test validation of matching row with invalid answer format."""
        row = {
            "type": "match",
            "question": "Match capitals",
            "correct": "",
            "wrong_answers": "",
            "left": "Paris|London",
            "right": "France|England",
            "answers": "invalid-format"
        }
        errors = validate_csv_row(row, 1)
        assert len(errors) > 0
        assert any("must be in format" in error for error in errors)


class TestJSONValidation:
    """Test JSON validation functions."""
    
    def test_validate_json_file_valid(self):
        """Test validation of valid JSON file."""
        data = [
            {
                "type": "multiple",
                "question": "What is 2+2?",
                "correct": "4",
                "wrong_answers": ["3", "5", "6"]
            },
            {
                "type": "truefalse",
                "question": "The sky is blue",
                "correct": "True",
                "wrong_answers": ["False"]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            
            is_valid, errors = validate_json_file(Path(f.name))
            assert is_valid
            assert len(errors) == 0
    
    def test_validate_json_file_invalid_syntax(self):
        """Test validation of JSON with invalid syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            f.flush()
            
            is_valid, errors = validate_json_file(Path(f.name))
            assert not is_valid
            assert any("invalid json syntax" in error.lower() for error in errors)
    
    def test_validate_json_file_not_list(self):
        """Test validation of JSON that's not a list."""
        data = {"not": "a list"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            
            is_valid, errors = validate_json_file(Path(f.name))
            assert not is_valid
            assert any("must contain a list" in error.lower() for error in errors)
    
    def test_validate_json_question_legacy_format(self):
        """Test validation of legacy JSON format."""
        question = {"q": "What is 2+2?", "a": "4"}
        errors = validate_json_question(question, 1)
        assert len(errors) == 0  # Legacy format is always valid
    
    def test_validate_json_question_valid_multiple(self):
        """Test validation of valid multiple choice question."""
        question = {
            "type": "multiple",
            "question": "What is 2+2?",
            "correct": "4",
            "wrong_answers": ["3", "5", "6"]
        }
        errors = validate_json_question(question, 1)
        assert len(errors) == 0
    
    def test_validate_json_question_valid_truefalse(self):
        """Test validation of valid true/false question."""
        question = {
            "type": "truefalse",
            "question": "The sky is blue",
            "correct": "True",
            "wrong_answers": ["False"]
        }
        errors = validate_json_question(question, 1)
        assert len(errors) == 0
    
    def test_validate_json_question_valid_fillin(self):
        """Test validation of valid fill-in question."""
        question = {
            "type": "fillin",
            "question": "The capital of France is ______.",
            "correct": "Paris"
        }
        errors = validate_json_question(question, 1)
        assert len(errors) == 0
    
    def test_validate_json_question_valid_match(self):
        """Test validation of valid matching question."""
        question = {
            "type": "match",
            "question": "Match capitals",
            "pairs": {
                "left": ["Paris", "London"],
                "right": ["France", "England"],
                "answers": {"a": "1", "b": "2"}
            }
        }
        errors = validate_json_question(question, 1)
        assert len(errors) == 0
    
    def test_validate_json_question_missing_fields(self):
        """Test validation of question missing required fields."""
        question = {
            "wrong": "format"
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("missing required fields" in error.lower() for error in errors)
    
    def test_validate_json_question_invalid_type(self):
        """Test validation of question with invalid type."""
        question = {
            "type": "invalid_type",
            "question": "Test question",
            "correct": "4",
            "wrong_answers": ["3", "5", "6"]
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("invalid question type" in error.lower() for error in errors)
    
    def test_validate_json_question_missing_correct(self):
        """Test validation of multiple choice missing correct answer."""
        question = {
            "type": "multiple",
            "question": "What is 2+2?",
            "wrong_answers": ["3", "5", "6"]
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("missing 'correct' field" in error.lower() for error in errors)
    
    def test_validate_json_question_wrong_answers_not_list(self):
        """Test validation of question with wrong_answers not as list."""
        question = {
            "type": "multiple",
            "question": "What is 2+2?",
            "correct": "4",
            "wrong_answers": "not a list"
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("'wrong_answers' must be a list" in error for error in errors)
    
    def test_validate_json_question_match_missing_pairs(self):
        """Test validation of matching question missing pairs."""
        question = {
            "type": "match",
            "question": "Match capitals"
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("missing 'pairs' field" in error.lower() for error in errors)
    
    def test_validate_json_question_match_pairs_not_dict(self):
        """Test validation of matching question with pairs not as dict."""
        question = {
            "type": "match",
            "question": "Match capitals",
            "pairs": "not a dict"
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("'pairs' must be a dictionary" in error for error in errors)
    
    def test_validate_json_question_match_missing_pairs_fields(self):
        """Test validation of matching question missing pairs fields."""
        question = {
            "type": "match",
            "question": "Match capitals",
            "pairs": {
                "left": ["Paris", "London"]
                # missing right and answers
            }
        }
        errors = validate_json_question(question, 1)
        assert len(errors) > 0
        assert any("missing pairs fields" in error.lower() for error in errors)


class TestValidationUtilities:
    """Test validation utility functions."""
    
    def test_show_validation_errors_empty(self):
        """Test show_validation_errors with empty errors."""
        show_validation_errors([])  # Should not raise any exception
    
    def test_show_validation_errors_with_errors(self):
        """Test show_validation_errors with actual errors."""
        errors = [
            "Test error 1",
            "Test error 2"
        ]
        show_validation_errors(errors)  # Should not raise any exception
    
    def test_is_file_valid_csv(self):
        """Test is_file_valid with CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            writer.writerow(["multiple", "What is 2+2?", "4", "3,5,6", "", "", ""])
            f.flush()
            
            result = is_file_valid(Path(f.name), "csv")
            assert result
    
    def test_is_file_valid_json(self):
        """Test is_file_valid with JSON file."""
        data = [
            {
                "type": "multiple",
                "question": "What is 2+2?",
                "correct": "4",
                "wrong_answers": ["3", "5", "6"]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            
            result = is_file_valid(Path(f.name), "json")
            assert result
    
    def test_is_file_valid_invalid_type(self):
        """Test is_file_valid with invalid file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test")
            f.flush()
            
            result = is_file_valid(Path(f.name), "invalid")
            assert not result
    
    def test_is_file_valid_invalid_csv(self):
        """Test is_file_valid with invalid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["wrong", "headers"])
            writer.writerow(["data", "more"])
            f.flush()
            
            result = is_file_valid(Path(f.name), "csv")
            assert not result
    
    def test_is_file_valid_invalid_json(self):
        """Test is_file_valid with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            f.flush()
            
            result = is_file_valid(Path(f.name), "json")
            assert not result


class TestValidationConstants:
    """Test validation constants."""
    
    def test_valid_types(self):
        """Test VALID_TYPES constant."""
        assert isinstance(VALID_TYPES, set)
        assert "multiple" in VALID_TYPES
        assert "truefalse" in VALID_TYPES
        assert "fillin" in VALID_TYPES
        assert "match" in VALID_TYPES
        assert len(VALID_TYPES) == 4
    
    def test_csv_headers(self):
        """Test CSV_HEADERS constant."""
        assert isinstance(CSV_HEADERS, list)
        assert "type" in CSV_HEADERS
        assert "question" in CSV_HEADERS
        assert "correct" in CSV_HEADERS
        assert "wrong_answers" in CSV_HEADERS
        assert "left" in CSV_HEADERS
        assert "right" in CSV_HEADERS
        assert "answers" in CSV_HEADERS
        assert len(CSV_HEADERS) == 7
