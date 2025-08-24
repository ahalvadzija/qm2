import builtins
import pytest

import qm2.app as app


class FakeQuestionary:
    """Simulira questionary.select().ask() poziv."""
    def __init__(self, to_return):
        self.to_return = to_return

    def select(self, message, choices):
        class Q:
            def __init__(self, result):
                self.result = result
            def ask(self):
                return self.result
        return Q(self.to_return)


def test_select_category_allows_create(monkeypatch, tmp_path):
    # simulate that get_categories vrati listu kategorija
    monkeypatch.setattr(app, "get_categories", lambda: ["math.json"])
    # simulate questionary.select() -> vrati "➕ Create new"
    monkeypatch.setattr(app, "questionary", FakeQuestionary("➕ Create new"))
    # simulate Prompt.ask() -> vrati "history"
    monkeypatch.setattr(app, "Prompt", type("P", (), {"ask": staticmethod(lambda _: "history")}))

    # override save_json da provjerimo da se poziva
    called = {}
    def fake_save_json(path, data):
        called["path"] = path
        called["data"] = data
        return True
    monkeypatch.setattr(app, "save_json", fake_save_json)

    result = app.select_category(allow_create=True)
    assert result.endswith("history.json")
    assert called["path"].endswith("history.json")
    assert called["data"] == []


def test_select_category_disallow_create(monkeypatch):
    monkeypatch.setattr(app, "get_categories", lambda: ["science.json"])
    # simulate da korisnik izabere postojecu kategoriju
    monkeypatch.setattr(app, "questionary", FakeQuestionary("science.json"))

    result = app.select_category(allow_create=False)
    assert result.endswith("science.json")
