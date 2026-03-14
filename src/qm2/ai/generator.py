import os
import json
import re
from rich.console import Console

console = Console()

# Fallback if Google GenAI library is missing
try:
    from google import genai
except (ImportError, AttributeError):
    class DummyGenai:
        Client = None
    genai = DummyGenai()


def _get_system_prompt(topic: str, num: int) -> str:
    """Returns extremely strict instructions to ensure AI follows the exact JSON schema."""
    return (
        f"Create an educational quiz about '{topic}' with exactly {num} questions in English. "
        "Return ONLY a raw JSON array of objects. No markdown, no intro/outro text.\n\n"
        "STRICT SCHEMA RULES:\n"
        "1. MULTIPLE CHOICE: {\"type\": \"multiple\", \"question\": \"...\", \"correct\": \"...\", \"wrong_answers\": [\"...\", \"...\", \"...\"]}\n"
        "2. TRUE/FALSE: {\"type\": \"truefalse\", \"question\": \"...\", \"correct\": \"True\", \"wrong_answers\": [\"False\"]}\n"
        "3. FILL-IN: {\"type\": \"fillin\", \"question\": \"The ___ is...\", \"correct\": \"...\", \"wrong_answers\": []}\n"
        "4. MATCHING: {\"type\": \"match\", \"question\": \"...\", \"correct\": \"\", \"wrong_answers\": [], \"pairs\": {\"left\": [\"A\", \"B\"], \"right\": [\"1\", \"2\"], \"answers\": {\"a\": \"1\", \"b\": \"2\"}}}\n\n"
        "CRITICAL FOR MATCHING:\n"
        "- The 'answers' keys MUST be lowercase letters ('a', 'b', 'c'...). \n"
        "- The 'answers' values MUST be the VISIBLE NUMBER displayed in the 'right' list starting from \"1\".\n"
        "- Example: If 'right' is [\"Zeus\", \"Ares\"], then Zeus is \"1\" and Ares is \"2\".\n\n"
        "ALL 4 fields (type, question, correct, wrong_answers) MUST be present in EVERY object."
    )


def _clean_ai_response(text: str) -> list:
    """Extracts JSON array from AI response."""
    if not text:
        return []
    text = re.sub(r'```json\s*|```\s*', '', text).strip()
    try:
        start = text.find('[')
        end = text.rfind(']') + 1
        if start != -1 and end != 0:
            return json.loads(text[start:end])
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []


def generate_quiz(topic: str, num: int, provider: str, custom_model: str = None) -> list:
    """Generate a quiz using Google GenAI with model fallback and error handling."""
    if provider != "Gemini":
        return []

    prompt = _get_system_prompt(topic, num)
    is_testing = os.getenv("PYTEST_CURRENT_TEST") is not None

    if (genai is None or getattr(genai, "Client", None) is None) and not is_testing:
        console.print("[red]❌ Google GenAI library not found.[/]")
        return []

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key and not is_testing:
        console.print("[red]❌ No API Key found in environment.[/]")
        return []

    effective_api_key = api_key if api_key else "test_dummy_key"

    try:
        client = genai.Client(api_key=effective_api_key)

        # Priority list of models to try
        models_to_try = []
        if custom_model:
            model_map = {
                "gemini-flash-latest": "gemini-flash-latest",
                "gemini-2.5-flash-lite": "gemini-2.5-flash",
                "gemini-2.5-flash": "gemini-flash-latest",
                "gemini-2.0-flash-lite": "gemini-flash-latest",
                "gemini-2.5-pro": "gemini-1.5-pro",
            }
            models_to_try.append(model_map.get(custom_model, custom_model))

        models_to_try.extend(['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro'])
        models_to_try = list(dict.fromkeys(models_to_try))  # Deduplicate

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response and hasattr(response, 'text') and response.text:
                    result = _clean_ai_response(response.text)
                    if result:
                        return result
            except Exception as e:
                error_str = str(e).lower()
                if any(x in error_str for x in ["401", "403"]):
                    console.print("[red]❌ API Key Error.[/]")
                    return []
                console.print(f"[yellow]⚠️ Model '{model_name}' failed. Trying fallback...[/]")
                continue

        return []
    except Exception as e:
        console.print(f"[red]❌ Client error: {e}[/]")
        return []