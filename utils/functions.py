from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo
import sys
import os
import subprocess
import psutil
import json

from utils.launchers import KNOWN_LAUNCHERS

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

def restart_as_admin():
    executable = sys.executable
    script = sys.argv[0]
    args = sys.argv[1:]
    command = [executable, script] + args

    subprocess.run([
        "powershell",
        "-Command",
        f"Start-Process '{executable}' -ArgumentList '{' '.join([script] + args)}' -Verb runAs"
    ])
    sys.exit()  # chiude l'istanza attuale