import json
from pathlib import Path
import qm2.paths as paths
import os
import importlib
from unittest.mock import patch
import qm2.paths



def test_migrate_scores_from_home(tmp_path, monkeypatch):
    # 🔹 1. Fake HOME dir
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # 🔹 2. Legacy scores.json
    legacy_file = fake_home / "scores.json"
    legacy_data = {"score": 123}
    legacy_file.write_text(json.dumps(legacy_data), encoding="utf-8")

    # 🔹 3. Patch DATA_DIR
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(paths, "SCORES_FILE", paths.DATA_DIR / "scores.json")
    monkeypatch.setattr(paths, "CATEGORIES_DIR", paths.DATA_DIR / "categories")
    monkeypatch.setattr(paths, "CSV_DIR", paths.DATA_DIR / "csv")

    # 🔹 4. Run migration
    paths.migrate_legacy_paths()

    # 🐞 DEBUG: print what happened
    print("\nTMP PATH:", tmp_path)
    print("FILES AFTER MIGRATION:", list(tmp_path.rglob("*")))

    # 🔹 5. Assertions
    new_file = paths.SCORES_FILE
    assert new_file.exists()
    assert json.loads(new_file.read_text(encoding="utf-8")) == legacy_data
    assert not legacy_file.exists()


def test_migrate_categories_from_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # 🔹 2. Legacy "categories"
    legacy_dir = tmp_path / "categories"
    legacy_dir.mkdir()
    legacy_file = legacy_dir / "old.json"
    legacy_data = [{"q": "2+2", "a": "4"}]
    legacy_file.write_text(json.dumps(legacy_data), encoding="utf-8")

    # 🔹 3. Patch DATA_DIR
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(paths, "SCORES_FILE", paths.DATA_DIR / "scores.json")
    monkeypatch.setattr(paths, "CATEGORIES_DIR", paths.DATA_DIR / "categories")
    monkeypatch.setattr(paths, "CSV_DIR", paths.DATA_DIR / "csv")

    # 🔹 4. Run migration
    paths.migrate_legacy_paths()

    # 🐞 DEBUG: print state
    print("\nTMP PATH:", tmp_path)
    print("FILES AFTER MIGRATION:", list(tmp_path.rglob("*")))

    # 🔹 5. Assertions
    new_file = paths.CATEGORIES_DIR / "old.json"
    assert new_file.exists()
    assert json.loads(new_file.read_text(encoding="utf-8")) == legacy_data
    assert not legacy_file.exists()

def test_paths_creation_error_handling():
    """
    Test the error handling logic in paths.py when directory creation fails.
    By mocking os.makedirs to raise a PermissionError, we force the code 
    to execute the 'except' blocks (lines 44-46, 57-58).
    """
    # Mock os.makedirs to simulate a lack of write permissions
    with patch('os.makedirs', side_effect=PermissionError("No access")):
        # Reload the module to trigger the path initialization logic again under the mock
        importlib.reload(qm2.paths)
    
    # If no unhandled exception was raised, the 'except' block in paths.py 
    # successfully caught the PermissionError
    assert True