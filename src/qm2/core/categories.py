from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import questionary
from rich.console import Console
from rich.prompt import Prompt

from qm2.paths import CATEGORIES_DIR, CSV_DIR
from qm2.utils.files import save_json

categories_cache: list[str] | None = None
console = Console()


def categories_root_dir() -> str:
    """Return the categories directory (platformdirs-based)."""
    return str(CATEGORIES_DIR)


def csv_root_dir() -> str:
    """Return the CSV directory (platformdirs-based)."""
    return str(CSV_DIR)

def refresh_csv_cache() -> list[str]:
    """Get list of CSV files (no caching for now)."""
    try:
        return [
            f.name for f in os.scandir(csv_root_dir())
            if f.is_file() and f.name.endswith(".csv")
        ]
    except (FileNotFoundError, PermissionError):
        return []

def get_categories(
    use_cache: bool = True, root_dir: str | None = None
) -> list[str]:
    if root_dir is None:
        root_dir = categories_root_dir()
    
    global categories_cache
    if not use_cache or categories_cache is None:
        refresh_categories_cache(root_dir)
    # Return a sanitized copy to avoid external mutations and accidental UI items in cache
    base = categories_cache or []
    cats = [c for c in base if isinstance(c, str) and c.endswith(".json")]
    return list(cats)

def _get_formatted_choices() -> list[Choice]:
    """Helper to get paginated-ready choices for category files."""
    rel_files = get_categories()
    choices = []
    for f in rel_files:
        p = Path(f)

        category_name = p.parent.name if p.parent.name and p.parent.name != "." else "General"
        
        display = f"📁 {category_name} › {p.stem}"
        
        choices.append(Choice(title=display, value=f))
        
    return choices

