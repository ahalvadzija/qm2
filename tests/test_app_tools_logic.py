from unittest.mock import patch
from qm2.app import _handle_csv_to_json

def test_handle_csv_to_json_no_files():
    """Tests the tools logic when no CSV files are present."""
    
    # We patch os.listdir to return an empty list to trigger the "No CSV files found" block
    # We also patch console.print to verify the warning message
    with patch('os.listdir', return_value=[]), \
         patch('rich.console.Console.print') as mock_print:
        
        # Call the internal function directly
        _handle_csv_to_json()
        
        # Verify it printed the warning
        mock_print.assert_any_call("[red]⚠️ No CSV files found.")

def test_handle_csv_to_json_back_option():
    """Tests choosing the 'Back' option in CSV conversion."""
    
    # Simulate one CSV file exists, but user selects 'Back'
    with patch('os.listdir', return_value=["test.csv"]), \
         patch('questionary.select') as mock_select:
        
        # Mocking the choice to be 'Back'
        mock_select.return_value.ask.return_value = "↩ Back"
        
        _handle_csv_to_json()
        
        # Verify the selection was shown
        assert mock_select.called