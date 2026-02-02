import qm2.app as app
import qm2.core.categories as categories
import qm2.core.import_export as import_export


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content      # 🔹 Dodali smo .content jer ga kod koristi
        self.status_code = 200

    def raise_for_status(self):
        return True

    def iter_content(self, chunk_size=8192):
        yield self.content          # 🔹 usklađeno sa .content


def test_import_remote_file_json_safe(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(categories, "CATEGORIES_DIR", categories_dir)

    # fake requests.get -> vrati JSON
    data = b'[{"q": "2+2", "a": "4"}]'
    monkeypatch.setattr(import_export, "requests", type("R", (), {"get": lambda *a, **k: FakeResponse(data)})())

    # Prompt.ask se zove 2x: prvo za URL, pa za ime fajla
    answers = iter(["http://fake/file.json", "math"])
    monkeypatch.setattr(app, "Prompt", type("P", (), {
        "ask": staticmethod(lambda _: next(answers))
    }))

    # fake questionary.confirm -> uvijek overwrite
    monkeypatch.setattr(app, "questionary", type("Q", (), {
        "confirm": staticmethod(lambda msg=None: type("C", (), {
            "ask": staticmethod(lambda : True)
        })())
    }))

    # patch categories_add
    called = {}
    monkeypatch.setattr(app, "categories_add", lambda path: called.setdefault("added", path))

    # poziv
    app.import_remote_file()

    # očekujemo math.json u categories/
    file_path = categories_dir / "math.json"
    assert file_path.exists()
    assert b"2+2" in file_path.read_bytes()
    assert called["added"].endswith("math.json")


def test_import_remote_file_rejects_bad_name(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(categories, "CATEGORIES_DIR", categories_dir)

    # fake requests.get -> vrati JSON
    data = b'[{"q": "bad test"}]'
    monkeypatch.setattr(import_export, "requests", type("R", (), {"get": lambda *a, **k: FakeResponse(data)})())

    # Prompt.ask: prvo za URL vrati ispravan, a poslije uvijek "../bad"
    def fake_prompt_ask(msg):
        if "URL" in msg:
            return "http://fake/file.json"
        return "../bad"

    monkeypatch.setattr(app, "Prompt", type("P", (), {
        "ask": staticmethod(fake_prompt_ask)
    }))

    # fake questionary.confirm
    monkeypatch.setattr(app, "questionary", type("Q", (), {
        "confirm": staticmethod(lambda msg=None: type("C", (), {
            "ask": staticmethod(lambda : True)
        })())
    }))

    called = {}
    monkeypatch.setattr(app, "categories_add", lambda path: called.setdefault("added", path))

    # poziv funkcije
    app.import_remote_file()

    # nema fajla
    for p in categories_dir.glob("*.json"):
        raise AssertionError(f"Unexpected file created: {p}")

    # categories_add se nije smio pozvati
    assert "added" not in called
