import argparse
import sys
from .app import main as run_app
from qm2.paths import ensure_dirs, migrate_legacy_paths

def main():
    # Define the argument parser
    parser = argparse.ArgumentParser(
        prog="qm2", 
        description="Quiz Maker 2 (QM2) - Interactive Terminal Quiz Application"
    )
    
    # Add --version
    parser.add_argument(
        "-v", "--version", 
        action="version", 
        version="qm2 1.0.11" # Update this whenever you bump version
    )
    
    # Add --data-dir (even if you don't use it yet in app.main, 
    # it's good to have it parsed)
    parser.add_argument(
        "--data-dir", 
        type=str, 
        help="Path to custom data directory"
    )

    # Parse arguments
    args = parser.parse_args()

    # 🔹 1. Prepare application storage
    # If you later want to support custom data-dir, 
    # you would pass args.data_dir to these functions
    ensure_dirs()
    migrate_legacy_paths()

    # 🔹 2. Run the app
    run_app()

if __name__ == "__main__":
    main()