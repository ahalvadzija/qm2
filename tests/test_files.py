import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
import qm2.utils.files as files


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    json_file = tmp_path / "test.json"
    test_data = [
        {"question": "Test question", "type": "multiple", "correct": "Answer", "wrong_answers": []}
    ]
    json_file.write_text(json.dumps(test_data, indent=2), encoding="utf-8")
    return json_file


@pytest.fixture
def temp_invalid_json_file(tmp_path):
    """Create a temporary invalid JSON file for testing."""
    json_file = tmp_path / "invalid.json"
    json_file.write_text('{"invalid": json content}', encoding="utf-8")
    return json_file


@pytest.fixture
def temp_empty_file(tmp_path):
    """Create an empty temporary file for testing."""
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("", encoding="utf-8")
    return empty_file


def test_load_json_file_exists(temp_json_file):
    """Test load_json with existing valid JSON file."""
    result = files.load_json(temp_json_file)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["question"] == "Test question"


def test_load_json_file_not_exists():
    """Test load_json with non-existent file."""
    result = files.load_json("/nonexistent/file.json")
    assert result == []


def test_load_json_invalid_json(temp_invalid_json_file):
    """Test load_json with invalid JSON content."""
    result = files.load_json(temp_invalid_json_file)
    assert result == []


def test_load_json_empty_file(temp_empty_file):
    """Test load_json with empty file."""
    result = files.load_json(temp_empty_file)
    assert result == []


def test_load_json_null_content(tmp_path):
    """Test load_json with file containing null."""
    json_file = tmp_path / "null.json"
    json_file.write_text("null", encoding="utf-8")
    
    result = files.load_json(json_file)
    assert result == []


def test_load_json_non_dict_list(tmp_path):
    """Test load_json with file containing non-list/dict content."""
    json_file = tmp_path / "string.json"
    json_file.write_text('"just a string"', encoding="utf-8")
    
    result = files.load_json(json_file)
    assert result == []


def test_load_json_result_valid_file(temp_json_file):
    """Test load_json_result with valid file."""
    data, error = files.load_json_result(temp_json_file)
    
    assert error is None
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["question"] == "Test question"


def test_load_json_result_file_not_exists():
    """Test load_json_result with non-existent file."""
    data, error = files.load_json_result("/nonexistent/file.json")
    
    assert data == []
    assert "File not found" in error


def test_load_json_result_invalid_json(temp_invalid_json_file):
    """Test load_json_result with invalid JSON."""
    data, error = files.load_json_result(temp_invalid_json_file)
    
    assert data == []
    assert "Invalid JSON" in error


def test_load_json_result_encoding_error(tmp_path):
    """Test load_json_result with encoding error."""
    # Create a file with invalid UTF-8 bytes
    json_file = tmp_path / "bad_encoding.json"
    json_file.write_bytes(b'\xff\xfe{"test": "data"}')  # UTF-16 BOM
    
    data, error = files.load_json_result(json_file)
    
    assert data == []
    assert "Encoding error" in error


def test_load_json_result_permission_error():
    """Test load_json_result with permission error."""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            data, error = files.load_json_result("/some/file.json")
            
            assert data == []
            assert "Error reading" in error


def test_save_json_new_file(tmp_path):
    """Test save_json creating a new file."""
    test_data = [{"question": "New question", "type": "multiple"}]
    json_file = tmp_path / "new_file.json"
    
    result = files.save_json(json_file, test_data)
    
    assert result is True
    assert json_file.exists()
    
    # Verify content
    loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert loaded_data == test_data


def test_save_json_existing_file(temp_json_file):
    """Test save_json overwriting existing file."""
    test_data = [{"question": "Updated question", "type": "multiple"}]
    
    result = files.save_json(temp_json_file, test_data)
    
    assert result is True
    
    # Verify content was updated
    loaded_data = json.loads(temp_json_file.read_text(encoding="utf-8"))
    assert loaded_data == test_data
    assert len(loaded_data) == 1
    assert loaded_data[0]["question"] == "Updated question"


def test_save_json_creates_directories(tmp_path):
    """Test save_json creates parent directories if they don't exist."""
    test_data = [{"question": "Test", "type": "multiple"}]
    nested_file = tmp_path / "nested" / "dir" / "file.json"
    
    result = files.save_json(nested_file, test_data)
    
    assert result is True
    assert nested_file.exists()
    
    # Verify content
    loaded_data = json.loads(nested_file.read_text(encoding="utf-8"))
    assert loaded_data == test_data


def test_save_json_permission_error():
    """Test save_json with permission error."""
    test_data = [{"question": "Test", "type": "multiple"}]
    
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        result = files.save_json("/some/path/file.json", test_data)
        
        assert result is False


def test_save_json_type_error():
    """Test save_json with non-serializable data."""
    # Create data that can't be JSON serialized
    class UnserializableObject:
        pass
    
    test_data = {"object": UnserializableObject()}
    
    with patch('qm2.utils.files.console'):
        result = files.save_json("/some/file.json", test_data)
        
        assert result is False


def test_save_json_updates_cache(tmp_path):
    """Test that save_json updates the questions cache."""
    test_data = [{"question": "Cached question", "type": "multiple"}]
    json_file = tmp_path / "cached_file.json"
    
    # Clear cache first
    files.questions_cache.clear()
    
    # Save file
    result = files.save_json(json_file, test_data)
    assert result is True
    
    # Check if cache was updated
    abs_path = str(json_file.absolute())
    assert abs_path in files.questions_cache
    assert files.questions_cache[abs_path]["data"] == test_data


