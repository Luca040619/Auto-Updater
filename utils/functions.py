from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo
from utils.launchers import KNOWN_LAUNCHERS
import psutil
import os
import json

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
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def save_config(config):
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_icon_from_exe(path: str) -> QIcon:
    info = QFileInfo(path)
    provider = QFileIconProvider()
    return provider.icon(info)

def search_default_programs():
    found = {}

    drives = [dp.device for dp in psutil.disk_partitions(all=False)]

    for drive in drives:
        for name, paths in KNOWN_LAUNCHERS.items():
            for rel_path in paths:
                full_path = os.path.join(drive, rel_path)
                if os.path.exists(full_path):
                    found[name] = full_path  # Salviamo il path, non solo True
                    break  # Stop al primo trovato

    return found

def get_size(bytes):
    """
    Returns size of bytes in a nice format
    """
    
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024