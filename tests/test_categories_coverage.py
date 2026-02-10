import os
from unittest.mock import patch
import qm2.core.categories as categories
from qm2.core.categories import rename_category


def test_create_category_directory_structure(tmp_path):
    """Test that creating a new category creates proper directory structure."""
    with patch('qm2.core.categories.categories_root_dir', return_value=str(tmp_path)):
        with patch('qm2.core.categories.questionary.select') as mock_select:
            with patch('qm2.core.categories.Prompt.ask') as mock_ask:
                with patch('qm2.core.categories.save_json') as mock_save:
                    # Mock user selecting "Create new"
                    mock_select.return_value.ask.return_value = "➕ Create new"
                    # Mock user entering category name
                    mock_ask.return_value = "test_category.json"
                    
                    result = categories.select_category(allow_create=True)
                    
                    # Verify the path is constructed correctly
                    expected_path = os.path.join(str(tmp_path), "test_category.json")
                    assert result == expected_path
                    
                    # Verify save_json was called with empty list
                    mock_save.assert_called_once_with(expected_path, [])


def test_delete_category_file_and_update_cache(tmp_path):
    """Test deleting a category file and updating cache."""
    # Create a test category file
    test_file = tmp_path / "test_category.json"
    test_file.write_text('[]')
    
    with patch('qm2.core.categories.categories_root_dir', return_value=str(tmp_path)):
        with patch('qm2.core.categories.get_categories', return_value=["test_category.json"]):
            with patch('qm2.core.categories.questionary.select') as mock_select:
                with patch('qm2.core.categories.questionary.confirm') as mock_confirm:
                    with patch('os.remove') as mock_remove:
                        # Mock user selecting the test file
                        mock_select.return_value.ask.return_value = "test_category.json"
                        # Mock user confirming deletion
                        mock_confirm.return_value.ask.return_value = True
                        
                        categories.delete_category()
                        
                        # Verify file removal was attempted
                        mock_remove.assert_called_once_with(str(test_file))


def test_rename_category_with_validation(tmp_path):
    """Test renaming a category with proper validation."""
    # Create a test category file
    old_file = tmp_path / "old_category.json"
    old_file.write_text('[]')
    
    with patch('qm2.core.categories.categories_root_dir', return_value=str(tmp_path)):
        with patch('qm2.core.categories.get_categories', return_value=["old_category.json"]):
            with patch('qm2.core.categories.questionary.select') as mock_select:
                with patch('qm2.core.categories.Prompt.ask') as mock_ask:
                    with patch('os.rename') as mock_rename:
                        # Mock user selecting the old file
                        mock_select.return_value.ask.return_value = "old_category.json"
                        # Mock user entering new name
                        mock_ask.return_value = "new_category"
                        
                        categories.rename_category()
                        
                        # Verify rename was called with correct paths
                        expected_old = str(old_file)
                        expected_new = str(tmp_path / "new_category.json")
                        mock_rename.assert_called_once_with(expected_old, expected_new)


def test_invalid_category_name_validation():
    """Tests that forbidden characters in category names are rejected by validation."""
    # List of invalid inputs to test (including the newly added forbidden characters)
    invalid_names = ["test<name", "test>name", "test:name", "test|name", "test/name", "test\\name"]
    
    # Mock both the category selection and the prompt for new name
    with patch('qm2.core.categories.get_categories', return_value=["some_file.json"]), \
         patch('qm2.core.categories.select_with_pagination', return_value="some_file.json"), \
         patch('qm2.core.categories.Prompt.ask') as mock_ask, \
         patch('qm2.core.categories.console.print') as mock_print:
        
        for invalid_name in invalid_names:
            mock_ask.return_value = invalid_name
            rename_category()
            
            # Aggregate all console output to verify validation message
            all_output = "".join([str(call) for call in mock_print.call_args_list])
            assert "Invalid" in all_output or "avoid special characters" in all_output


def test_category_cache_operations(tmp_path):
    """Test category cache refresh and operations."""
    # Create some test category files
    (tmp_path / "cat1.json").write_text('[]')
    (tmp_path / "cat2.json").write_text('[]')
    (tmp_path / "not_a_category.txt").write_text('test')
    
    with patch('qm2.core.categories.categories_root_dir', return_value=str(tmp_path)):
        # Test cache refresh
        categories.refresh_categories_cache(str(tmp_path))
        
        # Test get_categories returns only .json files
        result = categories.get_categories(use_cache=False)
        assert len(result) == 2
        assert "cat1.json" in result
        assert "cat2.json" in result
        assert "not_a_category.txt" not in result
