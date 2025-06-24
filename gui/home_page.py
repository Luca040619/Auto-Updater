from qfluentwidgets import (
    ProgressBar, TitleLabel, PrimaryPushButton,
    SwitchButton, StrongBodyLabel, CardWidget,
    FluentIcon, IconWidget, FluentIcon, IconWidget, CaptionLabel
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QScrollArea
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from utils.functions import get_icon_from_exe

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("home")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(16)

        self.title = TitleLabel("Auto Updater")
        self.main_layout.addWidget(self.title)

        self.info_card = CardWidget()
        self.main_layout.addWidget(self.info_card)

        self.setup_info_layout()

        self.apps_container = QWidget()
        self.apps_container.setStyleSheet("background-color: transparent;")
        self.apps_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.apps_list_layout = QVBoxLayout(self.apps_container)
        self.apps_list_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_list_layout.setSpacing(12)
        

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.apps_container)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        self.main_layout.addWidget(self.scroll_area)

        self.populate_app_list([
            ("Steam", True, "Scaricamento in corso..."),
            ("Epic Games", True, None),
            ("Battle.net", True, None),
            ("GOG.com", False, None)
        ])

    def setup_info_layout(self):
        info_layout = QVBoxLayout(self.info_card)
        self.info_card.setMaximumHeight(220) 
        self.info_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        info_layout.setContentsMargins(24, 16, 24, 16)
        info_layout.setSpacing(14)

         # Layout superiore con titolo a sinistra e rete a destra
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Titolo
        title_label = TitleLabel("Auto Updater")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        # Info rete con icone
        net_info_layout = QVBoxLayout()
        net_info_layout.setSpacing(4)
    
        # Upload
        upload_layout = QHBoxLayout()
        upload_layout.setSpacing(4)
        upload_icon = IconWidget(FluentIcon.UP.icon(), self)
        upload_speed = CaptionLabel("1.2 MB/s")
        upload_layout.addWidget(upload_icon)
        upload_layout.addWidget(upload_speed)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_info_layout.addLayout(upload_layout)

        # Download
        download_layout = QHBoxLayout()
        download_layout.setSpacing(4)
        download_icon = IconWidget(FluentIcon.DOWN.icon(), self)
        download_speed = CaptionLabel("4.5 MB/s")
        download_layout.addWidget(download_icon)
        download_layout.addWidget(download_speed)
        download_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_info_layout.addLayout(download_layout)

        top_layout.addLayout(net_info_layout)
        info_layout.addLayout(top_layout)

        # Progresso
        self.progress_label = StrongBodyLabel("Progresso aggiornamenti: 33%")
        info_layout.addWidget(self.progress_label)

        self.progress = ProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(33)
        info_layout.addWidget(self.progress)

        # Bottone
        self.start_button = PrimaryPushButton("Avvia sequenza aggiornamenti")
        self.start_button.setFixedHeight(40)
        info_layout.addWidget(self.start_button)

        self.main_layout.addWidget(self.info_card)

    def populate_app_list(self, app_data: list[tuple[str, bool, str | None]]):
        for name, is_active, status in app_data:
            self.add_app_item(name, is_active, status)

    def add_app_item(self, name: str, active: bool, status: str | None):
        item = QFrame()
        item.setObjectName("appItem")
        item.setStyleSheet("QFrame#appItem { border-radius: 8px; }")

        hl = QHBoxLayout(item)
        hl.setContentsMargins(12, 6, 12, 6)
        hl.setSpacing(10)

        # --- Ottieni il percorso dell'eseguibile (placeholder temporaneo) ---
        exe_paths = {
            "Steam": r"C:\Program Files (x86)\Steam\Steam.exe",
            "Epic Games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
            "Battle.net": r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe",
            "GOG.com": r"C:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe"
        }
        exe_path = exe_paths.get(name)

        # --- Icona dell'applicazione ---
        icon_label = QLabel()
        if exe_path:
            icon = get_icon_from_exe(exe_path)
            icon_label.setPixmap(icon.pixmap(24, 24))
        hl.addWidget(icon_label)

        # --- Nome ---
        name_label = StrongBodyLabel(name)
        name_label.setFont(QFont("Inter", 11))
        hl.addWidget(name_label)

        # --- Stato ---
        if status:
            status_label = QLabel(status)
            hl.addWidget(status_label)

        hl.addStretch()

        # --- Toggle ---
        toggle = SwitchButton()
        toggle.setChecked(active)
        hl.addWidget(toggle)

        self.apps_list_layout.addWidget(item)
