"""
Validation utilities for CSV and JSON quiz files.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rich.console import Console

console = Console()

# Valid question types
VALID_TYPES = {"multiple", "truefalse", "fillin", "match"}

# Required fields for all questions
REQUIRED_FIELDS = {"type", "question"}

# Fields required by question type
TYPE_SPECIFIC_FIELDS = {
    "multiple": ["correct", "wrong_answers"],
    "truefalse": ["correct", "wrong_answers"], 
    "fillin": ["correct"],
    "match": ["pairs"]
}

# CSV headers
CSV_HEADERS = ["type", "question", "correct", "wrong_answers", "left", "right", "answers"]


def validate_csv_file(csv_file: Path) -> Tuple[bool, List[str]]:
    """
    Validate CSV file format and content.
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                errors.append("CSV file is empty or has no headers")
                return False, errors
            
            headers = set(reader.fieldnames)
            
            # Check required headers
            required_headers = {"type", "question"}
            missing_headers = required_headers - headers
            if missing_headers:
                errors.append(f"Missing required headers: {', '.join(missing_headers)}")
            
            # Validate each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                row_errors = validate_csv_row(row, row_num)
                errors.extend(row_errors)
    
    except Exception as e:
        errors.append(f"Error reading CSV file: {str(e)}")
    
    return len(errors) == 0, errors


def validate_csv_row(row: Dict[str, str], row_num: int) -> List[str]:
    """Validate a single CSV row."""
    errors = []
    
    # Check required fields
    if not row.get("type", "").strip():
        errors.append(f"Row {row_num}: 'type' field is required")
        return errors
    
    if not row.get("question", "").strip():
        errors.append(f"Row {row_num}: 'question' field is required")
    
    q_type = row["type"].strip().lower()
    
    # Validate question type
    if q_type not in VALID_TYPES:
        errors.append(f"Row {row_num}: Invalid question type '{q_type}'. Valid types: {', '.join(VALID_TYPES)}")
        return errors
    
    # Type-specific validation
    if q_type == "multiple":
        if not row.get("correct", "").strip():
            errors.append(f"Row {row_num}: 'correct' field is required for multiple choice")
        
        wrong_answers = row.get("wrong_answers", "").strip()
        if not wrong_answers:
            errors.append(f"Row {row_num}: 'wrong_answers' field is required for multiple choice")
    
    elif q_type == "truefalse":
        correct = row.get("correct", "").strip().lower()
        if correct not in ["true", "false"]:
            errors.append(f"Row {row_num}: 'correct' must be 'True' or 'False' for true/false questions")
        
        wrong_answers = row.get("wrong_answers", "").strip()
        if not wrong_answers:
            errors.append(f"Row {row_num}: 'wrong_answers' field is required for true/false questions")
    
    elif q_type == "fillin":
        if not row.get("correct", "").strip():
            errors.append(f"Row {row_num}: 'correct' field is required for fill-in questions")
    
    elif q_type == "match":
        left = row.get("left", "").strip()
        right = row.get("right", "").strip()
        answers = row.get("answers", "").strip()
        
        if not left or not right or not answers:
            errors.append(f"Row {row_num}: 'left', 'right', and 'answers' fields are required for matching questions")
        else:
            # Validate answer format (a:1,b:2)
            if not all(":" in pair for pair in answers.split(",")):
                errors.append(f"Row {row_num}: 'answers' must be in format 'a:1,b:2' for matching questions")
    
    return errors


