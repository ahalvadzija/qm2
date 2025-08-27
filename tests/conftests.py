import pytest

class FakeQuestionary:
    """Fake questionary helper da izbjegnemo interaktivni prompt u testovima."""
    def __init__(self, return_value):
        self.return_value = return_value

    def select(self, *args, **kwargs):
        return self   # imitira chainable API

    def confirm(self, *args, **kwargs):
        return self   # da radi i confirm.ask()

    def ask(self):
        return self.return_value


@pytest.fixture
def fake_questionary(monkeypatch):
    """
    Fixture koji omogućava da se questionary "prevari" tako da vraća
    unaprijed zadatu vrijednost.
    """
    def _apply(value):
        monkeypatch.setattr("qm2.app.questionary", FakeQuestionary(value))
    return _apply
