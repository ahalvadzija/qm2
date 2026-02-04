"""
Final coverage tests for app.py to push project to 85%+ total coverage.
Tests main menu navigation, help, exit, and diagnose functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from qm2.app import main
from qm2.diagnose import main as diagnose_main


class TestAppCoverage:
    """Additional tests for app.py to improve overall project coverage."""
    
    def test_main_menu_help_option(self):
        """Test main menu help option navigation."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_help') as mock_help:
                with patch('qm2.app.show_logo') as mock_logo:
                    with patch('qm2.app.console.clear') as mock_clear:
                        # Select help option, then exit
                        mock_select.return_value.ask.side_effect = ["6.) 💞 Help", "7.) ⏻  Exit"]
                        
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function (it will exit after second selection)
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify help was shown
                            mock_help.assert_called_once()
                            # Verify exit was confirmed
                            mock_confirm.assert_called_once()
    
    def test_main_menu_exit_no_confirmation(self):
        """Test main menu exit without confirmation."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    # Select exit option twice: first no, then yes
                    mock_select.return_value.ask.side_effect = ["7.) ⏻  Exit", "7.) ⏻  Exit"]
                    
                    with patch('qm2.app.questionary.confirm') as mock_confirm:
                        # First confirm: no, second confirm: yes
                        mock_confirm.return_value.ask.side_effect = [False, True]
                        
                        # Run the main function
                        try:
                            main()
                        except SystemExit:
                            pass  # Expected when main() exits
                            
                        # Verify confirm was called twice
                        assert mock_confirm.call_count == 2
    
    def test_main_menu_exit_with_confirmation(self):
        """Test main menu exit with confirmation."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    with patch('qm2.app.console.print') as mock_print:
                        # Select exit option and confirm
                        mock_select.return_value.ask.side_effect = ["7.) ⏻  Exit"]
                        
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify exit message was printed
                            mock_print.assert_any_call("[bold green]👋 Exit. Good luck with your studies!")
    
    def test_main_menu_start_quiz_flow(self):
        """Test main menu start quiz flow."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    # Select quiz option, then exit
                    mock_select.return_value.ask.side_effect = ["1.) 🚀 Start Quiz", "7.) ⏻  Exit"]
                    
                    with patch('qm2.app._handle_quiz_choice') as mock_quiz:
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify quiz handler was called
                            mock_quiz.assert_called_once()
    
    def test_main_menu_flashcards_flow(self):
        """Test main menu flashcards flow."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    # Select flashcards option, then exit
                    mock_select.return_value.ask.side_effect = ["2.) 👾 Flashcards Learning", "7.) ⏻  Exit"]
                    
                    with patch('qm2.app._handle_flashcards_choice') as mock_flashcards:
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify flashcards handler was called
                            mock_flashcards.assert_called_once()
    
    def test_main_menu_questions_flow(self):
        """Test main menu questions flow."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    # Select questions option, then exit
                    mock_select.return_value.ask.side_effect = ["3.) 🗂️ Questions", "7.) ⏻  Exit"]
                    
                    with patch('qm2.app._handle_questions_menu') as mock_questions:
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify questions handler was called
                            mock_questions.assert_called_once()
    
    def test_main_menu_statistics_flow(self):
        """Test main menu statistics flow."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    # Select statistics option, then exit
                    mock_select.return_value.ask.side_effect = ["4.) 📈 Statistics", "7.) ⏻  Exit"]
                    
                    with patch('qm2.app._handle_stats_menu') as mock_stats:
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify stats handler was called
                            mock_stats.assert_called_once()
    
    def test_main_menu_tools_flow(self):
        """Test main menu tools flow."""
        with patch('qm2.app.questionary.select') as mock_select:
            with patch('qm2.app.show_logo') as mock_logo:
                with patch('qm2.app.console.clear') as mock_clear:
                    # Select tools option, then exit
                    mock_select.return_value.ask.side_effect = ["5.) 🧰 Tools", "7.) ⏻  Exit"]
                    
                    with patch('qm2.app._handle_tools_menu') as mock_tools:
                        with patch('qm2.app.questionary.confirm') as mock_confirm:
                            mock_confirm.return_value.ask.return_value = True
                            
                            # Run the main function
                            try:
                                main()
                            except SystemExit:
                                pass  # Expected when main() exits
                            
                            # Verify tools handler was called
                            mock_tools.assert_called_once()
    
    def test_diagnose_functionality(self):
        """Test diagnose.py functionality."""
        with patch('qm2.diagnose.ensure_dirs') as mock_ensure:
            with patch('qm2.diagnose.print') as mock_print:
                # Mock the paths to avoid dependency on actual file system
                with patch('qm2.diagnose.DATA_DIR', '/mock/data'):
                    with patch('qm2.diagnose.CATEGORIES_DIR', '/mock/categories'):
                        with patch('qm2.diagnose.CSV_DIR', '/mock/csv'):
                            with patch('qm2.diagnose.SCORES_FILE', '/mock/scores.json'):
                                diagnose_main()
                                
                                # Verify directories were ensured
                                mock_ensure.assert_called_once()
                                
                                # Verify output was printed
                                assert mock_print.call_count >= 6  # Header + 4 paths + success message
    
    def test_diagnose_main_function_structure(self):
        """Test diagnose main function structure and imports."""
        # Test that the function exists and is callable
        assert callable(diagnose_main)
        
        # Test the function has the expected signature
        import inspect
        sig = inspect.signature(diagnose_main)
        assert sig.parameters == {}  # No parameters expected
    
    def test_app_imports_and_structure(self):
        """Test app.py imports and main function structure."""
        # Test that main function exists and is callable
        assert callable(main)
        
        # Test the function has the expected signature
        import inspect
        sig = inspect.signature(main)
        assert sig.parameters == {}  # No parameters expected
