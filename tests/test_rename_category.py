import qm2.core.categories as categories
from pathlib import Path

class FakeQuestionary:
    def __init__(self, return_value):
        self.return_value = return_value

    def select(self, *args, **kwargs):
        return self

    def ask(self):
        return self.return_value


def test_rename_category_normalizes_extension(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    old_file = categories_dir / "old.json"
    old_file.write_text("[]", encoding="utf-8")

    # fake get_categories
    monkeypatch.setattr(categories, "get_categories", lambda: ["old.json"])
    # patchamo baš modul gdje se koristi questionary
    monkeypatch.setattr("qm2.core.categories.questionary", FakeQuestionary("old.json"))
    # fake Prompt.ask -> korisnik unese "new.json"
    monkeypatch.setattr(categories, "Prompt", type("P", (), {"ask": staticmethod(lambda _: "new.json")}))
    # fake console
    monkeypatch.setattr(categories, "console", type("C", (), {"print": staticmethod(lambda *a, **k: None)}))

    categories.rename_category()

    assert (categories_dir / "new.json").exists()
    assert not (categories_dir / "old.json").exists()
