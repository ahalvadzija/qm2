from unittest.mock import patch
from qm2.core.categories import (
    delete_json_quiz_file, 
    categories_add, 
    get_categories as categories_get_all,
    create_new_category, 
    rename_category
)

def test_delete_json_quiz_file_permission_denied():
    """Tests PermissionError when deleting a category file."""
    # We must patch select_with_pagination where it is USED (in core.categories)
    # This prevents the function from trying to open a real terminal menu
    with patch('qm2.core.categories.get_categories', return_value=["test.json"]), \
         patch('qm2.core.categories.select_with_pagination', return_value="test.json"), \
         patch('qm2.core.categories.questionary.confirm') as mock_conf, \
         patch('qm2.core.categories.console.print') as mock_print, \
         patch('os.remove', side_effect=PermissionError("Permission denied")):
        
        # Simulate user confirming the deletion via questionary
        mock_conf.return_value.ask.return_value = True
        
        # Execute the function that we are testing
        delete_json_quiz_file()
        
        # Verify that the error message was printed to the Rich console
        args, _ = mock_print.call_args
        assert "Error" in args[0] and "Permission denied" in args[0]

def test_categories_add_internal_logic():
    """Directly tests the addition and cache synchronization."""
    mock_cache = []
    # Patch the global cache list inside the module
    with patch('qm2.core.categories.categories_cache', mock_cache):
        categories_add("test_quiz.json")
        # Verify it was added to the cache
        assert "test_quiz.json" in categories_get_all()

def test_create_new_category_invalid_names():
    """Covers validation logic for special characters in folder and file names."""
    with patch('qm2.core.categories.Prompt.ask') as mock_prompt, \
         patch('qm2.core.categories.console.print') as mock_print:
        
        # Scenario 1: Invalid folder name
        mock_prompt.return_value = "invalid:folder"
        create_new_category()
        
        args1, _ = mock_print.call_args_list[0]
        assert "Invalid folder name" in args1[0]
        
        # Scenario 2: Valid folder, but invalid file name
        mock_prompt.side_effect = ["valid_folder", "bad*file.json"]
        create_new_category()
        
        args2, _ = mock_print.call_args_list[1]
        assert "Invalid file name" in args2[0]

def test_rename_category_invalid_input():
    """Covers validation logic when renaming a category with forbidden characters."""
    # Patch select_with_pagination to return the file we want to rename
    with patch('qm2.core.categories.get_categories', return_value=["test.json"]), \
         patch('qm2.core.categories.select_with_pagination', return_value="test.json"), \
         patch('qm2.core.categories.Prompt.ask') as mock_prompt, \
         patch('qm2.core.categories.console.print') as mock_print, \
         patch('os.rename'): 
        
        # Provide a name with a forbidden character '/'
        # Our new validation should catch this
        mock_prompt.return_value = "illegal/name"
        
        rename_category()
        
        # Collect all printed output to check for validation error
        all_printed = "".join([str(call) for call in mock_print.call_args_list])
        
        # Verify that our validation caught the illegal character
        assert "Invalid characters" in all_printed or "Invalid file name" in all_printed