def select_category(allow_create: bool = True) -> str | None:
    categories = get_categories()
    choices = categories + (["➕ Create new"] if allow_create else []) + ["↩ Back"]

    choice = questionary.select("📂 Select a category:", choices=choices).ask()

    if choice is None or choice == "↩ Back":
        return None

    if choice == "➕ Create new":
        name = Prompt.ask("Enter file name (e.g., geography.json)").strip()
        base = os.path.splitext(name)[0]
        filename = base + ".json"
        path = os.path.join(categories_root_dir(), filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        save_json(path, [])
        return path

    return os.path.join(categories_root_dir(), choice)

def categories_add(path: str, root_dir: str | None = None) -> None:
    if root_dir is None:
        root_dir = categories_root_dir()
    
    global categories_cache
    if categories_cache is None:
        return
    rel = _rel_from_root(path, root_dir)
    if rel not in categories_cache:
        categories_cache.append(rel)
        categories_cache.sort()

def create_new_category(root_dir: str | None = None) -> None:
    if root_dir is None:
        root_dir = categories_root_dir()
    folder = Prompt.ask("📁 Enter a folder inside 'categories' (e.g., programming/python)").strip()
    # Validate folder name
    if not folder or any(c in folder for c in ["<", ">", ":", '"', "|", "?", "*"]):
        console.print("[red]⚠️ Invalid folder name. Please avoid special characters.")
        return

    name = Prompt.ask("📄 Enter file name (e.g., loops.json)").strip()
    # Validate file name
    if not name or any(c in name for c in ["<", ">", ":", '"', "|", "?", "*"]):
        console.print("[red]⚠️ Invalid file name. Please avoid special characters.")
        return
    path = os.path.join(root_dir, folder, name if name.endswith(".json") else f"{name}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    save_json(path, [])
    categories_add(path)
    refresh_categories_cache()  # Refresh cache after creation
    console.print(f"[green]✅ New category created: {path}")

def save_category_file(path: str, data: list[Any] | dict[str, Any]) -> bool:
    """Save category file and also update categories cache."""
    if save_json(path, data):
        categories_add(path)
        return True
    return False

def rename_category(root_dir: str | None = None) -> None:
    if root_dir is None:
        root_dir = categories_root_dir()
    
    # use helper to get formatted choices for pagination (returns list of Choice objects with 'value' as relative path)
    choices = _get_formatted_choices()
    
    if not choices:
        console.print("[yellow]⚠️ No categories to rename.")
        return

    # use pagination select, it will return the 'value' from Choice (relative path) or "back"/None
    choice = select_with_pagination("✏️ Choose a category to rename:", choices)
    
    if choice == "↩ Back" or choice is None:
        return

    # 'choice' is now the relative path of the selected category file, we can construct the absolute path
    old_path = os.path.join(root_dir, choice)
    
    # show current name and prompt for new name
    current_stem = Path(old_path).stem
    new_name_input = Prompt.ask(f"📝 New name for '{current_stem}' (without .json)").strip()

    if not new_name_input:
        console.print("[yellow]↩ Rename canceled (empty name).")
        return

    # Validate new name for invalid characters
    if any(c in new_name_input for c in ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]):
        console.print("[red]⚠️ Invalid characters in name.")
        return

    # Normalize new name to ensure it ends with .json
    new_name = Path(new_name_input).stem + ".json"
    new_path = os.path.join(os.path.dirname(old_path), new_name)

    # check if new path already exists and is different from old path
    if os.path.exists(new_path) and old_path != new_path:
        confirm = questionary.confirm(f"⚠️ File '{new_name}' already exists. Overwrite?").ask()
        if not confirm:
            console.print("[yellow]↩ Rename canceled.")
            return

    try:
        os.rename(old_path, new_path)
        
        # update cache: remove old relative path and add new relative path
        new_rel_path = os.path.relpath(new_path, root_dir)
        categories_rename(choice, new_rel_path)
        refresh_categories_cache()
        
        console.print(f"[green]✅ Renamed to: {new_name}")
    except OSError as e:
        console.print(f"[red]⚠️ Error renaming file: {e}")

def categories_remove(path: str, root_dir: str | None = None) -> None:
    if root_dir is None:
        root_dir = categories_root_dir()

    global categories_cache
    if categories_cache is None:
        return
    rel = _rel_from_root(path, root_dir)
    if rel in categories_cache:
        categories_cache.remove(rel)

def delete_category(root_dir: str | None = None) -> None:
    if root_dir is None:
        root_dir = categories_root_dir()

    choices = _get_formatted_choices() # Call helper to get Choice objects for pagination
    if not choices:
        console.print("[yellow]⚠️ No categories to delete.")
        return

    # call pagination with Choice objects, it will return the 'value' (relative path) or "back"
    choice = select_with_pagination("🗑️ Choose a category to delete:", choices)
    
    # select_with_pagination returns the 'value' from Choice (relative path) or "back"/None
    if choice == "back" or choice == "↩ Back" or choice is None:
        return

    path = os.path.join(root_dir, choice)
    
    # For confirmation, we can show the formatted name again for better UX
    confirm = questionary.confirm(f"⚠️ Are you sure you want to delete: {choice}?").ask()
    if confirm:
        try:
            os.remove(path)
            categories_remove(choice)
            refresh_categories_cache()
            console.print(f"[red]❌ Category deleted: {choice}")
        except OSError as e:
            console.print(f"[red]⚠️ Error: {e}")

def categories_rename(
    old_path: str, new_path: str, root_dir: str | None = None
) -> None:
    global categories_cache
    if categories_cache is None:
        return
    old_rel = _rel_from_root(old_path, root_dir)
    new_rel = _rel_from_root(new_path, root_dir)
    if old_rel in categories_cache:
        categories_cache.remove(old_rel)
    if new_rel not in categories_cache:
        categories_cache.append(new_rel)
        categories_cache.sort()
        
def refresh_categories_cache(root_dir: str | None = None) -> list[str]:
    if root_dir is None:
        root_dir = categories_root_dir()
        
    global categories_cache
    categories = []
    if os.path.exists(root_dir):
        for dirpath, _, filenames in os.walk(root_dir):
            for f in filenames:
                if f.endswith(".json"):
                    categories.append(os.path.relpath(os.path.join(dirpath, f), root_dir))
    categories_cache = sorted(set(categories))
    return categories_cache

def _rel_from_root(path: str, root_dir: str | None = None) -> str:
    if root_dir is None:
        root_dir = categories_root_dir()

    abs_root = os.path.abspath(root_dir)
    abs_path = os.path.abspath(path)
    try:
        common = os.path.commonpath([abs_root, abs_path])
    except Exception:
        common = abs_root
    if common == abs_root:
        return os.path.relpath(abs_path, abs_root)
    # path is already relative or outside root; return as-is
    if path.startswith(root_dir + os.sep):
        return os.path.relpath(path, root_dir)
    return path

def delete_json_quiz_file(root_dir: str | None = None) -> None:
    if root_dir is None:
        root_dir = categories_root_dir()
        
    json_rel = get_categories()

    if not json_rel:
        console.print("[yellow]⚠️ No .json files available to delete.")
        return

    choices = json_rel + ["↩ Back"]

    choice = questionary.select("🗑️ Choose a .json file to delete:", choices=choices).ask()

    if choice == "↩ Back":
        return

    file_to_delete = os.path.join(root_dir, choice)
    confirm = questionary.confirm(f"⚠️ Do you really want to delete: [bold]{choice}[/]?").ask()
    if confirm:
        try:
            os.remove(file_to_delete)
            categories_remove(choice)
            refresh_categories_cache()  # Refresh cache after deletion
            console.print(f"[red]🗑️ File '{choice}' deleted.")
        except OSError as e:
            console.print(f"[red]⚠️ Error deleting file: {e}")
            return
    else:
        console.print("[yellow]↩ Deletion canceled.")