from PyQt6.QtWidgets import ( QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
                             QFileDialog, QFrame, QToolButton, QMenu, QSizePolicy )
from qfluentwidgets import (
    TitleLabel, BodyLabel, CardWidget, PrimaryPushButton,
    SwitchButton, FluentIcon, IconWidget, StrongBodyLabel, ToolButton, ScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from core.config import load_config
from utils.functions import get_icon_from_exe
import os


class SettingsPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings")
        self.setStyleSheet("background-color: transparent;")
        self.config = load_config()

        # Imposta i margini e layout principale
        self.view = QWidget()  # contenuto interno
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.main_layout = QVBoxLayout(self.view)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(24)
        self.view.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Titolo
        self.title = TitleLabel("Impostazioni")
        self.main_layout.addWidget(self.title)

        self.build_launcher_section()
        self.build_shutdown_section()
        self.build_legal_section()

    def build_launcher_section(self):
        launcher_card = CardWidget()
        launcher_layout = QVBoxLayout(launcher_card)
        launcher_layout.setContentsMargins(24, 16, 24, 16)
        launcher_layout.setSpacing(12)

        launcher_header = QHBoxLayout()
        launcher_header.setSpacing(8)
        launcher_icon = IconWidget(FluentIcon.APPLICATION)
        launcher_icon.setFixedSize(20, 20)
        launcher_header.addWidget(launcher_icon)
        launcher_header.addWidget(StrongBodyLabel("Launcher"))
        launcher_layout.addLayout(launcher_header)
        launcher_layout.addWidget(BodyLabel("Configura i launcher da aggiornare automaticamente. Puoi modificare il percorso o rimuoverli."))

        self.launcher_container = QVBoxLayout()
        self.launcher_container.setSpacing(12)
        launcher_layout.addLayout(self.launcher_container)

        for name, data in self.config.get("launchers", {}).items():
            self.add_launcher_entry(name, data)

        add_launcher_btn = PrimaryPushButton("Aggiungi nuovo launcher")
        launcher_layout.addWidget(add_launcher_btn)

        self.main_layout.addWidget(launcher_card)

    def add_launcher_entry(self, name, data):
        entry = QWidget()
        layout = QVBoxLayout(entry)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(20, 20)

        path = data.get("path")
        if path and os.path.exists(path):
            icon = get_icon_from_exe(path)
            icon_label.setPixmap(icon.pixmap(20, 20))
        else:
            icon_label = IconWidget(FluentIcon.GAME)
            icon_label.setFixedSize(20, 20)

        name_label = StrongBodyLabel(name)
        name_label.setMinimumWidth(120)

        path_input = QLineEdit()
        path_input.setText(data.get("path", ""))
        path_input.setDisabled(True)
        path_input.setPlaceholderText("Percorso del launcher")

        browse_btn = QToolButton()
        browse_btn.setText("...")
        browse_btn.setToolTip("Sfoglia")
        browse_btn.clicked.connect(lambda: self.choose_path(path_input))

        remove_btn = ToolButton(FluentIcon.DELETE)
        remove_btn.setToolTip("Rimuovi launcher")
        remove_btn.clicked.connect(lambda: self.remove_launcher(entry, name))

        top_row.addWidget(icon_label)
        top_row.addWidget(name_label)
        top_row.addWidget(path_input, 1)
        top_row.addWidget(browse_btn)
        top_row.addWidget(remove_btn)

        layout.addLayout(top_row)

        self.launcher_container.addWidget(entry)

    def choose_path(self, input_widget):
        path, _ = QFileDialog.getOpenFileName(caption="Seleziona il file eseguibile")
        if path:
            input_widget.setText(os.path.normpath(path))

    def remove_launcher(self, widget, name):
        widget.setParent(None)
        self.config["launchers"].pop(name, None)

    def build_shutdown_section(self):
        shutdown_card = CardWidget()
        shutdown_layout = QVBoxLayout(shutdown_card)
        shutdown_layout.setContentsMargins(24, 16, 24, 16)
        shutdown_layout.setSpacing(12)

        shutdown_header = QHBoxLayout()
        shutdown_header.setSpacing(8)
        shutdown_icon = IconWidget(FluentIcon.POWER_BUTTON)
        shutdown_icon.setFixedSize(20, 20)
        shutdown_header.addWidget(shutdown_icon)
        shutdown_header.addWidget(StrongBodyLabel("Spegnimento automatico"))
        shutdown_layout.addLayout(shutdown_header)
        shutdown_layout.addWidget(BodyLabel("Configura le soglie di traffico e disco per lo spegnimento automatico."))

        self.main_layout.addWidget(shutdown_card)

    def build_legal_section(self):
        legal_card = CardWidget()
        legal_layout = QVBoxLayout(legal_card)
        legal_layout.setContentsMargins(24, 16, 24, 16)
        legal_layout.setSpacing(12)

        legal_header = QHBoxLayout()
        legal_header.setSpacing(8)
        legal_icon = IconWidget(FluentIcon.INFO)
        legal_icon.setFixedSize(20, 20)
        legal_header.addWidget(legal_icon)
        legal_header.addWidget(StrongBodyLabel("Informazioni legali"))
        legal_layout.addLayout(legal_header)
        legal_layout.addWidget(BodyLabel("Visualizza termini di servizio, EULA e note di versione."))

        self.main_layout.addWidget(legal_card)