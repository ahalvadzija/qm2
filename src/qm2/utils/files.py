from rich.console import Console
import os
import json

from qm2.core.categories import categories_root_dir, categories_add

console = Console()
questions_cache = {}

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(f"[red]⚠️ Invalid JSON format in file: {filename}. Returning empty list.")
            return []
        except UnicodeDecodeError:
            console.print(f"[red]⚠️ Encoding error in file: {filename}. Returning empty list.")
            return []
        except Exception as e:
            console.print(f"[red]⚠️ Error reading file {filename}: {e}. Returning empty list.")
            return []
    return []

def save_json(filename, data):
    try:
        # Ensure directory exists (only if filename contains directory)
        dirname = os.path.dirname(filename)
        if dirname:  # Only create directory if dirname is not empty
            os.makedirs(dirname, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        console.print(f"[red]⚠️ Error saving file {filename}: {e}")
        return False
    except (TypeError, ValueError) as e:
        console.print(f"[red]⚠️ Error serializing data to JSON: {e}")
        return False

    # update caches
    try:
        abs_path = os.path.abspath(filename)
        mtime = os.path.getmtime(abs_path)
        questions_cache[abs_path] = {"mtime": mtime, "data": data}
    except Exception:
        pass
    # if saved under categories_root and is json, update categories cache
    try:
        abs_root = os.path.abspath(categories_root_dir())
        abs_file = os.path.abspath(filename)
        if abs_file.endswith(".json") and abs_file.startswith(abs_root + os.sep):
            categories_add(abs_file)
    except Exception:
        pass

    return True