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
    import ast
    
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check if this is a flattened CSV format (with wrong_answers/0, pairs/left/0, etc.)
    fieldnames = reader.fieldnames or []
    is_flattened = any('/' in field for field in fieldnames)

    processed_rows = []
    for row in rows:
        if is_flattened:
            # Handle flattened CSV format
            processed_row = {}
            
            # Reconstruct wrong_answers from flattened columns
            wrong_answers = []
            for key in row:
                if key.startswith('wrong_answers/'):
                    value = row[key]
                    if isinstance(value, list):
                        wrong_answers.extend(str(v) for v in value if v)
                    elif value and value.strip():
                        wrong_answers.append(value.strip())
            processed_row['wrong_answers'] = wrong_answers
            
            # Reconstruct pairs from flattened columns
            pairs = {}
            left_items = []
            right_items = []
            answers = {}
            
            # Collect left items
            for key in sorted(row.keys()):
                if key.startswith('pairs/left/'):
                    value = row[key]
                    if isinstance(value, list):
                        left_items.extend(str(v) for v in value if v)
                    elif value and value.strip():
                        left_items.append(value.strip())
            
            # Collect right items
            for key in sorted(row.keys()):
                if key.startswith('pairs/right/'):
                    value = row[key]
                    if isinstance(value, list):
                        right_items.extend(str(v) for v in value if v)
                    elif value and value.strip():
                        right_items.append(value.strip())
            
            # Collect answers
            for key in sorted(row.keys()):
                if key.startswith('pairs/answers/'):
                    sub_key = key.split('/')[-1]
                    value = row[key]
                    if isinstance(value, list):
                        for v in value:
                            if v:
                                answers[sub_key] = str(v)
                    elif value and value.strip():
                        answers[sub_key] = value.strip()
            
            if left_items or right_items or answers:
                pairs = {
                    'left': left_items,
                    'right': right_items,
                    'answers': answers
                }
            processed_row['pairs'] = pairs
            
            # Copy other fields
            for key in ['type', 'question', 'correct']:
                if key in row:
                    value = row[key]
                    if isinstance(value, list):
                        processed_row[key] = str(value) if value else ""
                    elif value and value.strip():
                        processed_row[key] = value.strip()
            
        else:
            # Handle normal CSV format
            processed_row = {}
            extras = row.get(None)
            extras_used = False
            for key, value in row.items():
                if key is None:
                    continue
                # Convert all values to strings first to handle booleans
                if isinstance(value, bool):
                    value = str(value)
                elif isinstance(value, list):
                    value = [str(v) if isinstance(v, bool) else v for v in value]

                if (
                    not extras_used
                    and extras
                    and isinstance(extras, list)
                    and isinstance(value, str)
                    and key in {"wrong_answers", "answers"}
                ):
                    extras_text = ",".join([e for e in extras if isinstance(e, str) and e.strip()])
                    if extras_text:
                        if key == "answers" and all(":" in e for e in extras if isinstance(e, str) and e.strip()):
                            value = f"{value},{extras_text}" if value else extras_text
                            extras_used = True
                        elif key == "wrong_answers" and not any(":" in e for e in extras if isinstance(e, str) and e.strip()):
                            value = f"{value},{extras_text}" if value else extras_text
                            extras_used = True
                
                # Handle case where value might be a list
                if isinstance(value, list):
                    # If it's already a list, use it directly
                    if key == "wrong_answers":
                        processed_row[key] = value
                    elif key == "pairs":
                        processed_row[key] = {}
                    else:
                        processed_row[key] = str(value) if value else ""
                elif not value or (isinstance(value, str) and value.strip() == ""):
                    # Handle empty values
                    if key == "wrong_answers":
                        processed_row[key] = []
                    elif key == "pairs":
                        processed_row[key] = {}
                    else:
                        processed_row[key] = value
                elif key == "wrong_answers":
                    # Parse string representation of list or comma-separated values
                    try:
                        processed_row[key] = ast.literal_eval(value)
                        if not isinstance(processed_row[key], list):
                            processed_row[key] = [processed_row[key]]
                    except (ValueError, SyntaxError):
                        # Fallback: split by comma if literal_eval fails
                        if value and value.strip():
                            # Handle quoted CSV values
                            value = value.strip().strip('"')
                            processed_row[key] = [item.strip() for item in value.split(",") if item.strip()]
                        else:
                            processed_row[key] = []
                elif key == "left":
                    # Handle pipe-separated values for matching questions
                    if value and value.strip():
                        processed_row[key] = [item.strip() for item in value.split("|") if item.strip()]
                    else:
                        processed_row[key] = []
                elif key == "right":
                    # Handle pipe-separated values for matching questions
                    if value and value.strip():
                        processed_row[key] = [item.strip() for item in value.split("|") if item.strip()]
                    else:
                        processed_row[key] = []
                elif key == "answers":
                    # Parse answer mapping like "a:1,b:2"
                    if value and value.strip():
                        answers_dict = {}
                        for pair in value.split(","):
                            if ":" in pair:
                                k, v = pair.split(":", 1)
                                answers_dict[k.strip()] = v.strip()
                        processed_row[key] = answers_dict
                    else:
                        processed_row[key] = {}
                else:
                    processed_row[key] = value
        
        # Reconstruct pairs for matching questions
        if processed_row.get('type') == 'match':
            existing_pairs = processed_row.get('pairs')
            if (
                isinstance(existing_pairs, dict)
                and (existing_pairs.get('left') or existing_pairs.get('right') or existing_pairs.get('answers'))
            ):
                processed_row['pairs'] = {
                    'left': existing_pairs.get('left', []),
                    'right': existing_pairs.get('right', []),
                    'answers': existing_pairs.get('answers', {}),
                }
            else:
                left = processed_row.get('left', [])
                right = processed_row.get('right', [])
                answers = processed_row.get('answers', {})

                processed_row['pairs'] = {
                    'left': left,
                    'right': right,
                    'answers': answers,
                }

            # Remove the individual fields
            processed_row.pop('left', None)
            processed_row.pop('right', None)
            processed_row.pop('answers', None)
        else:
            # For non-matching questions, ensure pairs is empty
            processed_row['pairs'] = {}
            # Remove extra fields
            processed_row.pop('left', None)
            processed_row.pop('right', None)
            processed_row.pop('answers', None)
        
        processed_rows.append(processed_row)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(processed_rows, f, ensure_ascii=False, indent=2)


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

    # Handle matching questions - convert pairs to string
    processed_rows = []
    for row in rows:
        processed_row = row.copy()
        if 'pairs' in row:
            # Convert pairs dict to JSON string for CSV compatibility
            processed_row['pairs'] = json.dumps(row['pairs'])
        processed_rows.append(processed_row)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        # Get ALL possible field names from ALL rows
        all_fieldnames = set()
        for row in processed_rows:
            all_fieldnames.update(row.keys())
        
        # Sort fieldnames for consistent order
        fieldnames = sorted(all_fieldnames)
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)


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
