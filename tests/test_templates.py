import json
import csv
from qm2.core import templates


def test_create_csv_template(tmp_path, monkeypatch):
    # Patch CSV_DIR to point to temp folder
    monkeypatch.setattr(templates, "CSV_DIR", tmp_path)

    # Function call
    path = templates.create_csv_template()

    # Checks
    assert path.exists(), "CSV template not created"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "question" in headers
        rows = list(reader)
        assert any("Paris" in row for row in rows)


def test_create_json_template(tmp_path, monkeypatch):
    # Patch CATEGORIES_DIR to point to temp folder
    monkeypatch.setattr(templates, "CATEGORIES_DIR", tmp_path)

    # Function call
    path = templates.create_json_template()

    # Checks
    assert path.exists(), "JSON template not created"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert any(item.get("type") == "multiple" for item in data)
    assert any(item.get("correct") == "Paris" for item in data)
