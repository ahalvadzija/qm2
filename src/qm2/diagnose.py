from qm2.paths import DATA_DIR, CATEGORIES_DIR, CSV_DIR, SCORES_FILE, ensure_dirs

def main() -> None:
    # Ensure dirs exist
    ensure_dirs()

    print("🔍 QM2 storage locations:")
    print(f"  DATA_DIR       = {DATA_DIR}")
    print(f"  CATEGORIES_DIR = {CATEGORIES_DIR}")
    print(f"  CSV_DIR        = {CSV_DIR}")
    print(f"  SCORES_FILE    = {SCORES_FILE}")

    print("\n✅ Directories created (if they were missing).")

if __name__ == "__main__":
    main()
