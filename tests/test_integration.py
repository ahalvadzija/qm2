import pytest
from unittest.mock import patch
from qm2.app import main

@pytest.mark.timeout(5)
class TestAppIntegration:
    """
    Integration tests for app.py.
    These tests simulate user interaction with the main menu and submenus
    to ensure the application flow is correct.
    """
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_main_menu_exit(self, mock_logo, mock_select):
        """Test direct exit from main menu with confirmation."""
        # Use the exact string from app.py: "8.) ⏻  Exit"
        mock_select.return_value.ask.side_effect = ["8.) ⏻  Exit"]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            # Confirm the exit dialog
            mock_confirm.return_value.ask.return_value = True
            
            main()
        
        mock_logo.assert_called()
        mock_confirm.assert_called_once()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_help_menu_flow(self, mock_logo, mock_select):
        """Test navigating to help and back, then exiting."""
        # Strings must match exactly with those in app.py
        mock_select.return_value.ask.side_effect = [
            "7.) 💞 Help",      # Selection 1: Open Help
            "8.) ⏻  Exit"       # Selection 2: Exit
        ]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            with patch('qm2.app.show_help') as mock_show_help:
                main()
        
        mock_show_help.assert_called_once()
        assert mock_select.return_value.ask.call_count == 2

    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_tools_menu_flow(self, mock_logo, mock_select):
        """Test tools menu navigation."""
        mock_select.return_value.ask.side_effect = [
            "5.) 🧰 Tools",    # Main Menu
            "↩ Back",          # Tools Submenu
            "8.) ⏻  Exit"      # Main Menu again
        ]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            main()
        
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count == 3
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_questions_menu_flow(self, mock_logo, mock_select):
        """Test questions menu flow including the 'manage' option."""
        mock_select.return_value.ask.side_effect = [
            "3.) 🗂️ Questions",   # Main Menu
            "↩ Back",              # Questions Submenu
            "8.) ⏻  Exit"          # Main Menu exit
        ]
        
        # Patch the internal pagination select used for category choosing
        with patch('qm2.app.select_with_pagination') as mock_pag:
            mock_pag.return_value = "↩ Back"
            with patch('qm2.app.questionary.confirm') as mock_confirm:
                mock_confirm.return_value.ask.return_value = True
                main()
        
        mock_logo.assert_called()
        assert mock_select.return_value.ask.call_count >= 2
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_quiz_no_category_selected(self, mock_logo, mock_select):
        """Test quiz flow when user chooses back in category selection."""
        mock_select.return_value.ask.side_effect = [
            "1.) 🚀 Start Quiz", 
            "8.) ⏻  Exit"
        ]
        
        with patch('qm2.app.select_with_pagination') as mock_select_paginated:
            mock_select_paginated.return_value = "↩ Back"
            
            with patch('qm2.app.questionary.confirm') as mock_confirm:
                mock_confirm.return_value.ask.return_value = True
                main()
        
        mock_select_paginated.assert_called_once()
        mock_confirm.assert_called()
    
    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_full_quiz_session(self, mock_logo, mock_select):
        """Test a complete quiz session including the 'Press Enter' at the end."""
        mock_select.return_value.ask.side_effect = [
            "1.) 🚀 Start Quiz", 
            "8.) ⏻  Exit"
        ]
        
        with patch('qm2.app.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            with patch('qm2.app.select_with_pagination') as mock_select_paginated:
                mock_select_paginated.return_value = "test_quiz" # Just a string value
                
                with patch('qm2.app.get_questions') as mock_questions:
                    mock_questions.return_value = [{"type": "multiple", "question": "Q", "correct": "A", "wrong_answers": ["B"]}]
                    
                    with patch('qm2.app.quiz_session') as mock_quiz:
                        # Crucial: Mock builtins.input for the "Press Enter to return" part
                        with patch('builtins.input', return_value="") as mock_input:
                            main()
                            
        mock_quiz.assert_called_once()
        # Verify that input was called once at the end of the quiz session
        mock_input.assert_called()

    @patch('qm2.app.questionary.select')
    @patch('qm2.app.show_logo')
    def test_ai_generator_setup_flow(self, mock_logo, mock_select):
        """Test entering AI Generator menu and backing out."""
        mock_select.return_value.ask.side_effect = [
            "6.) 🤖 AI Generator",
            "8.) ⏻  Exit"
        ]
        
        # Mock API key retrieval to prevent key setup prompt
        with patch('qm2.app.get_api_key', return_value="fake_key"):
            # Mock the internal handle function so we don't need to mock all Prompt.ask calls
            with patch('qm2.app._handle_ai_menu') as mock_ai:
                with patch('qm2.app.questionary.confirm') as mock_confirm:
                    mock_confirm.return_value.ask.return_value = True
                    main()
        
        mock_ai.assert_called_once()
        mock_confirm.assert_called()