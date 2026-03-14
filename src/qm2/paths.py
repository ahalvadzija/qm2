from __future__ import annotations

import json
from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "qm2"
APP_AUTHOR = "Adnan Halvadžija"

# Main application data directory (cross-platform):
#  - Linux:  ~/.local/share/qm2
#  - macOS:  ~/Library/Application Support/qm2
#  - Windows: %LOCALAPPDATA%/qm2
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))

# Subdirectories / files of interest
CATEGORIES_DIR = DATA_DIR / "categories"
CSV_DIR = DATA_DIR / "csv"
SCORES_FILE = DATA_DIR / "scores.json"
CONFIG_FILE = DATA_DIR / "config.json"


def ensure_dirs() -> None:
    """Create required directories if they don’t already exist."""
    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize config file with default model if it doesn't exist
    if not CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"model": "gemini-2.0-flash-exp"}, f)
        except Exception:
            pass


def get_ai_config() -> dict:
    """Read AI configuration from the config file."""
    if not CONFIG_FILE.exists():
        return {"model": "gemini-2.0-flash-exp"}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"model": "gemini-2.0-flash-exp"}


def save_ai_config(config: dict) -> None:
    """Save AI configuration to the config file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass


def migrate_legacy_paths(project_root: Path | None = None) -> None:
    """
    Gently migrate old files/directories to the new structure if they exist:
      - scores.json from $HOME or CWD
      - 'categories/*.json' from CWD
    Does not overwrite existing new files.
    """
    ensure_dirs()

    # 1) scores.json in HOME or CWD
    legacy_scores = [Path.home() / "scores.json", Path("scores.json")]
    for src in legacy_scores:
        try:
            if src.exists() and not SCORES_FILE.exists():
                SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
                src.replace(SCORES_FILE)
        except Exception:
            # Soft-fail: migration should not break the app
            pass

    # 2) categories directory in CWD → move .json files
    legacy_categories_dir = Path("categories")
    if legacy_categories_dir.exists() and legacy_categories_dir.is_dir():
        for json_file in legacy_categories_dir.glob("*.json"):
            target = CATEGORIES_DIR / json_file.name
            try:
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    json_file.replace(target)
            except Exception:
                pass