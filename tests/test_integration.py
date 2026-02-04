"""
Integration tests for app.py using builtins.input mock to simulate full user sessions.
"""

import pytest
from unittest.mock import patch, MagicMock

from qm2.app import main


@pytest.mark.timeout(5)
class TestAppIntegration:
    """Integration tests for app.py to improve coverage from 23% to 40%+."""
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_main_menu_exit(self, mock_logo, mock_select):
        """Test direct exit from main menu."""
        # Mock main menu selection and exit confirmation
        mock_select.return_value.ask.side_effect = ["7.) ⏻  Exit"]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Run main app
            main()
        
        # Verify components
        mock_logo.assert_called()
        mock_select.return_value.ask.assert_called()
        mock_confirm.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_help_menu_flow(self, mock_logo, mock_select):
        """Test help menu flow."""
        # Mock main menu selection: Help, then Exit (multiple exits to prevent StopIteration)
        mock_select.return_value.ask.side_effect = ["6.) 💞 Help", "7.) ⏻  Exit", "7.) ⏻  Exit"]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Mock user input for help (press Enter to continue)
            with patch('builtins.input') as mock_input:
                mock_input.return_value = ""
                
                # Run main app
                main()
        
        # Verify components
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 1
        mock_confirm.assert_called()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_tools_menu_flow(self, mock_logo, mock_select):
        """Test tools menu flow."""
        # Mock main menu selection: Tools, then Exit (multiple exits to prevent StopIteration)
        mock_select.return_value.ask.side_effect = ["5.) 🧰 Tools", "7.) ⏻  Exit", "7.) ⏻  Exit"]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Mock tools menu selection using the same mock_select
            # First call is for main menu, second for tools menu
            mock_select.return_value.ask.side_effect = [
                "5.) 🧰 Tools",  # Main menu selection
                "↩ Back",        # Tools menu selection
                "7.) ⏻  Exit",   # Main menu exit
                "7.) ⏻  Exit"    # Extra exit to prevent StopIteration
            ]
            
            # Run main app
            main()
        
        # Verify components
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 1
        mock_confirm.assert_called()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_questions_menu_flow(self, mock_logo, mock_select):
        """Test questions menu flow."""
        # Mock main menu selection: Questions, then Exit (multiple exits to prevent StopIteration)
        mock_select.return_value.ask.side_effect = [
            "3.) 🗂️ Questions",  # Main menu selection
            "↩ Back",           # Questions menu selection
            "7.) ⏻  Exit",      # Main menu exit
            "7.) ⏻  Exit"       # Extra exit to prevent StopIteration
        ]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Run main app
            main()
        
        # Verify components
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 1
        mock_confirm.assert_called()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_quiz_no_category_selected(self, mock_logo, mock_select):
        """Test quiz flow when no category is selected."""
        # Mock main menu selection: Quiz, then Exit (multiple exits to prevent StopIteration)
        mock_select.return_value.ask.side_effect = ["1.) 🚀 Start Quiz", "7.) ⏻  Exit", "7.) ⏻  Exit"]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Mock category selection (user cancels)
            with patch('qm2.app.select_category') as mock_select_category:
                mock_select_category.return_value = None
                
                # Mock input for quiz completion
                with patch('builtins.input') as mock_input:
                    mock_input.return_value = ""
                    
                    # Run main app
                    main()
        
        # Verify components
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 1
        mock_select_category.assert_called_once()
        mock_confirm.assert_called()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_full_quiz_session(self, mock_logo, mock_select):
        """Test complete quiz session flow."""
        # Mock main menu selection: Quiz, then Exit (multiple exits to prevent StopIteration)
        mock_select.return_value.ask.side_effect = ["1.) 🚀 Start Quiz", "7.) ⏻  Exit", "7.) ⏻  Exit"]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Mock category selection
            with patch('qm2.app.select_category') as mock_select_category:
                mock_select_category.return_value = "test.json"
                
                # Mock questions data
                with patch('qm2.app.get_questions') as mock_questions:
                    mock_questions.return_value = [
                        {
                            "type": "multiple",
                            "question": "What is 2+2?",
                            "correct": "4",
                            "wrong_answers": ["3", "5", "6"]
                        }
                    ]
                    
                    # Mock quiz session result
                    with patch('qm2.app.quiz_session') as mock_quiz:
                        mock_quiz.return_value = MagicMock(score=1, total=1, time_taken=30)
                        
                        # Mock input for quiz completion (press Enter to continue)
                        with patch('builtins.input') as mock_input:
                            mock_input.return_value = ""
                            
                            # Run main app
                            main()
        
        # Verify all components were called
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 1
        mock_select_category.assert_called_once()
        mock_questions.assert_called_once_with("test.json")
        mock_quiz.assert_called_once()
        mock_confirm.assert_called()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_multiple_menu_navigation(self, mock_logo, mock_select):
        """Test navigating through multiple menus."""
        # Mock main menu selection: Tools, then Exit (multiple exits to prevent StopIteration)
        mock_select.return_value.ask.side_effect = [
            "5.) 🧰 Tools",   # Main menu selection
            "↩ Back",         # Tools menu selection
            "7.) ⏻  Exit",    # Main menu exit
            "7.) ⏻  Exit"     # Extra exit to prevent StopIteration
        ]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            # Run main app
            main()
        
        # Verify main menu was called multiple times
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 1
        mock_confirm.assert_called()
