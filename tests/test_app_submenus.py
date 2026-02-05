"""
Unit tests for app.py submenu functions to improve coverage for lines 189-244 and 296-325.
"""

import pytest
import tempfile
from unittest.mock import patch
from pathlib import Path

from qm2.app import _handle_questions_submenu, _handle_questions_menu, _handle_tools_menu, _handle_csv_to_json


@pytest.mark.timeout(5)
class TestAppSubmenus:
    """Unit tests for app.py submenu functions to improve coverage."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @patch('qm2.app.questionary.select')
    def test_questions_submenu_show_all_questions(self, mock_select):
        """Test showing all questions in submenu."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]},
            {"question": "Test 2", "correct": "B", "wrong_answers": ["A", "C"]}
        ]
        
        # Mock menu selection: Show all questions, then Back
        mock_select.return_value.ask.side_effect = ["📚 Show all questions", "↩ Back"]
        
        with patch('qm2.app.show_questions_paginated') as mock_show:
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify show was called and questions unchanged
            mock_show.assert_called_once_with(questions, title="📚 Questions", page_size=25)
            assert result == questions
    
    @patch('qm2.app.questionary.select')
    def test_questions_submenu_show_empty_questions(self, mock_select):
        """Test showing empty questions list."""
        questions = []
        
        # Mock menu selection: Show all questions, then Back
        mock_select.return_value.ask.side_effect = ["📚 Show all questions", "↩ Back"]
        
        with patch('qm2.app.console.print') as mock_print:
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify warning message and questions unchanged
            mock_print.assert_called_with("[yellow]⚠️ No questions in this category.")
            assert result == questions
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.Prompt.ask')
    def test_questions_submenu_edit_by_number(self, mock_prompt, mock_select):
        """Test editing question by number."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]},
            {"question": "Test 2", "correct": "B", "wrong_answers": ["A", "C"]}
        ]
        
        # Mock menu selection: Edit by number, then Back
        mock_select.return_value.ask.side_effect = ["🔢 Edit by number", "↩ Back"]
        # Mock user input: question number 1
        mock_prompt.return_value = "1"
        
        with patch('qm2.app.edit_question_by_index') as mock_edit:
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify edit was called with correct arguments (questions, index)
            mock_edit.assert_called_once_with(questions, 1)
            assert result == questions
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.Prompt.ask')
    def test_questions_submenu_edit_by_number_invalid(self, mock_prompt, mock_select):
        """Test editing question with invalid number."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]}
        ]
        
        # Mock menu selection: Edit by number, then Back
        mock_select.return_value.ask.side_effect = ["🔢 Edit by number", "↩ Back"]
        # Mock user input: invalid number
        mock_prompt.return_value = "invalid"
        
        with patch('qm2.app.edit_question_by_index') as mock_edit:
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify edit was not called
            mock_edit.assert_not_called()
            assert result == questions
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.Prompt.ask')
    def test_questions_submenu_delete_by_number(self, mock_prompt, mock_select):
        """Test deleting question by number."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]},
            {"question": "Test 2", "correct": "B", "wrong_answers": ["A", "C"]}
        ]
        
        # Mock menu selection: Delete by number, then Back
        mock_select.return_value.ask.side_effect = ["🔢 Delete by number", "↩ Back"]
        # Mock user input: question number 1
        mock_prompt.return_value = "1"
        
        with patch('qm2.app.delete_question_by_index') as mock_delete:
            with patch('qm2.app.get_questions') as mock_get:
                mock_get.return_value = questions  # Return same questions after deletion
                
                result = _handle_questions_submenu("test.json", questions)
                
                # Verify delete was called with correct arguments (filename, index)
                mock_delete.assert_called_once_with("test.json", 1)
                assert result == questions
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.Prompt.ask')
    def test_questions_submenu_add_question(self, mock_prompt, mock_select):
        """Test adding a new question."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]}
        ]
        
        # Mock menu selection: Add question, then Back
        mock_select.return_value.ask.side_effect = ["➕ Add question", "↩ Back"]
        # Mock create_question to return a valid question
        mock_prompt.return_value = "Test question"
        
        with patch('qm2.app.create_question') as mock_add:
            mock_add.return_value = {"question": "New Q", "correct": "C", "wrong_answers": ["A", "B"]}
            
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify add was called
            mock_add.assert_called_once()
            assert len(result) == 2  # Original + new question
    
    @patch('qm2.app.questionary.select')
    def test_questions_submenu_edit_question(self, mock_select):
        """Test editing existing question."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]}
        ]
        
        # Mock menu selection: Edit question, then Back
        mock_select.return_value.ask.side_effect = ["📝 Edit question", "↩ Back"]
        
        with patch('qm2.app.edit_question') as mock_edit:
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify edit was called
            mock_edit.assert_called_once_with(questions)
            assert result == questions
    
    @patch('qm2.app.questionary.select')
    def test_questions_submenu_delete_question(self, mock_select):
        """Test deleting existing question."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]}
        ]
        
        # Mock menu selection: Delete question, then Back
        mock_select.return_value.ask.side_effect = ["🗑️ Delete question", "↩ Back"]
        
        with patch('qm2.app.delete_question') as mock_delete:
            with patch('qm2.app.get_questions') as mock_get:
                mock_get.return_value = questions  # Return same questions after deletion
                
                result = _handle_questions_submenu("test.json", questions)
                
                # Verify delete was called with filename
                mock_delete.assert_called_once_with("test.json")
                assert result == questions
    
    @patch('qm2.app.questionary.select')
    def test_questions_submenu_save_questions(self, mock_select):
        """Test saving questions."""
        questions = [
            {"question": "Test 1", "correct": "A", "wrong_answers": ["B", "C"]}
        ]
        
        # Mock menu selection: Save questions, then Back
        mock_select.return_value.ask.side_effect = ["💾 Save questions", "↩ Back"]
        
        with patch('qm2.app.save_json') as mock_save:
            result = _handle_questions_submenu("test.json", questions)
            
            # Verify save was called with filename and questions
            mock_save.assert_called_once_with("test.json", questions)
            assert result == questions
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.Prompt.ask')
    def test_questions_menu_no_categories(self, mock_prompt, mock_select):
        """Test questions menu when no categories exist."""
        # Mock get_categories to return empty list
        with patch('qm2.app.get_categories') as mock_get:
            mock_get.return_value = []
            
            # Mock any Prompt.ask calls to prevent hanging
            mock_prompt.return_value = ""
            
            # Mock all questionary.select calls to prevent hanging
            mock_select.return_value.ask.return_value = "↩ Back"
            
            with patch('qm2.app.console.print') as mock_print:
                _handle_questions_menu()
                
                # Debug: See what mock_print actually received
                print(f"DEBUG: Calls received: {mock_print.call_args_list}")
                
                # Verify any warning message about no categories (less sensitive to emojis)
                assert any('No categories found.' in str(call) for call in mock_print.call_args_list)
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.Prompt.ask')
    def test_questions_menu_back_to_main(self, mock_prompt, mock_select):
        """Test questions menu back to main."""
        # Mock get_categories and menu selection
        with patch('qm2.app.get_categories') as mock_get:
            mock_get.return_value = ["test.json"]
            
            # Mock menu selection: Back
            mock_select.return_value.ask.side_effect = ["↩ Back"]
            
            # Mock any Prompt.ask calls to prevent hanging
            mock_prompt.return_value = ""
            
            _handle_questions_menu()
            
            # Should exit without loading questions
    
    @patch('qm2.app.questionary.select')
    def test_tools_menu_csv_to_json(self, mock_select):
        """Test tools menu CSV to JSON conversion."""
        # Mock menu selection: CSV to JSON, then Back
        mock_select.return_value.ask.side_effect = ["🧾 Convert CSV to JSON", "↩ Back"]
        
        with patch('qm2.app._handle_csv_to_json') as mock_convert:
            _handle_tools_menu()
            
            # Verify conversion function was called
            mock_convert.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    def test_tools_menu_json_to_csv(self, mock_select):
        """Test tools menu JSON to CSV conversion."""
        # Mock menu selection: JSON to CSV, then Back
        mock_select.return_value.ask.side_effect = ["📤 Export JSON to CSV", "↩ Back"]
        
        with patch('qm2.app._handle_json_to_csv') as mock_export:
            _handle_tools_menu()
            
            # Verify export function was called
            mock_export.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    def test_tools_menu_create_csv_template(self, mock_select):
        """Test tools menu create CSV template."""
        # Mock menu selection: Create CSV template, then Back
        mock_select.return_value.ask.side_effect = ["📄 Create CSV template", "↩ Back"]
        
        with patch('qm2.app.create_csv_template') as mock_template:
            with patch('qm2.app.refresh_csv_cache') as mock_refresh:
                with patch('qm2.app.console.print'):
                    _handle_tools_menu()
                    
                    # Verify template function was called
                    mock_template.assert_called_once()
                    mock_refresh.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    def test_tools_menu_create_json_template(self, mock_select):
        """Test tools menu create JSON template."""
        # Mock menu selection: Create JSON template, then Back
        mock_select.return_value.ask.side_effect = ["📄 Create JSON template", "↩ Back"]
        
        with patch('qm2.app.create_json_template') as mock_template:
            with patch('qm2.app.refresh_categories_cache') as mock_refresh:
                with patch('qm2.app.console.print'):
                    _handle_tools_menu()
                    
                    # Verify template function was called
                    mock_template.assert_called_once()
                    mock_refresh.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    def test_tools_menu_import_remote(self, mock_select):
        """Test tools menu import remote file."""
        # Mock menu selection: Import remote, then Back
        mock_select.return_value.ask.side_effect = ["🌐 Import remote CSV/JSON", "↩ Back"]
        
        with patch('qm2.app.import_remote_file') as mock_import:
            _handle_tools_menu()
            
            # Verify import function was called
            mock_import.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    def test_tools_menu_back_to_main(self, mock_select):
        """Test tools menu back to main."""
        # Mock menu selection: Back
        mock_select.return_value.ask.side_effect = ["↩ Back"]
        
        _handle_tools_menu()
        
        # Should exit immediately
    
    def test_handle_csv_to_json_success(self, temp_dir):
        """Test successful CSV to JSON conversion."""
        # Mock all OS operations
        with patch('qm2.app.os.listdir') as mock_listdir:
            with patch('qm2.app.os.makedirs'):
                with patch('qm2.app.questionary.select') as mock_select:
                    with patch('qm2.app.Prompt.ask') as mock_prompt:
                        with patch('qm2.app.is_file_valid') as mock_valid:
                            with patch('qm2.app.core_csv_to_json') as mock_convert:
                                with patch('qm2.app.categories_add') as mock_add:
                                    with patch('qm2.app.refresh_categories_cache') as mock_refresh:
                                        with patch('qm2.app.categories_root_dir') as mock_root:
                                            with patch('qm2.app.console.print'):
                                                with patch('qm2.app.paths') as mock_paths:
                                                    # Mock CSV files
                                                    mock_listdir.return_value = ["test.csv"]
                                                    
                                                    # Mock menu selections
                                                    mock_select.return_value.ask.side_effect = ["test.csv"]
                                                    # Mock folder input
                                                    mock_prompt.return_value = "history"
                                                    
                                                    # Mock validation success
                                                    mock_valid.return_value = True
                                                    
                                                    # Mock paths to use temp directory
                                                    mock_paths.CSV_DIR = temp_dir
                                                    mock_root.return_value = str(temp_dir)
                                                    
                                                    _handle_csv_to_json()
                                                    
                                                    # Verify all steps were called
                                                    mock_valid.assert_called_once()
                                                    mock_convert.assert_called_once()
                                                    mock_add.assert_called_once()
                                                    mock_refresh.assert_called_once()
    
    def test_handle_csv_to_json_no_files(self, temp_dir):
        """Test CSV to JSON when no CSV files exist."""
        # Mock all OS operations
        with patch('qm2.app.os.listdir') as mock_listdir:
            with patch('qm2.app.questionary.select'):
                with patch('qm2.app.console.print') as mock_print:
                    with patch('qm2.app.paths') as mock_paths:
                        # Mock no CSV files
                        mock_listdir.return_value = []
                        
                        # Mock paths to use temp directory
                        mock_paths.CSV_DIR = temp_dir
                        
                        _handle_csv_to_json()
                        
                        # Verify no files message
                        mock_print.assert_called_with("[red]⚠️ No CSV files found.")
    
    def test_handle_csv_to_json_back_selection(self, temp_dir):
        """Test CSV to JSON when user selects Back."""
        # Mock all OS operations
        with patch('qm2.app.os.listdir') as mock_listdir:
            with patch('qm2.app.questionary.select') as mock_select:
                with patch('qm2.app.console.print'):
                    with patch('qm2.app.paths') as mock_paths:
                        # Mock CSV files
                        mock_listdir.return_value = ["test.csv"]
                        
                        # Mock menu selection: Back
                        mock_select.return_value.ask.side_effect = ["↩ Back"]
                        
                        # Mock paths to use temp directory
                        mock_paths.CSV_DIR = temp_dir
                        
                        _handle_csv_to_json()
                        
                        # Should exit without processing
    
    def test_handle_csv_to_json_validation_failed(self, temp_dir):
        """Test CSV to JSON when validation fails."""
        # Mock all OS operations
        with patch('qm2.app.os.listdir') as mock_listdir:
            with patch('qm2.app.os.makedirs'):
                with patch('qm2.app.questionary.select') as mock_select:
                    with patch('qm2.app.Prompt.ask') as mock_prompt:
                        with patch('qm2.app.is_file_valid') as mock_valid:
                            with patch('qm2.app.categories_root_dir') as mock_root:
                                with patch('qm2.app.console.print') as mock_print:
                                    with patch('qm2.app.paths') as mock_paths:
                                        # Mock CSV files
                                        mock_listdir.return_value = ["test.csv"]
                                                    
                                        # Mock menu selections
                                        mock_select.return_value.ask.side_effect = ["test.csv"]
                                        # Mock folder input
                                        mock_prompt.return_value = ""
                                                    
                                        # Mock validation failure
                                        mock_valid.return_value = False
                                                    
                                        # Mock paths to use temp directory
                                        mock_paths.CSV_DIR = temp_dir
                                        mock_root.return_value = str(temp_dir)
                                                    
                                        _handle_csv_to_json()
                                                    
                                        # Verify validation error message
                                        mock_print.assert_any_call("[red]❌ CSV validation failed. Please fix the errors and try again.[/red]")