def validate_json_file(json_file: Path) -> Tuple[bool, List[str]]:
    """
    Validate JSON file format and content.
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's a list
        if not isinstance(data, list):
            errors.append("JSON file must contain a list of questions")
            return False, errors
        
        # Validate each question
        for q_num, question in enumerate(data, start=1):
            q_errors = validate_json_question(question, q_num)
            errors.extend(q_errors)
    
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON syntax: {str(e)}")
    except Exception as e:
        errors.append(f"Error reading JSON file: {str(e)}")
    
    return len(errors) == 0, errors


def validate_json_question(question: Dict[str, Any], q_num: int) -> List[str]:
    """Validate a single JSON question."""
    errors = []
    
    # Check for legacy format (q, a) or new format (type, question, correct)
    has_legacy_format = "q" in question and "a" in question
    has_new_format = "type" in question and "question" in question
    
    if not has_legacy_format and not has_new_format:
        errors.append(f"Question {q_num}: Missing required fields. Need either 'q'/'a' (legacy) or 'type'/'question' (new format)")
        return errors
    
    # For legacy format, convert to new format for validation
    if has_legacy_format:
        # Legacy format is always valid (simple question-answer)
        return errors
    
    # Validate new format
    q_type = str(question["type"]).lower()
    
    # Validate question type
    if q_type not in VALID_TYPES:
        errors.append(f"Question {q_num}: Invalid question type '{q_type}'. Valid types: {', '.join(VALID_TYPES)}")
        return errors
    
    # Type-specific validation
    if q_type == "multiple":
        if "correct" not in question:
            errors.append(f"Question {q_num}: Missing 'correct' field for multiple choice")
        
        if "wrong_answers" not in question:
            errors.append(f"Question {q_num}: Missing 'wrong_answers' field for multiple choice")
        elif not isinstance(question["wrong_answers"], list):
            errors.append(f"Question {q_num}: 'wrong_answers' must be a list")
    
    elif q_type == "truefalse":
        if "correct" not in question:
            errors.append(f"Question {q_num}: Missing 'correct' field for true/false")
        else:
            correct = str(question["correct"]).lower()
            if correct not in ["true", "false"]:
                errors.append(f"Question {q_num}: 'correct' must be 'True' or 'False' for true/false questions")
        
        if "wrong_answers" not in question:
            errors.append(f"Question {q_num}: Missing 'wrong_answers' field for true/false")
        elif not isinstance(question["wrong_answers"], list):
            errors.append(f"Question {q_num}: 'wrong_answers' must be a list")
    
    elif q_type == "fillin":
        if "correct" not in question:
            errors.append(f"Question {q_num}: Missing 'correct' field for fill-in questions")
    
    elif q_type == "match":
        if "pairs" not in question:
            errors.append(f"Question {q_num}: Missing 'pairs' field for matching questions")
        elif not isinstance(question["pairs"], dict):
            errors.append(f"Question {q_num}: 'pairs' must be a dictionary")
        else:
            pairs = question["pairs"]
            required_keys = {"left", "right", "answers"}
            missing_keys = required_keys - set(pairs.keys())
            if missing_keys:
                errors.append(f"Question {q_num}: Missing pairs fields: {', '.join(missing_keys)}")
            
            # Check structure
            if "left" in pairs and not isinstance(pairs["left"], list):
                errors.append(f"Question {q_num}: 'pairs.left' must be a list")
            if "right" in pairs and not isinstance(pairs["right"], list):
                errors.append(f"Question {q_num}: 'pairs.right' must be a list")
            if "answers" in pairs and not isinstance(pairs["answers"], dict):
                errors.append(f"Question {q_num}: 'pairs.answers' must be a dictionary")
    
    return errors


def show_validation_errors(errors: List[str]) -> None:
    """Display validation errors in a user-friendly format."""
    if not errors:
        return
    
    console.print("[red]🚨 Validation Errors Found:[/red]")
    for error in errors:
        console.print(f"  • [yellow]{error}[/yellow]")
    
    console.print("\n[cyan]💡 Tips:[/cyan]")
    console.print("  • For CSV: Check that all required columns are present")
    console.print("  • For JSON: Ensure proper syntax and required fields")
    console.print("  • Legacy JSON format (q, a) is also supported")
    console.print("  • Matching questions need left|right format and a:1,b:2 answers")
    console.print("  • Multiple choice needs at least one wrong answer")


def is_file_valid(file_path: Path, file_type: str) -> bool:
    """
    Quick validation check for UI purposes.
    
    Args:
        file_path: Path to the file
        file_type: 'csv' or 'json'
    
    Returns:
        True if file is valid, False otherwise
    """
    if file_type.lower() == "csv":
        is_valid, errors = validate_csv_file(file_path)
    elif file_type.lower() == "json":
        is_valid, errors = validate_json_file(file_path)
    else:
        return False
    
    if not is_valid:
        show_validation_errors(errors)
    
    return is_valid
