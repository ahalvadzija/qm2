"""
Simple tests for import_export.py to improve coverage.
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

from qm2.core.import_export import (
    download_remote, csv_to_json, json_to_csv
)


class TestImportExportSimple:
    """Simple tests for import_export functions."""
    
    def test_download_remote_file_exists_no_overwrite(self):
        """Test download when file exists and overwrite=False."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            with pytest.raises(FileExistsError):
                download_remote("http://example.com/test", tmp_path, overwrite=False)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    
    def test_download_remote_with_overwrite(self):
        """Test download with overwrite=True."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp_path.write_bytes(b"existing")
        
        try:
            # Mock requests response
            mock_response = MagicMock()
            mock_response.content = b"new data"
            
            with patch('requests.get', return_value=mock_response):
                result = download_remote("http://example.com/test", tmp_path, overwrite=True)
                assert result == tmp_path
                assert tmp_path.read_bytes() == b"new data"
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    
    def test_csv_to_json_basic(self):
        """Test basic CSV to JSON conversion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "test.csv"
            json_path = Path(tmp_dir) / "test.json"
            
            # Create proper CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['type', 'question', 'correct', 'wrong_answers', 'left', 'right', 'answers'])
                writer.writerow(['multiple', 'What is 2+2?', '4', '3,5,6', '', '', ''])
                writer.writerow(['truefalse', 'The sky is blue', 'True', 'False', '', '', ''])
            
            # Convert
            csv_to_json(csv_path, json_path)
            
            # Check result
            assert json_path.exists()
            with open(json_path) as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['type'] == 'multiple'
            assert data[0]['question'] == 'What is 2+2?'
            assert data[0]['correct'] == '4'
    
    def test_csv_to_json_empty_file(self):
        """Test CSV to JSON with empty file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "test.csv"
            json_path = Path(tmp_dir) / "test.json"
            
            # Create empty CSV with headers only
            csv_path.write_text("type,question,correct,wrong_answers,left,right,answers\n")
            
            # Convert
            csv_to_json(csv_path, json_path)
            
            # Check result
            assert json_path.exists()
            with open(json_path) as f:
                data = json.load(f)
            
            assert data == []
    
    def test_json_to_csv_basic(self):
        """Test basic JSON to CSV conversion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "test.json"
            csv_path = Path(tmp_dir) / "test.csv"
            
            # Create simple JSON
            data = [
                {
                    "type": "multiple",
                    "question": "What is 2+2?",
                    "correct": "4",
                    "wrong_answers": ["3", "5", "6"],
                    "pairs": {}
                }
            ]
            
            with open(json_path, 'w') as f:
                json.dump(data, f)
            
            # Convert
            json_to_csv(json_path, csv_path)
            
            # Check result
            assert csv_path.exists()
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['type'] == 'multiple'
            assert rows[0]['question'] == 'What is 2+2?'
            assert rows[0]['correct'] == '4'
    
    def test_json_to_csv_empty_list(self):
        """Test JSON to CSV with empty list."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "test.json"
            csv_path = Path(tmp_dir) / "test.csv"
            
            # Create empty JSON
            with open(json_path, 'w') as f:
                json.dump([], f)
            
            # Should raise ValueError for empty JSON
            with pytest.raises(ValueError, match="JSON is empty"):
                json_to_csv(json_path, csv_path)
    
    def test_json_to_csv_matching_question(self):
        """Test JSON to CSV with matching question."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "test.json"
            csv_path = Path(tmp_dir) / "test.csv"
            
            # Create JSON with matching question
            data = [
                {
                    "type": "match",
                    "question": "Match capitals",
                    "pairs": {
                        "left": ["Paris", "London"],
                        "right": ["France", "England"],
                        "answers": {"a": "1", "b": "2"}
                    }
                }
            ]
            
            with open(json_path, 'w') as f:
                json.dump(data, f)
            
            # Convert
            json_to_csv(json_path, csv_path)
            
            # Check result
            assert csv_path.exists()
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['type'] == 'match'
            assert rows[0]['question'] == 'Match capitals'
    
    def test_download_remote_creates_directories(self):
        """Test download creates parent directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "subdir" / "test.txt"
            
            # Create parent directory first
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mock requests response
            mock_response = MagicMock()
            mock_response.content = b"test data"
            
            with patch('requests.get', return_value=mock_response):
                result = download_remote("http://example.com/test", tmp_path, overwrite=True)
                assert result == tmp_path
                assert tmp_path.exists()
                assert tmp_path.read_bytes() == b"test data"
    
    def test_download_remote_request_error(self):
        """Test download with request error."""
        tmp_path = Path("/tmp/test_download")
        
        with patch('requests.get', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                download_remote("http://example.com/test", tmp_path)
    
    def test_csv_to_json_file_not_found(self):
        """Test CSV to JSON with non-existent file."""
        with pytest.raises(FileNotFoundError):
            csv_to_json(Path("/non/existent/file.csv"), Path("/tmp/output.json"))
    
    def test_json_to_csv_file_not_found(self):
        """Test JSON to CSV with non-existent file."""
        with pytest.raises(FileNotFoundError):
            json_to_csv(Path("/non/existent/file.json"), Path("/tmp/output.csv"))
    
    def test_json_to_csv_invalid_json(self):
        """Test JSON to CSV with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "test.json"
            csv_path = Path(tmp_dir) / "test.csv"
            
            # Create invalid JSON
            json_path.write_text('{"invalid": json}')
            
            # Should raise JSONDecodeError
            with pytest.raises(json.JSONDecodeError):
                json_to_csv(json_path, csv_path)
