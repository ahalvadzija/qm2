"""
Error handling tests for import_export.py to improve coverage for download and file operations.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

from qm2.core.import_export import download_remote, download_remote_file


class TestImportExportErrors:
    """Test error handling in import_export.py functions."""
    
    def test_download_remote_404_not_found(self):
        """Test download_remote with 404 Not Found response."""
        url = "https://example.com/nonexistent.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "test.json"
            
            # Mock requests.get to return 404
            with patch('qm2.core.import_export.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
                mock_get.return_value = mock_response
                
                # Should raise HTTPError
                with pytest.raises(requests.exceptions.HTTPError, match="404 Not Found"):
                    download_remote(url, dest_path)
                
                # Verify the request was made
                mock_get.assert_called_once_with(url, timeout=20)
    
    def test_download_remote_connection_timeout(self):
        """Test download_remote with connection timeout."""
        url = "https://example.com/slow.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "test.json"
            
            # Mock requests.get to raise timeout
            with patch('qm2.core.import_export.requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
                
                # Should raise Timeout
                with pytest.raises(requests.exceptions.Timeout, match="Connection timeout"):
                    download_remote(url, dest_path)
                
                # Verify the request was made
                mock_get.assert_called_once_with(url, timeout=20)
    
    def test_download_remote_connection_error(self):
        """Test download_remote with general connection error."""
        url = "https://example.com/unreachable.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "test.json"
            
            # Mock requests.get to raise connection error
            with patch('qm2.core.import_export.requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
                
                # Should raise ConnectionError
                with pytest.raises(requests.exceptions.ConnectionError, match="Connection failed"):
                    download_remote(url, dest_path)
                
                # Verify the request was made
                mock_get.assert_called_once_with(url, timeout=20)
    
    def test_download_remote_request_exception(self):
        """Test download_remote with generic RequestException."""
        url = "https://example.com/error.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "test.json"
            
            # Mock requests.get to raise generic RequestException
            with patch('qm2.core.import_export.requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.RequestException("Generic request error")
                
                # Should raise RequestException
                with pytest.raises(requests.exceptions.RequestException, match="Generic request error"):
                    download_remote(url, dest_path)
                
                # Verify the request was made
                mock_get.assert_called_once_with(url, timeout=20)
    
    def test_download_remote_permission_error_on_write(self):
        """Test download_remote when file cannot be written due to permissions."""
        url = "https://example.com/test.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "test.json"
            
            # Mock requests.get to return successful response
            with patch('qm2.core.import_export.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None
                mock_response.content = b'{"test": "data"}'
                mock_get.return_value = mock_response
                
                # Mock Path.write_bytes to raise PermissionError
                with patch.object(Path, 'write_bytes') as mock_write:
                    mock_write.side_effect = PermissionError("Permission denied")
                    
                    # Should raise PermissionError
                    with pytest.raises(PermissionError, match="Permission denied"):
                        download_remote(url, dest_path)
                    
                    # Verify write was attempted
                    mock_write.assert_called_once_with(b'{"test": "data"}')
    
    def test_download_remote_file_exists_no_overwrite(self):
        """Test download_remote when file exists and overwrite is False."""
        url = "https://example.com/existing.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "existing.json"
            
            # Create the file first
            dest_path.write_text('{"existing": "data"}')
            
            # Should raise FileExistsError
            with pytest.raises(FileExistsError):
                download_remote(url, dest_path, overwrite=False)
    
    @patch('qm2.core.import_export.Prompt.ask')
    @patch('qm2.core.import_export.questionary.confirm')
    def test_download_remote_file_404_ui_layer(self, mock_confirm, mock_prompt):
        """Test download_remote_file UI layer with 404 error."""
        url = "https://example.com/nonexistent.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_dir = Path(tmp_dir)
            
            # Mock user inputs
            mock_prompt.return_value = "test_category"
            mock_confirm.return_value.ask.return_value = True
            
            # Create existing file to trigger overwrite confirmation
            existing_file = dest_dir / "test_category.json"
            existing_file.parent.mkdir(parents=True, exist_ok=True)
            existing_file.write_text('{"existing": "data"}')
            
            # Mock download_remote to raise HTTPError
            with patch('qm2.core.import_export.download_remote') as mock_download:
                mock_download.side_effect = requests.exceptions.HTTPError("404 Not Found")
                
                # Should propagate the HTTPError
                with pytest.raises(requests.exceptions.HTTPError, match="404 Not Found"):
                    download_remote_file(url, dest_dir)
                
                # Verify user was asked for category name
                mock_prompt.assert_called_once_with("Category name")
                # Verify overwrite confirmation was asked (since file exists)
                mock_confirm.assert_called_once()
                # Verify download was attempted
                mock_download.assert_called_once()
    
    @patch('qm2.core.import_export.Prompt.ask')
    @patch('qm2.core.import_export.questionary.confirm')
    def test_download_remote_file_timeout_ui_layer(self, mock_confirm, mock_prompt):
        """Test download_remote_file UI layer with timeout error."""
        url = "https://example.com/slow.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_dir = Path(tmp_dir)
            
            # Mock user inputs
            mock_prompt.return_value = "test_category"
            mock_confirm.return_value.ask.return_value = True
            
            # Create existing file to trigger overwrite confirmation
            existing_file = dest_dir / "test_category.json"
            existing_file.parent.mkdir(parents=True, exist_ok=True)
            existing_file.write_text('{"existing": "data"}')
            
            # Mock download_remote to raise Timeout
            with patch('qm2.core.import_export.download_remote') as mock_download:
                mock_download.side_effect = requests.exceptions.Timeout("Connection timeout")
                
                # Should propagate the Timeout
                with pytest.raises(requests.exceptions.Timeout, match="Connection timeout"):
                    download_remote_file(url, dest_dir)
                
                # Verify user was asked for category name
                mock_prompt.assert_called_once_with("Category name")
                # Verify overwrite confirmation was asked (since file exists)
                mock_confirm.assert_called_once()
                # Verify download was attempted
                mock_download.assert_called_once()
    
    @patch('qm2.core.import_export.Prompt.ask')
    @patch('qm2.core.import_export.questionary.confirm')
    def test_download_remote_file_permission_error_ui_layer(self, mock_confirm, mock_prompt):
        """Test download_remote_file UI layer with permission error."""
        url = "https://example.com/test.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_dir = Path(tmp_dir)
            
            # Mock user inputs
            mock_prompt.return_value = "test_category"
            mock_confirm.return_value.ask.return_value = True
            
            # Create existing file to trigger overwrite confirmation
            existing_file = dest_dir / "test_category.json"
            existing_file.parent.mkdir(parents=True, exist_ok=True)
            existing_file.write_text('{"existing": "data"}')
            
            # Mock download_remote to raise PermissionError
            with patch('qm2.core.import_export.download_remote') as mock_download:
                mock_download.side_effect = PermissionError("Permission denied")
                
                # Should propagate the PermissionError
                with pytest.raises(PermissionError, match="Permission denied"):
                    download_remote_file(url, dest_dir)
                
                # Verify user was asked for category name
                mock_prompt.assert_called_once_with("Category name")
                # Verify overwrite confirmation was asked (since file exists)
                mock_confirm.assert_called_once()
                # Verify download was attempted
                mock_download.assert_called_once()
    
    @patch('qm2.core.import_export.Prompt.ask')
    @patch('qm2.core.import_export.questionary.confirm')
    def test_download_remote_file_user_refuses_overwrite(self, mock_confirm, mock_prompt):
        """Test download_remote_file when user refuses overwrite."""
        url = "https://example.com/existing.json"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_dir = Path(tmp_dir)
            
            # Mock user inputs
            mock_prompt.return_value = "test_category"
            mock_confirm.return_value.ask.return_value = False  # User refuses
            
            # Create existing file
            existing_file = dest_dir / "test_category.json"
            existing_file.parent.mkdir(parents=True, exist_ok=True)
            existing_file.write_text('{"existing": "data"}')
            
            # Should return None when user refuses overwrite
            result = download_remote_file(url, dest_dir)
            
            assert result is None
            
            # Verify user was asked for category name
            mock_prompt.assert_called_once_with("Category name")
            # Verify overwrite confirmation was asked
            mock_confirm.assert_called_once()
    
    @patch('qm2.core.import_export.Prompt.ask')
    def test_download_remote_file_mkdir_permission_error(self, mock_prompt):
        """Test download_remote_file when directory creation fails due to permissions."""
        url = "https://example.com/test.json"
        
        # Use a directory that likely doesn't exist and can't be created
        restricted_dir = Path("/root/restricted_qm2_test")
        
        # Mock user input
        mock_prompt.return_value = "test_category"
        
        # Mock Path.mkdir to raise PermissionError
        with patch.object(Path, 'mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            # Should raise PermissionError
            with pytest.raises(PermissionError, match="Permission denied"):
                download_remote_file(url, restricted_dir)
            
            # Verify user was asked for category name
            mock_prompt.assert_called_once_with("Category name")
            # Verify mkdir was attempted
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
