import pytest
import json
import os
from unittest.mock import patch, mock_open
from qm2.utils.files import save_json, load_json, load_json_result

def test_load_json_result_not_found():
    """Covers lines where file does not exist."""
    with patch('os.path.exists', return_value=False):
        data, error = load_json_result("nonexistent.json")
        assert data == []
        assert "File not found" in error

def test_load_json_result_json_decode_error():
    """Covers lines 43-46: JSONDecodeError."""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('qm2.utils.files.console.print') as mock_print:
                data, error = load_json_result("bad.json")
                assert data == []
                assert "Invalid JSON" in error
                assert mock_print.called

def test_load_json_result_unicode_error():
    """Covers lines 47-50: UnicodeDecodeError."""
    with patch('os.path.exists', return_value=True):
        # We simulate UnicodeDecodeError by mocking open to raise it on read
        mock_file = mock_open()
        mock_file.return_value.__enter__.return_value.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "")
        
        with patch('builtins.open', mock_file):
            with patch('qm2.utils.files.console.print') as mock_print:
                # We need to trigger the error during json.load
                with patch('json.load', side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "")):
                    data, error = load_json_result("wrong_encoding.json")
                    assert data == []
                    assert "Encoding error" in error
                    assert mock_print.called

def test_load_json_result_os_error():
    """Covers lines 51-54: OSError during read."""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=OSError("Read failed")):
            with patch('qm2.utils.files.console.print') as mock_print:
                data, error = load_json_result("locked.json")
                assert data == []
                assert "Error reading" in error
                assert mock_print.called

def test_save_json_os_error():
    """Covers lines 70-73: OSError during save (e.g. Permission denied)."""
    with patch('os.makedirs'): # Prevent directory creation
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with patch('qm2.utils.files.console.print') as mock_print:
                result = save_json("readonly.json", {"test": "data"})
                assert result is False
                assert mock_print.called
                # Check for the actual error message format in your code
                args, _ = mock_print.call_args
                assert "Error saving file" in args[0]

def test_save_json_serialization_error():
    """Covers lines 74-77: TypeError during JSON serialization."""
    # Data that cannot be serialized to JSON (like a function)
    bad_data = {"func": lambda x: x}
    with patch('qm2.utils.files.console.print') as mock_print:
        # We don't need to mock open because json.dump fails before writing
        result = save_json("test.json", bad_data)
        assert result is False
        assert mock_print.called
        args, _ = mock_print.call_args
        assert "Error serializing data" in args[0]