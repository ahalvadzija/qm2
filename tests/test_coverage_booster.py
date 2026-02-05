from unittest.mock import patch
import qm2.app as app


def test_handle_tools_menu_coverage():
    """Targeting app.py _handle_tools_menu using correct named imports."""
    # Patch questionary
    with patch('qm2.app.questionary.select') as mock_select, \
         patch('qm2.app.create_csv_template') as mock_csv_temp, \
         patch('qm2.app.create_json_template') as mock_json_temp, \
         patch('qm2.app.import_remote_file') as mock_remote, \
         patch('qm2.app.console.print'):
        
        # CSV -> JSON -> Remote -> Back
        mock_select.return_value.ask.side_effect = [
            "📄 Create CSV template",
            "📄 Create JSON template",
            "🌐 Import remote CSV/JSON",
            "↩ Back"
        ]
        
        app._handle_tools_menu()
        
        assert mock_csv_temp.called
        assert mock_json_temp.called
        assert mock_remote.called

def test_handle_stats_menu_coverage():
    """Targeting _handle_stats_menu using correct names."""
    with patch('qm2.app.questionary.select') as mock_select, \
         patch('qm2.app.view_scores') as mock_view, \
         patch('qm2.app.reset_scores') as mock_reset:
        
        # View -> Reset -> Back
        mock_select.return_value.ask.side_effect = [
            "📈 View results",
            "♻️ Reset results",
            "↩ Back"
        ]
        
        app._handle_stats_menu("dummy_scores.json")
        
        assert mock_view.called
        assert mock_reset.called

def test_full_tools_and_stats_flow():
    """Udaramo direktno na Tools i Stats menije u app.py."""
    with patch('qm2.app.questionary.select') as mock_select, \
         patch('qm2.app.view_scores') as mock_view, \
         patch('qm2.app.reset_scores'), \
         patch('qm2.app._handle_csv_to_json') as mock_csv_conv, \
         patch('qm2.app._handle_json_to_csv'):
        
        mock_select.return_value.ask.side_effect = [
            "📈 View results", "♻️ Reset results", "↩ Back"
        ]
        app._handle_stats_menu("dummy.json")
        
        mock_select.return_value.ask.side_effect = [
            "🧾 Convert CSV to JSON", "📤 Export JSON to CSV", "↩ Back"
        ]
        app._handle_tools_menu()
        
        assert mock_view.called
        assert mock_csv_conv.called