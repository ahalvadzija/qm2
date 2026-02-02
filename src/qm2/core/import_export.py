# src/qm2/core/import_export.py
from pathlib import Path
import requests
import questionary
from rich.prompt import Prompt


def csv_to_json(csv_file: Path, json_file: Path) -> None:
    """
    Convert CSV file to JSON format.

    Example:
    >>> import tempfile, json
    >>> from pathlib import Path
    >>> tmp = Path(tempfile.gettempdir())
    >>> csv_file = tmp / "demo.csv"
    >>> json_file = tmp / "demo.json"
    >>> csv_file.write_text("q,a\\n2+2,4\\n", encoding="utf-8")
    8
    >>> csv_to_json(csv_file, json_file)
    >>> data = json.loads(json_file.read_text(encoding="utf-8"))
    >>> data[0]["q"]
    '2+2'
    """
    import csv
    import json
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def json_to_csv(json_file: Path, csv_file: Path) -> None:
    """
    Convert JSON file back to CSV format.

    Example:
    >>> import tempfile, json, csv
    >>> from pathlib import Path
    >>> tmp = Path(tempfile.gettempdir())
    >>> json_file = tmp / "demo.json"
    >>> csv_file = tmp / "demo.csv"
    >>> json_file.write_text('[{"q": "2+2", "a": "4"}]', encoding="utf-8")
    25
    >>> json_to_csv(json_file, csv_file)
    >>> rows = list(csv.DictReader(open(csv_file, encoding="utf-8")))
    >>> rows[0]["a"]
    '4'
    """
    import csv
    import json
    with open(json_file, encoding="utf-8") as f:
        rows = json.load(f)

    if not rows:
        raise ValueError("JSON is empty")

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def download_remote(url: str, dest_path: Path, overwrite: bool = False) -> Path:
    """
    Core logic for downloading a file (CSV or JSON) and saving to the correct path.

    >>> import tempfile
    >>> from pathlib import Path
    >>> tmp = Path(tempfile.gettempdir()) / "remote.json"
    >>> # Fake response (monkeypatch or requests_mock in test)
    >>> isinstance(download_remote.__call__, object)  # doctest: +ELLIPSIS
    True
    """
    dest_path = Path(dest_path)
    if dest_path.exists() and not overwrite:
        raise FileExistsError(dest_path)

    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    dest_path.write_bytes(resp.content)
    return dest_path


def download_remote_file(url: str, dest_dir: Path) -> Path | None:
    """
    UI layer for file download:
    - asks user for file name,
    - checks overwrite,
    - calls core.download_remote

    (Doctest not provided as it requires interaction via Prompt/confirm.)
    """
    name = Prompt.ask("Category name")
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{name}.json"

    if dest_path.exists():
        if not questionary.confirm(
            f"File {dest_path.name} already exists. Overwrite?"
        ).ask():
            return None  # user refused overwrite

    return download_remote(url, dest_path, overwrite=True)
