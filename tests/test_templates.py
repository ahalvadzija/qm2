import json
import csv
from qm2.core import templates


def test_create_csv_template(tmp_path, monkeypatch):
    # Patch CSV_DIR da pokazuje na privremeni folder
    monkeypatch.setattr(templates, "CSV_DIR", tmp_path)

    # Poziv funkcije
    path = templates.create_csv_template()

    # Provjere
    assert path.exists(), "CSV template nije kreiran"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "question" in headers
        rows = list(reader)
        assert any("Paris" in row for row in rows)


def test_create_json_template(tmp_path, monkeypatch):
    # Patch CATEGORIES_DIR da pokazuje na privremeni folder
    monkeypatch.setattr(templates, "CATEGORIES_DIR", tmp_path)

    # Poziv funkcije
    path = templates.create_json_template()

    # Provjere
    assert path.exists(), "JSON template nije kreiran"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert any(item.get("type") == "multiple" for item in data)
    assert any(item.get("correct") == "Paris" for item in data)
