from qfluentwidgets import (
    ProgressBar, TitleLabel, PrimaryPushButton,
    SwitchButton, StrongBodyLabel, CardWidget,
    FluentIcon, IconWidget, FluentIcon, IconWidget, CaptionLabel
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QScrollArea
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from utils.functions import get_icon_from_exe, load_config, save_config, get_size
from core.updater import Updater 
import os

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("home")
        self.config = load_config()

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(1000)  # ogni 1 secondo
        self.status_timer.timeout.connect(self.update_gui_from_updater)

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
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        self.launchers: dict = self.config.get("launchers", {})

        self.populate_app_list()

    def setup_info_layout(self):
        info_layout = QVBoxLayout(self.info_card)
        self.info_card.setMaximumHeight(220) 
        self.info_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        info_layout.setContentsMargins(24, 16, 24, 16)
        info_layout.setSpacing(14)

        # Layout superiore con titolo a sinistra e rete a destra
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        title_label = TitleLabel("Auto Updater")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        # --- Network info widgets salvati in self ---
        net_info_layout = QVBoxLayout()
        net_info_layout.setSpacing(4)

        # Upload
        upload_layout = QHBoxLayout()
        upload_layout.setSpacing(4)
        self.upload_icon = IconWidget(FluentIcon.UP.icon(), self)
        self.upload_speed_label = CaptionLabel("0 KB/s")
        upload_layout.addWidget(self.upload_icon)
        upload_layout.addWidget(self.upload_speed_label)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_info_layout.addLayout(upload_layout)

        # Download
        download_layout = QHBoxLayout()
        download_layout.setSpacing(4)
        self.download_icon = IconWidget(FluentIcon.DOWN.icon(), self)
        self.download_speed_label = CaptionLabel("0 KB/s")
        download_layout.addWidget(self.download_icon)
        download_layout.addWidget(self.download_speed_label)
        download_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_info_layout.addLayout(download_layout)

        top_layout.addLayout(net_info_layout)
        info_layout.addLayout(top_layout)

        # Progresso
        self.progress_label = StrongBodyLabel("Pronto per iniziare")
        info_layout.addWidget(self.progress_label)

        self.progress = ProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        info_layout.addWidget(self.progress)

        # Bottone dinamico
        self.start_button = PrimaryPushButton("Avvia sequenza aggiornamenti")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.toggle_updating)
        info_layout.addWidget(self.start_button)

        self.main_layout.addWidget(self.info_card)

        # Stato iniziale
        self.is_updating = False

    def populate_app_list(self):
        for name, data in self.launchers.items():
            path = data.get("path", "")
            enabled = data.get("enabled", False)
            self.add_app_item(name, enabled, path)

    def add_app_item(self, name: str, active: bool, path: str | None):
        item = QFrame()
        item.setObjectName("appItem")
        item.setStyleSheet("QFrame#appItem { border-radius: 8px; }")

        hl = QHBoxLayout(item)
        hl.setContentsMargins(12, 6, 12, 6)
        hl.setSpacing(10)

        # --- Icona dell'applicazione ---
        icon_label = QLabel()
        if path and os.path.exists(path):
            icon = get_icon_from_exe(path)
            icon_label.setPixmap(icon.pixmap(24, 24))
        hl.addWidget(icon_label)

        # --- Nome ---
        name_label = StrongBodyLabel(name)
        name_label.setFont(QFont("Inter", 11))
        hl.addWidget(name_label)

        # --- Percorso (opzionale da mostrare) ---
        if path:
            path_label = QLabel(f"...{os.path.sep}" + os.path.basename(path))
            path_label.setStyleSheet("color: gray; font-size: 10px;")
            hl.addWidget(path_label)

        hl.addStretch()

        # --- Toggle ---
        toggle = SwitchButton()
        toggle.setChecked(active)
        toggle.checkedChanged.connect(
            lambda checked, launcher=name: self._on_toggle_launcher(launcher, checked)
        )

        hl.addWidget(toggle)

        self.apps_list_layout.addWidget(item)

    def _on_toggle_launcher(self, launcher_name: str, checked: bool):
        if "launchers" not in self.config:
            self.config["launchers"] = {}

        if launcher_name in self.config["launchers"]:
            self.config["launchers"][launcher_name]["enabled"] = checked
            save_config(self.config)

    def toggle_all_switches(self, enable: bool):
        for i in range(self.apps_list_layout.count()):
            item = self.apps_list_layout.itemAt(i).widget()
            toggle = item.findChild(SwitchButton)
            if toggle:
                toggle.setEnabled(enable)

    def toggle_updating(self):
        if not self.is_updating:
            self.is_updating = True
            self.start_button.setText("Interrompi aggiornamenti")
            self.progress_label.setText("Aggiornamento in corso...")
            self.progress.setValue(0)

            # 🔁 Ricarica la configurazione aggiornata
            self.config = load_config()
            self.launchers = self.config.get("launchers", {})

            self.updater = Updater(self.launchers)
            self.updater.start()

            self.status_timer.start()
            self.toggle_all_switches(False)
        else:
            self.is_updating = False
            self.start_button.setText("Avvia sequenza aggiornamenti")
            self.progress_label.setText("Aggiornamento interrotto.")
            self.updater.stop()
            self.status_timer.stop()
            self.toggle_all_switches(True)

    def update_gui_from_updater(self):
        if not self.updater or not self.updater.current_status:
            return

        data = self.updater.current_status
        launcher = data["launcher"]
        net_sent = 0
        speed_recv = data["speed_recv"]
        #disk_read = data["disk_read"]
        #disk_write = data["disk_write"]
        inactive_for = data["inactive_for"]

        self.upload_speed_label.setText(f"{get_size(net_sent)}/s")
        self.download_speed_label.setText(f"{get_size(speed_recv)}/s")

        self.progress_label.setText(
            f"{launcher} attivo - inattivo da {inactive_for}s"
        )