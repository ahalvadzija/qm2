import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import qm2.app as app

def test_import_remote_file_logic_fixed():
    """
    Covers app.py lines 77-85 (remote import detection).
    """
    with patch('requests.head') as mock_head, \
         patch('qm2.app.Prompt.ask') as mock_prompt, \
         patch('qm2.app.is_file_valid', return_value=True), \
         patch('qm2.app.core_download_remote', return_value=Path("dummy.json")), \
         patch('qm2.app.categories_add'), \
         patch('qm2.app.refresh_categories_cache'):
        
        # 1. URL, 2. Filename
        mock_prompt.side_effect = ["https://example.com/test", "my_remote_file"]
        
        # Mock HEAD response for JSON
        mock_res = MagicMock()
        mock_res.headers = {'content-type': 'application/json'}
        mock_head.return_value = mock_res
        
        app.import_remote_file()
        
        # Now it should call requests.head to detect type
        assert mock_head.called