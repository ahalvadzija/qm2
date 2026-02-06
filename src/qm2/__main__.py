import argparse
import importlib.metadata
from .app import main as run_app
from qm2.paths import ensure_dirs, migrate_legacy_paths

def main():
    # Get version from metadata automatically
    try:
        __version__ = importlib.metadata.version("qm2")
    except importlib.metadata.PackageNotFoundError:
        __version__ = "1.0.17" # Fallback

    parser = argparse.ArgumentParser(
        prog="qm2", 
        description="Quiz Maker 2 (QM2) - Interactive Terminal Quiz Application"
    )
    
    parser.add_argument(
        "-v", "--version", 
        action="version", 
        version=f"qm2 {__version__}" # Now it uses the dynamic version
    )

    # Parse arguments
    parser.parse_args()

    # 🔹 1. Prepare application storage
    # If you later want to support custom data-dir, 
    # you would pass args.data_dir to these functions
    ensure_dirs()
    migrate_legacy_paths()

    # 🔹 2. Run the app
    run_app()

if __name__ == "__main__":
    main()