import os
import qm2.app as app


class FakeQuestionary:
    def __init__(self, to_return):
        self.to_return = to_return

    def select(self, message, choices):
        class Q:
            def __init__(self, result):
                self.result = result
            def ask(self):
                return self.result
        return Q(self.to_return)


def test_rename_category_normalizes_extension(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    old_file = categories_dir / "old.json"
    old_file.write_text("[]", encoding="utf-8")

    # fake get_categories
    monkeypatch.setattr(app, "get_categories", lambda: ["old.json"])
    # fake questionary.select -> vraća "old.json"
    monkeypatch.setattr(app, "questionary", FakeQuestionary("old.json"))
    # fake Prompt.ask -> korisnik unese "new.json"
    monkeypatch.setattr(app, "Prompt", type("P", (), {"ask": staticmethod(lambda _: "new.json")}))
    # fake console
    monkeypatch.setattr(app, "console", type("C", (), {"print": staticmethod(lambda *a, **k: None)}))

    # poziv BEZ argumenata
    app.rename_category()

    # sad očekujemo da postoji fajl new.json
    new_file = categories_dir / "new.json"
    assert new_file.exists()