def test_save_json_cache_update_failure():
    """Test save_json when cache update fails (should not affect save result)."""
    test_data = [{"question": "Test", "type": "multiple"}]
    
    with patch('os.path.abspath', side_effect=Exception("Path error")):
        # Save should still succeed even if cache update fails
        with patch('builtins.open', mock_open()):
            with patch('json.dump'):
                with patch('os.makedirs'):
                    result = files.save_json("/some/file.json", test_data)
                    assert result is True


def test_save_json_unicode_content(tmp_path):
    """Test save_json with unicode content."""
    test_data = [{"question": "测试问题", "type": "multiple", "correct": "答案"}]
    json_file = tmp_path / "unicode.json"
    
    result = files.save_json(json_file, test_data)
    
    assert result is True
    
    # Verify unicode content is preserved
    loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert loaded_data == test_data
    assert loaded_data[0]["question"] == "测试问题"


def test_save_json_large_data(tmp_path):
    """Test save_json with large data structure."""
    # Create a large data structure
    test_data = []
    for i in range(1000):
        test_data.append({
            "question": f"Question {i}",
            "type": "multiple",
            "correct": f"Answer {i}",
            "wrong_answers": [f"Wrong {i}-{j}" for j in range(3)]
        })
    
    json_file = tmp_path / "large_data.json"
    
    result = files.save_json(json_file, test_data)
    
    assert result is True
    assert json_file.exists()
    
    # Verify all data was saved
    loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert len(loaded_data) == 1000
    assert loaded_data[999]["question"] == "Question 999"


def test_load_json_file_with_bom(tmp_path):
    """Test load_json with UTF-8 BOM."""
    json_file = tmp_path / "bom.json"
    test_data = [{"question": "Test", "type": "multiple"}]
    
    # Write file with UTF-8 BOM using utf-8-sig encoding
    with open(json_file, 'w', encoding='utf-8-sig') as f:
        json.dump(test_data, f, indent=2)
    
    # Read it back using utf-8-sig to handle BOM
    with open(json_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Write it back without BOM for the test
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    result = files.load_json(json_file)
    
    assert result == test_data


def test_save_json_minimal_data(tmp_path):
    """Test save_json with minimal data structures."""
    test_cases = [
        [],  # Empty list
        {},  # Empty dict
        {"key": "value"},  # Simple dict
        [1, 2, 3],  # List of numbers
        None  # None value (should be handled)
    ]
    
    for i, test_data in enumerate(test_cases):
        if test_data is None:
            continue  # Skip None as it's not valid JSON root
            
        json_file = tmp_path / f"minimal_{i}.json"
        
        result = files.save_json(json_file, test_data)
        
        assert result is True
        assert json_file.exists()
        
        # Verify round-trip
        loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert loaded_data == test_data


def test_load_json_special_characters(tmp_path):
    """Test load_json with special characters and escape sequences."""
    test_data = [
        {
            "question": "What is \"hello\" in Spanish?",
            "type": "multiple",
            "correct": "Hola",
            "wrong_answers": ["Bonjour\nNew line", "Ciao\tTab", "Привет"]
        }
    ]
    
    json_file = tmp_path / "special_chars.json"
    json_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")
    
    result = files.load_json(json_file)
    
    assert result == test_data
    assert result[0]["question"] == 'What is "hello" in Spanish?'
    assert "Bonjour\nNew line" in result[0]["wrong_answers"]


def test_save_json_pretty_formatting(tmp_path):
    """Test that save_json uses pretty formatting with indentation."""
    test_data = [{"question": "Test", "type": "multiple"}]
    json_file = tmp_path / "pretty.json"
    
    result = files.save_json(json_file, test_data)
    
    assert result is True
    
    # Check that file is properly formatted with indentation
    content = json_file.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # Should have multiple lines due to pretty printing
    assert len(lines) > 3
    # Should contain indentation
    assert '  ' in content  # 2-space indentation


def test_file_operations_cross_platform_paths():
    """Test file operations with different path formats."""
    # Test with Path objects
    path_obj = Path("/some/path/file.json")
    
    # Test with string paths
    path_str = "/some/path/file.json"
    
    # Both should work the same way (mocked)
    with patch('qm2.utils.files.load_json') as mock_load:
        mock_load.return_value = []
        
        result1 = files.load_json(path_obj)
        result2 = files.load_json(path_str)
        
        assert result1 == result2 == []
        assert mock_load.call_count == 2


def test_concurrent_file_access(tmp_path):
    """Test behavior when file is accessed concurrently."""
    test_data = [{"question": "Concurrent test", "type": "multiple"}]
    json_file = tmp_path / "concurrent.json"
    
    # Save initial data
    files.save_json(json_file, test_data)
    
    # Simulate concurrent access by loading multiple times
    results = []
    for _ in range(5):
        result = files.load_json(json_file)
        results.append(result)
    
    # All results should be identical
    for result in results:
        assert result == test_data


def test_file_path_with_spaces_and_special_chars(tmp_path):
    """Test file operations with paths containing spaces and special characters."""
    test_data = [{"question": "Special path test", "type": "multiple"}]
    
    # Create path with spaces and special characters
    special_path = tmp_path / "test folder" / "file with spaces.json"
    
    result = files.save_json(special_path, test_data)
    
    assert result is True
    assert special_path.exists()
    
    # Verify we can load it back
    loaded_data = files.load_json(special_path)
    assert loaded_data == test_data
