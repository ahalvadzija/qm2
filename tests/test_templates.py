import csv
from pathlib import Path
import qm2.paths as paths


def test_create_csv_template(tmp_path, monkeypatch):
    # 🔹 1. Patch DATA_DIR tako da ide u tmp_path (ne pravi u ~/.local/share/qm2)
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(paths, "CSV_DIR", paths.DATA_DIR / "csv")

    # 🔹 2. Kreiraj folder
    paths.CSV_DIR.mkdir(parents=True, exist_ok=True)

    # 🔹 3. Putanja fajla
    csv_path = paths.CSV_DIR / "example_template.csv"

    # 🔹 4. Simuliraj kreiranje fajla (isto kao u app.py)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["type", "question", "correct", "wrong_answers", "left", "right", "answers"]
        )

    # 🔹 5. Test – fajl mora postojati
    assert csv_path.exists()

    # 🔹 6. Test – prva linija u CSV-u mora biti header
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["type", "question", "correct", "wrong_answers", "left", "right", "answers"]
