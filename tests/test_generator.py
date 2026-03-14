from unittest.mock import patch
from qm2.ai.generator import generate_quiz, _clean_ai_response, _get_system_prompt

def test_clean_ai_response_empty_and_malformed():
    assert _clean_ai_response("") == []
    assert _clean_ai_response("not json") == []

def test_get_system_prompt_contains_topic():
    topic, num = "Math", 5
    prompt = _get_system_prompt(topic, num)
    assert topic in prompt
    assert str(num) in prompt

@patch("qm2.ai.generator.os.getenv", return_value=None)
@patch("qm2.ai.generator.genai")
@patch("qm2.ai.generator.Console.print")
def test_generate_quiz_provider_not_gemini(mock_print, mock_genai, mock_env):
    # Provider other than Gemini
    result = generate_quiz("Math", 5, "OtherProvider")
    assert result == []

@patch("qm2.ai.generator.genai")
@patch("qm2.ai.generator.os.getenv", return_value="dummy")
def test_generate_quiz_no_client(monkeypatch, mock_genai):
    # Remove Client to simulate missing genai
    mock_genai.Client = None
    result = generate_quiz("Science", 3, "Gemini")
    assert result == []

@patch("qm2.ai.generator.genai")
@patch("qm2.ai.generator.os.getenv", return_value="dummy")
def test_generate_quiz_client_exception(mock_env, mock_genai):
    # Simulate exception in generate_content
    class DummyClient:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                raise ValueError("Boom")
    mock_genai.Client = DummyClient
    result = generate_quiz("Physics", 2, "Gemini")
    assert result == []

@patch("qm2.ai.generator.genai")
@patch("qm2.ai.generator.os.getenv", return_value="dummy")
def test_generate_quiz_success(mock_env, mock_genai):
    # Simulate valid response
    class DummyResp:
        text = '[{"type":"multiple","question":"Q","correct":"A","wrong_answers":["B","C"]}]'

    class DummyModels:
        @staticmethod
        def generate_content(model, contents):
            return DummyResp()

    class DummyClient:
        models = DummyModels()

    mock_genai.Client = lambda api_key=None: DummyClient()
    result = generate_quiz("History", 1, "Gemini")
    assert isinstance(result, list)
    assert result[0]["type"] == "multiple"