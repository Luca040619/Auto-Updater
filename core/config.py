import os
import json

def get_default_config():
    return {
        "launchers": {},
        "shutdown": {
            "enabled_criteria": {
                "monitor_download": True,
                "monitor_upload": False,
                "monitor_disk_read": False,
                "monitor_disk_write": False
            },
            "thresholds": {
                "download": {
                    "value": 200,
                    "unit": "KB/s"
                },
                "upload": {
                    "value": 100,
                    "unit": "KB/s"
                },
                "disk_read": {
                    "value": 5,
                    "unit": "MB/s"
                },
                "disk_write": {
                    "value": 5,
                    "unit": "MB/s"
                }
            },
            "timeout_seconds": 60
        }
    }

def get_config_path():
    appdata = os.getenv("APPDATA") or os.path.expanduser("~/.config")
    config_dir = os.path.join(appdata, "AutoUpdater")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")

def config_path_exists():
    return os.path.exists(get_config_path())

def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        default = get_default_config()
        save_config(default)
        return default

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def save_config(config):
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)