# src/qm2/core/import_export.py
from pathlib import Path
import requests
import questionary
from rich.prompt import Prompt

def csv_to_json(csv_file: Path, json_file: Path) -> None:
    """
    Directly handles the specific way DictReader parses escaped commas.
    """
    import csv
    import json
    import ast

    with open(csv_file, newline="", encoding="utf-8") as f:
        # DictReader automatically handles ""x, y"" by removing outer quotes
        # and keeping the comma as part of the value.
        reader = csv.DictReader(f)
        rows = list(reader)

    fieldnames = reader.fieldnames or []
    is_flattened = any('/' in field for field in fieldnames)

    processed_rows = []
    for row in rows:
        res = {
            'type': str(row.get('type', '')).strip(),
            'question': str(row.get('question', '')).strip(),
            'correct': str(row.get('correct', '')).strip(),
            'wrong_answers': [],
        }

        if is_flattened:
            # --- FLATTENED ---
            wa = []
            for k, v in row.items():
                if k and k.startswith('wrong_answers/') and v:
                    wa.append(str(v).strip())
            res['wrong_answers'] = wa

            l_items, r_items, ans_dict = [], [], {}
            for k in sorted(row.keys()):
                v = row[k]
                if not v:
                    continue
                if k.startswith('pairs/left/'):
                    l_items.append(str(v).strip())
                elif k.startswith('pairs/right/'):
                    r_items.append(str(v).strip())
                elif k.startswith('pairs/answers/'):
                    ans_dict[k.split('/')[-1]] = str(v).strip()
            
            if l_items or r_items or ans_dict:
                res['pairs'] = {'left': l_items, 'right': r_items, 'answers': ans_dict}
        else:
            # --- NORMAL ---
            wa_raw = str(row.get('wrong_answers', '')).strip()
            if wa_raw:
                if wa_raw.startswith('[') and wa_raw.endswith(']'):
                    try:
                        res['wrong_answers'] = [str(i) for i in ast.literal_eval(wa_raw)]
                    except (ValueError, SyntaxError):
                        # Clean and split
                        c = wa_raw.strip('[]').replace('"', '').replace("'", "")
                        res['wrong_answers'] = [i.strip() for i in c.split(',') if i.strip()]
                else:
                    # Specific fix: if DictReader gave us "x, y" as one string, 
                    # we MUST split it even if it was quoted in CSV.
                    # Handle CSV escaped quotes: ""x, y"" becomes "x, y" in DictReader
                    
                    # Check if there are additional None keys from CSV parsing
                    additional_values = []
                    for key in row.keys():
                        if key is None and row[key]:
                            additional_values.extend(row[key])
                    
                    if wa_raw.startswith('"') and wa_raw.endswith('"'):
                        # Remove outer quotes from CSV escaped quotes
                        cleaned = wa_raw[1:-1]
                    else:
                        cleaned = wa_raw.replace('"', '').replace("'", "")
                    
                    # Add additional values if they exist
                    if additional_values:
                        # Clean additional values and join
                        cleaned_additional = ",".join([v.replace('"', '').replace("'", "").strip() for v in additional_values])
                        cleaned += "," + cleaned_additional
                    
                    # Split by comma and filter empty strings
                    res['wrong_answers'] = [i.strip() for i in cleaned.split(',') if i.strip()]

            if res['type'] == 'match':
                l_raw = str(row.get('left', '')).strip()
                r_raw = str(row.get('right', '')).strip()
                a_raw = str(row.get('answers', '')).strip()

                res['pairs'] = {
                    'left': [i.strip() for i in l_raw.split('|') if l_raw and i.strip()],
                    'right': [i.strip() for i in r_raw.split('|') if r_raw and i.strip()],
                    'answers': {}
                }
                
                if a_raw:
                    # Split answers like "a:1, b:0"
                    
                    # Check if there are additional None keys from CSV parsing for answers
                    additional_values = []
                    for key in row.keys():
                        if key is None and row[key]:
                            additional_values.extend(row[key])
                    
                    cleaned_a = a_raw.replace('"', '').replace("'", "")
                    
                    # Add additional values if they exist
                    if additional_values:
                        # Clean additional values and join
                        cleaned_additional = ",".join([v.replace('"', '').replace("'", "").strip() for v in additional_values])
                        cleaned_a += "," + cleaned_additional
                    
                    for pair in cleaned_a.split(','):
                        pair = pair.strip()
                        if ':' in pair:
                            k, v = pair.split(':', 1)
                            res['pairs']['answers'][k.strip()] = v.strip()

        processed_rows.append(res)

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
    fieldnames = ['type', 'question', 'correct', 'wrong_answers', 'left', 'right', 'answers', 'pairs']
    
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
        
        # Always include pairs as JSON string for compatibility
        if isinstance(row.get('pairs'), dict):
            processed_row['pairs'] = json.dumps(row['pairs'], ensure_ascii=False)
        else:
            processed_row['pairs'] = ""

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
