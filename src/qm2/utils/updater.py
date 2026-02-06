import requests
import importlib.metadata
from rich.console import Console
# Initialize console for standalone utility output if needed
console = Console()

def get_current_version():
    """Returns the version of qm2 as defined in pyproject.toml."""
    try:
        # Automatically grabs version from installed package metadata
        return importlib.metadata.version("qm2")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"

def check_for_updates():
    """
    Checks GitHub for a newer version.
    Returns: (bool, str) -> (update_available, latest_version)
    """
    repo_url = "https://api.github.com/repos/ahalvadzija/qm2/releases/latest"
    current_v = get_current_version()
    
    try:
        # 5 second timeout to prevent hanging on slow connections
        response = requests.get(repo_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        latest_v = data["tag_name"].lstrip('v')
        
        # Simple string comparison works for semantic versioning
        if latest_v > current_v:
            return True, latest_v
        return False, latest_v
        
    except Exception:
        # Fail silently or return None if offline
        return None, None