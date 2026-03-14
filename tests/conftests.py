import pytest
import sys
from unittest.mock import MagicMock

if "google.genai" not in sys.modules:
    mock_genai = MagicMock()
    sys.modules["google"] = MagicMock()
    sys.modules["google.genai"] = mock_genai

class FakeQuestionary:
    """Fake questionary helper to avoid interactive prompts in tests."""
    def __init__(self, return_value):
        self.return_value = return_value

    def select(self, *args, **kwargs):
        return self   # imitates chainable API

    def confirm(self, *args, **kwargs):
        return self   # so confirm.ask() also works

    def ask(self):
        return self.return_value


@pytest.fixture
def fake_questionary(monkeypatch):
    """
    Fixture that allows questionary to be "faked" to return
    a predefined value.
    """
    def _apply(value):
        monkeypatch.setattr("qm2.app.questionary", FakeQuestionary(value))
    return _apply
