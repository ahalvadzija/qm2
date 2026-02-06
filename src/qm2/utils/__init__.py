from .files import load_json, load_json_result, save_json
from .updater import check_for_updates, get_current_version

# Exporting these functions makes them accessible directly via qm2.utils
__all__ = ["load_json", "load_json_result", "save_json", "check_for_updates", "get_current_version"]