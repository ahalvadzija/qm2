from .app import main
from qm2.paths import ensure_dirs, migrate_legacy_paths

if __name__ == "__main__":
    # 🔹 1. Prepare application storage
    ensure_dirs()
    migrate_legacy_paths()

    # 🔹 2. Run the app
    main()
