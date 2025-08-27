import json
from pathlib import Path
import qm2.core.import_export as import_export


def test_csv_to_json_and_back(tmp_path):
    # 🔹 1. Kreiraj fake CSV fajl
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "type,question,correct,wrong_answers\n"
        "multiple,What is 2+2?,4,3|5|6\n",
        encoding="utf-8",
    )

    # 🔹 2. Konverzija u JSON
    json_file = tmp_path / "sample.json"
    import_export.csv_to_json(csv_file, json_file)
    assert json_file.exists()
    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data[0]["question"] == "What is 2+2?"

    # 🔹 3. Konverzija nazad u CSV
    roundtrip_csv = tmp_path / "roundtrip.csv"
    import_export.json_to_csv(json_file, roundtrip_csv)
    assert roundtrip_csv.exists()
    assert "What is 2+2?" in roundtrip_csv.read_text(encoding="utf-8")


def test_download_remote(monkeypatch, tmp_path):
    # 🔹 Fake response
    class FakeResponse:
        def __init__(self, content): self.content = content
        def raise_for_status(self): pass

    # Patch requests.get direktno na import_export
    monkeypatch.setattr(
        import_export.requests, "get",
        lambda url, timeout=20: FakeResponse(b'[{"q":"2+2","a":"4"}]')
    )

    # Patch prompt → vrati ime fajla
    monkeypatch.setattr(import_export, "Prompt", type("P", (), {
        "ask": staticmethod(lambda _: "math")
    }))

    # Patch confirm → uvijek overwrite
    monkeypatch.setattr(import_export, "questionary", type("Q", (), {
        "confirm": staticmethod(lambda msg=None: type("C", (), {
            "ask": staticmethod(lambda : True)
        })())
    }))

    # Izvrši download
    dest = tmp_path / "categories"
    dest.mkdir()
    out = import_export.download_remote_file(
        "http://fake/file.json", dest
    )

    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))[0]["a"] == "4"


def test_download_remote_refuses_overwrite(monkeypatch, tmp_path):
    # 🔹 Fake response
    class FakeResponse:
        def __init__(self, content): self.content = content
        def raise_for_status(self): pass

    monkeypatch.setattr(
        import_export.requests, "get",
        lambda url, timeout=20: FakeResponse(b'[{"q":"1+1","a":"2"}]')
    )

    # Prompt → ime fajla
    monkeypatch.setattr(import_export, "Prompt", type("P", (), {
        "ask": staticmethod(lambda _: "duplicate")
    }))

    # Confirm → kaže NO (ne overwrite)
    monkeypatch.setattr(import_export, "questionary", type("Q", (), {
        "confirm": staticmethod(lambda msg=None: type("C", (), {
            "ask": staticmethod(lambda : False)
        })())
    }))

    # Napravi već postojeći fajl
    dest = tmp_path / "categories"
    dest.mkdir()
    existing = dest / "duplicate.json"
    existing.write_text("[]", encoding="utf-8")

    # Poziv
    out = import_export.download_remote_file(
        "http://fake/file.json", dest
    )

    # Pošto je korisnik odbio overwrite, rezultat je None
    assert out is None
    assert existing.read_text(encoding="utf-8") == "[]"