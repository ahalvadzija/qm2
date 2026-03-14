# tests/test_ai.py
import json
from unittest.mock import MagicMock, patch
from qm2.ai.generator import _clean_ai_response, generate_quiz

def test_clean_ai_response_valid_json():
    raw_input = '[{"question": "Test?", "type": "truefalse"}]'
    cleaned = _clean_ai_response(raw_input)
    assert isinstance(cleaned, list)
    assert cleaned[0]["question"] == "Test?"

@patch("qm2.ai.generator.genai.Client")
def test_generate_quiz_gemini_success(mock_client_class):
    mock_response = MagicMock()
    mock_response.text = json.dumps([
        {"type": "multiple", "question": "Python?", "correct": "Yes", "wrong_answers": ["No"]}
    ])
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.models.generate_content.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        result = generate_quiz("Python", 1, "Gemini")
    
    assert result[0]["question"] == "Python?"