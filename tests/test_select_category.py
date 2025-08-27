import qm2.core.categories as categories

class FakeQuestionary:
    def __init__(self, return_value):
        self.return_value = return_value

    def select(self, *args, **kwargs):
        return self

    def ask(self):
        return self.return_value


def test_select_category_allows_create(monkeypatch, tmp_path):
    monkeypatch.setattr(categories, "get_categories", lambda: ["math.json"])
    monkeypatch.setattr("qm2.core.categories.questionary", FakeQuestionary("➕ Create new"))
    monkeypatch.setattr(categories, "Prompt", type("P", (), {"ask": staticmethod(lambda _: "history")}))

    called = {}
    def fake_save_json(path, data):
        called["path"] = path
        called["data"] = data
        return True
    monkeypatch.setattr(categories, "save_json", fake_save_json)

    result = categories.select_category(allow_create=True)

    assert "history.json" in result
    assert called["data"] == []


def test_select_category_disallow_create(monkeypatch):
    monkeypatch.setattr(categories, "get_categories", lambda: ["science.json"])
    monkeypatch.setattr("qm2.core.categories.questionary", FakeQuestionary("science.json"))

    result = categories.select_category(allow_create=False)

    assert result.endswith("science.json")
