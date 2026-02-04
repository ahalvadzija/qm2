"""
Tests for critical categories.py functions to improve coverage.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from qm2.core.categories import (
    create_new_category, delete_json_quiz_file
)


class TestCategoriesCritical:
    """Test critical categories functions."""
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    @patch('qm2.core.categories.save_json')
    @patch('qm2.core.categories.categories_add')
    @patch('qm2.core.categories.refresh_categories_cache')
    @patch('qm2.core.categories.os.makedirs')
    def test_create_new_category_success(self, mock_makedirs, mock_refresh, mock_add, 
                                        mock_save_json, mock_print, mock_ask):
        """Test successful category creation."""
        mock_ask.side_effect = ["programming/python", "test.json"]
        
        create_new_category()
        
        mock_makedirs.assert_called_once()
        mock_save_json.assert_called_once()
        mock_add.assert_called_once()
        mock_refresh.assert_called_once()
        mock_print.assert_called()
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    def test_create_new_category_invalid_folder_name(self, mock_print, mock_ask):
        """Test category creation with invalid folder name."""
        mock_ask.side_effect = ["invalid<name", "test.json"]
        
        create_new_category()
        
        mock_print.assert_called_with("[red]⚠️ Invalid folder name. Please avoid special characters.")
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    def test_create_new_category_empty_folder_name(self, mock_print, mock_ask):
        """Test category creation with empty folder name."""
        mock_ask.side_effect = ["", "test.json"]
        
        create_new_category()
        
        mock_print.assert_called_with("[red]⚠️ Invalid folder name. Please avoid special characters.")
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    def test_create_new_category_invalid_file_name(self, mock_print, mock_ask):
        """Test category creation with invalid file name."""
        mock_ask.side_effect = ["valid_folder", "invalid<name"]
        
        create_new_category()
        
        mock_print.assert_called_with("[red]⚠️ Invalid file name. Please avoid special characters.")
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    def test_create_new_category_empty_file_name(self, mock_print, mock_ask):
        """Test category creation with empty file name."""
        mock_ask.side_effect = ["valid_folder", ""]
        
        create_new_category()
        
        mock_print.assert_called_with("[red]⚠️ Invalid file name. Please avoid special characters.")
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    @patch('qm2.core.categories.save_json')
    @patch('qm2.core.categories.categories_add')
    @patch('qm2.core.categories.refresh_categories_cache')
    @patch('qm2.core.categories.os.makedirs')
    def test_create_new_category_without_json_extension(self, mock_makedirs, mock_refresh, mock_add, 
                                                     mock_save_json, mock_print, mock_ask):
        """Test category creation auto-adds .json extension."""
        mock_ask.side_effect = ["programming/python", "test"]  # No .json extension
        
        create_new_category()
        
        # Check that .json was added to the path
        mock_save_json.assert_called_once()
        save_path = mock_save_json.call_args[0][0]
        assert save_path.endswith('.json')
    
    @patch('qm2.core.categories.get_categories')
    @patch('qm2.core.categories.console.print')
    def test_delete_json_quiz_file_no_files(self, mock_print, mock_get_categories):
        """Test delete JSON file when no files available."""
        mock_get_categories.return_value = []
        
        delete_json_quiz_file()
        
        mock_print.assert_called_with("[yellow]⚠️ No .json files available to delete.")
    
    @patch('qm2.core.categories.get_categories')
    @patch('qm2.core.categories.questionary.select')
    def test_delete_json_quiz_file_back_selection(self, mock_select, mock_get_categories):
        """Test delete JSON file when user selects back."""
        mock_get_categories.return_value = ["test1.json", "test2.json"]
        mock_select.return_value.ask.return_value = "↩ Back"
        
        delete_json_quiz_file()
        
        mock_select.assert_called_once()
    
    @patch('qm2.core.categories.get_categories')
    @patch('qm2.core.categories.questionary.select')
    @patch('qm2.core.categories.questionary.confirm')
    @patch('qm2.core.categories.os.remove')
    @patch('qm2.core.categories.categories_remove')
    @patch('qm2.core.categories.refresh_categories_cache')
    @patch('qm2.core.categories.console.print')
    @patch('qm2.core.categories.categories_root_dir')
    def test_delete_json_quiz_file_success(self, mock_root_dir, mock_print, mock_refresh, mock_remove, 
                                          mock_categories_remove, mock_confirm, mock_select, mock_get_categories):
        """Test successful JSON file deletion."""
        mock_get_categories.return_value = ["test1.json", "test2.json"]
        mock_select.return_value.ask.return_value = "test1.json"
        mock_confirm.return_value.ask.return_value = True
        mock_root_dir.return_value = "/test/root"
        
        delete_json_quiz_file()
        
        # os.remove gets the full path
        mock_remove.assert_called_once()
        remove_path = mock_remove.call_args[0][0]
        assert remove_path.endswith("test1.json")
        
        # categories_remove gets the full path (choice is converted to full path)
        mock_categories_remove.assert_called_once()
        # The function is called with the full path, not just filename
        assert mock_categories_remove.call_args[0][0].endswith("test1.json")
        
        mock_refresh.assert_called_once()
        mock_print.assert_called_with("[red]🗑️ File 'test1.json' deleted.")
    
    @patch('qm2.core.categories.get_categories')
    @patch('qm2.core.categories.questionary.select')
    @patch('qm2.core.categories.questionary.confirm')
    @patch('qm2.core.categories.console.print')
    def test_delete_json_quiz_file_cancel(self, mock_print, mock_confirm, mock_select, mock_get_categories):
        """Test delete JSON file when user cancels."""
        mock_get_categories.return_value = ["test1.json", "test2.json"]
        mock_select.return_value.ask.return_value = "test1.json"
        mock_confirm.return_value.ask.return_value = False
        
        delete_json_quiz_file()
        
        mock_print.assert_called_with("[yellow]↩ Deletion canceled.")
    
    @patch('qm2.core.categories.get_categories')
    @patch('qm2.core.categories.questionary.select')
    @patch('qm2.core.categories.questionary.confirm')
    @patch('qm2.core.categories.os.remove')
    @patch('qm2.core.categories.console.print')
    def test_delete_json_quiz_file_permission_error(self, mock_print, mock_remove, 
                                                   mock_confirm, mock_select, mock_get_categories):
        """Test delete JSON file with permission error."""
        mock_get_categories.return_value = ["test1.json", "test2.json"]
        mock_select.return_value.ask.return_value = "test1.json"
        mock_confirm.return_value.ask.return_value = True
        mock_remove.side_effect = PermissionError("Permission denied")
        
        delete_json_quiz_file()
        
        mock_print.assert_called()
        # Check that error message contains "Error deleting file"
        error_call = mock_print.call_args_list[-1]
        assert "Error deleting file" in str(error_call)
    
    @patch('qm2.core.categories.get_categories')
    @patch('qm2.core.categories.questionary.select')
    @patch('qm2.core.categories.questionary.confirm')
    @patch('qm2.core.categories.os.remove')
    @patch('qm2.core.categories.console.print')
    def test_delete_json_quiz_file_file_not_found(self, mock_print, mock_remove, 
                                                   mock_confirm, mock_select, mock_get_categories):
        """Test delete JSON file when file doesn't exist."""
        mock_get_categories.return_value = ["test1.json", "test2.json"]
        mock_select.return_value.ask.return_value = "test1.json"
        mock_confirm.return_value.ask.return_value = True
        mock_remove.side_effect = FileNotFoundError("File not found")
        
        delete_json_quiz_file()
        
        mock_print.assert_called()
        # Check that error message contains "Error deleting file"
        error_call = mock_print.call_args_list[-1]
        assert "Error deleting file" in str(error_call)
    
    @patch('qm2.core.categories.Prompt.ask')
    @patch('qm2.core.categories.console.print')
    @patch('qm2.core.categories.save_json')
    @patch('qm2.core.categories.categories_add')
    @patch('qm2.core.categories.refresh_categories_cache')
    @patch('qm2.core.categories.os.makedirs')
    def test_create_new_category_save_json_error(self, mock_makedirs, mock_refresh, mock_add, 
                                                 mock_save_json, mock_print, mock_ask):
        """Test category creation when save_json fails."""
        mock_ask.side_effect = ["programming/python", "test.json"]
        mock_save_json.return_value = False
        
        create_new_category()
        
        # Should handle the error gracefully
        mock_save_json.assert_called_once()
        # Note: categories_add is still called even if save_json fails
        # This is the actual behavior of the function
