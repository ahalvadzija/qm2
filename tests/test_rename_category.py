import qm2.core.categories as categories

def test_rename_category_normalizes_extension(monkeypatch, tmp_path):
    # Setup test directory
    monkeypatch.chdir(tmp_path)

    categories_dir = tmp_path / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure categories_root_dir returns our temp path
    monkeypatch.setattr(categories, "categories_root_dir", lambda: str(categories_dir))

    # Create dummy file to rename
    old_file = categories_dir / "old.json"
    old_file.write_text("[]", encoding="utf-8")

    # Mock get_categories to return our test file
    monkeypatch.setattr(categories, "get_categories", lambda: ["old.json"])
    
    # Mock the new pagination helper to simulate user selection
    monkeypatch.setattr("qm2.core.categories.select_with_pagination", lambda msg, choices: "old.json")
    
    # Mock Rich Prompt to simulate user typing the new name
    monkeypatch.setattr(categories, "Prompt", type("P", (), {"ask": staticmethod(lambda *args, **kwargs: "new")}))
    
    # Suppress console output and side effects during test
    monkeypatch.setattr(categories, "console", type("C", (), {"print": staticmethod(lambda *a, **k: None)}))
    monkeypatch.setattr(categories, "refresh_categories_cache", lambda *args: None)
    monkeypatch.setattr(categories, "categories_rename", lambda *args: None)

    # Run the rename logic
    categories.rename_category(root_dir=str(categories_dir))

    # Assertions
    assert (categories_dir / "new.json").exists()
    assert not (categories_dir / "old.json").exists()