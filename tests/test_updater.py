from unittest.mock import patch, MagicMock
from qm2.utils.updater import check_for_updates

@patch('qm2.utils.updater.requests.get')
def test_check_for_updates_success(mock_get):
    """Test successful update check when a new version is available."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tag_name": "v9.9.9"}
    mock_get.return_value = mock_response

    # Mock version to something low so 9.9.9 is always an update
    with patch('qm2.utils.updater.__version__', "0.1.0", create=True):
        update_available, latest_v = check_for_updates()
    
    assert update_available is True
    assert latest_v == "9.9.9"

@patch('qm2.utils.updater.requests.get')
def test_check_for_updates_no_update(mock_get):
    """Test when the current version is already up to date."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tag_name": "v1.0.0"}
    mock_get.return_value = mock_response

    # Mock version to match the tag_name
    with patch('qm2.utils.updater.__version__', "1.0.0", create=True):
        update_available, latest_v = check_for_updates()
    
    assert update_available is False

@patch('qm2.utils.updater.requests.get')
def test_check_for_updates_error(mock_get):
    """Test update check when there is a network error."""
    mock_get.side_effect = Exception("Connection timeout")

    update_available, latest_v = check_for_updates()
    
    assert update_available is None
    assert latest_v is None