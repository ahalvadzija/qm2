from qm2.utils.files import save_json
from unittest.mock import patch

def test_save_json_exception_path():
    """Covers lines 52-55 in utils/files.py."""
    # Permission denied' when open file
    with patch("builtins.open", side_effect=PermissionError("Fake Error")):
        with patch("qm2.utils.files.console.print") as mock_print:
            success = save_json("any.json", {"data": 1})
            assert success is False
            assert mock_print.called # Cover 54-55