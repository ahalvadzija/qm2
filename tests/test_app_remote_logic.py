from unittest.mock import patch
from qm2.app import import_remote_file
import requests

def test_import_remote_file_unsupported_type():
    """Tests when the file extension is unknown and user selects manual type."""
    
    # 1. Mocking Prompt.ask to provide a URL without extension and a valid filename
    # 2. Mocking questionary.select to simulate user choosing 'CSV' when detection fails
    with patch('rich.prompt.Prompt.ask', side_effect=["http://non-existent-site.com/file", "my_file"]), \
         patch('questionary.select') as mock_select, \
         patch('requests.head') as mock_head, \
         patch('rich.console.Console.print'):
        
        # Simulate a network failure (DNS or Timeout) for requests.head
        mock_head.side_effect = requests.exceptions.ConnectionError()
        
        # Simulate user selecting "CSV" in the fallback menu
        mock_select.return_value.ask.return_value = "CSV"
        
        # Invoke the target function
        import_remote_file()
        
        # Verify that the manual type selection was triggered
        mock_select.assert_called()