from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()
questions_cache: dict[str, dict[str, Any]] = {}


def load_json(filename: str | Path) -> list[Any] | dict[str, Any]:
    """
    Load JSON from file. Returns empty list on any error.
    For detailed error info, use load_json_result().
    """
    data, error = load_json_result(filename)
    return data


def load_json_result(filename: str | Path) -> tuple[list[Any] | dict[str, Any], str | None]:
    """
    Load JSON from file. Returns (data, error_message).
    On success: (data, None)
    On error: ([], "descriptive error message")
    """
    path = str(filename)
    if not os.path.exists(path):
        return [], f"File not found: {path}"

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Normalize None or non-list/dict to empty list for app compatibility
        if data is None or not isinstance(data, (list, dict)):
            return [], None
        return data, None
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in {path}: {e}"
        console.print(f"[red]⚠️ {msg}")
        return [], msg
    except UnicodeDecodeError as e:
        msg = f"Encoding error in {path}: {e}"
        console.print(f"[red]⚠️ {msg}")
        return [], msg
    except OSError as e:
        msg = f"Error reading {path}: {e}"
        console.print(f"[red]⚠️ {msg}")
        return [], msg
    except Exception as e:
        msg = f"Unexpected error reading {path}: {e}"
        console.print(f"[red]⚠️ {msg}")
        return [], msg


def save_json(filename: str | Path, data: list[Any] | dict[str, Any]) -> bool:
    path = str(filename)
    try:
        # Ensure directory exists (only if filename contains directory)
        dirname = os.path.dirname(path)
        if dirname:  # Only create directory if dirname is not empty
            os.makedirs(dirname, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        console.print(f"[red]⚠️ Error saving file {path}: {e}")
        return False
    except (TypeError, ValueError) as e:
        console.print(f"[red]⚠️ Error serializing data to JSON for {path}: {e}")
        return False

    # update caches
    try:
        abs_path = os.path.abspath(path)
        mtime = os.path.getmtime(abs_path)
        questions_cache[abs_path] = {"mtime": mtime, "data": data}
    except Exception:
        pass

    return True
