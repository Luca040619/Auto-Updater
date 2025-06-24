from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo

def get_icon_from_exe(path: str) -> QIcon:
    info = QFileInfo(path)
    provider = QFileIconProvider()
    return provider.icon(info)