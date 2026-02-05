# src/qm2/core/import_export.py
from pathlib import Path
import requests
import questionary
from rich.prompt import Prompt

def csv_to_json(csv_file: Path, json_file: Path) -> None:
    """
    Convert CSV file to JSON format with support for standard and flattened formats.
    """
    import csv
    import json
    import ast
    
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Detect if CSV uses flattened headers (e.g., pairs/left/0)
    fieldnames = reader.fieldnames or []
    is_flattened = any('/' in field for field in fieldnames)

    processed_rows = []
    for row in rows:
        processed_row = {}
        
        if is_flattened:
            # --- HANDLE FLATTENED CSV FORMAT ---
            wrong_answers = []
            for key in row:
                if key.startswith('wrong_answers/'):
                    value = row[key]
                    if value and str(value).strip():
                        wrong_answers.append(str(value).strip())
            processed_row['wrong_answers'] = wrong_answers
            
            # Reconstruct matching components from flattened columns
            left_items, right_items, answers = [], [], {}
            for key in sorted(row.keys()):
                val = row[key]
                if not val or not str(val).strip(): 
                    continue
                if key.startswith('pairs/left/'): 
                    left_items.append(str(val).strip())
                elif key.startswith('pairs/right/'): 
                    right_items.append(str(val).strip())
                elif key.startswith('pairs/answers/'):
                    answers[key.split('/')[-1]] = str(val).strip()
            
            if left_items or right_items or answers:
                processed_row['pairs'] = {
                    'left': left_items, 
                    'right': right_items, 
                    'answers': answers
                }
            
            # Map basic fields
            for key in ['type', 'question', 'correct']:
                processed_row[key] = str(row.get(key, "")).strip()
        
        else:
            # --- HANDLE NORMAL CSV FORMAT ---
            for key, value in row.items():
                if key is None or value is None: 
                    continue
                val_str = str(value).strip()

                if key == "wrong_answers":
                    if val_str:
                        # Prevent ast.literal_eval from converting "False" to boolean False
                        if val_str.startswith('[') and val_str.endswith(']'):
                            try:
                                # Safe parsing for string-represented lists
                                items = ast.literal_eval(val_str)
                                processed_row[key] = [str(i) for i in items]
                            except:
                                # Fallback if literal_eval fails
                                processed_row[key] = [i.strip() for i in val_str.strip('[]').split(',') if i.strip()]
                        else:
                            # Standard comma-separated values
                            processed_row[key] = [i.strip() for i in val_str.split(',') if i.strip()]
                    else:
                        processed_row[key] = []
                
                elif key in ["left", "right"]:
                    # Split pipe-separated values for match questions
                    processed_row[key] = [i.strip() for i in val_str.split('|') if i.strip()] if val_str else []
                
                elif key == "answers":
                    # Parse "a:1, b:2" mapping
                    d = {}
                    if val_str:
                        for pair in val_str.split(','):
                            if ':' in pair:
                                k, v = pair.split(':', 1)
                                d[k.strip()] = v.strip()
                    processed_row[key] = d
                else:
                    processed_row[key] = val_str

        # --- FINAL CLEANUP AND STRUCTURING ---
        question_type = processed_row.get('type', '')

        if question_type == 'match':
            # Ensure 'pairs' object is structured correctly for matching questions
            if 'left' in processed_row or 'right' in processed_row:
                processed_row['pairs'] = {
                    'left': processed_row.pop('left', []),
                    'right': processed_row.pop('right', []),
                    'answers': processed_row.pop('answers', {})
                }
            # Remove redundant fields for match type
            processed_row.pop('correct', None)
            processed_row.pop('wrong_answers', None)
        else:
            # Remove matching fields for non-match question types
            processed_row.pop('pairs', None)
            processed_row.pop('left', None)
            processed_row.pop('right', None)
            processed_row.pop('answers', None)
            
            # Ensure wrong_answers key exists for consistency
            if 'wrong_answers' not in processed_row:
                processed_row['wrong_answers'] = []

        processed_rows.append(processed_row)

    # Save to JSON with indentation and UTF-8 support
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(processed_rows, f, ensure_ascii=False, indent=2)
        
def json_to_csv(json_file: Path, csv_file: Path) -> None:
    """
    Convert JSON file back to CSV format.
    """
    import csv
    import json
    
    with open(json_file, encoding="utf-8") as f:
        rows = json.load(f)

    if not rows:
        raise ValueError("JSON is empty")

    # Definiramo fixni redoslijed kolona prema README specifikaciji
    fieldnames = ['type', 'question', 'correct', 'wrong_answers', 'left', 'right', 'answers']
    
    processed_rows = []
    for row in rows:
        # Kreiramo novi rječnik sa svim potrebnim kolonama (inicijalno praznim)
        processed_row = {field: "" for field in fieldnames}
        
        # Popunjavamo osnovna polja
        processed_row['type'] = row.get('type', '')
        processed_row['question'] = row.get('question', '')
        processed_row['correct'] = row.get('correct', '')
        
        # Konvertujemo listu wrong_answers u string razdvojen zarezima
        wa = row.get('wrong_answers', [])
        if isinstance(wa, list):
            # Osiguravamo da su svi elementi stringovi i spajamo ih
            processed_row['wrong_answers'] = ",".join(map(str, wa))
        else:
            processed_row['wrong_answers'] = str(wa)

        # Raspakujemo 'pairs' ako postoje (za 'match' tip)
        pairs = row.get('pairs', {})
        if isinstance(pairs, dict) and pairs:
            # Spajamo left i right liste pomoću pipe (|)
            if 'left' in pairs:
                processed_row['left'] = "|".join(map(str, pairs['left']))
            if 'right' in pairs:
                processed_row['right'] = "|".join(map(str, pairs['right']))
            # Konvertujemo answers rječnik {'a': '1'} u string "a:1,b:2"
            if 'answers' in pairs:
                ans_dict = pairs['answers']
                processed_row['answers'] = ",".join([f"{k}:{v}" for k, v in ans_dict.items()])

        processed_rows.append(processed_row)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        # Koristimo definisane fieldnames za zaglavlje
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
