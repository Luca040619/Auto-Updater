from qfluentwidgets import (
    ProgressBar, TitleLabel, PrimaryPushButton,
    SwitchButton, StrongBodyLabel, CardWidget,
    FluentIcon, IconWidget, FluentIcon, IconWidget, CaptionLabel, Theme
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QScrollArea
from PyQt6.QtGui import QFont, QIcon
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
        self.launcher_widgets = {}

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

        icon_down = QIcon(FluentIcon.DOWNLOAD.path(Theme.AUTO))
        self.pixmap_down = icon_down.pixmap(12, 12)

        icon_sync = QIcon(FluentIcon.SYNC.path(Theme.AUTO))
        self.pixmap_sync = icon_sync.pixmap(12, 12)

        icon_done = QIcon(FluentIcon.COMPLETED.path(Theme.AUTO))
        self.pixmap_done = icon_done.pixmap(12, 12)

        self.pixmap_error = QIcon(FluentIcon.CANCEL.path(Theme.AUTO)).pixmap(12, 12)

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

        # Layout principale: orizzontale, per separare disco e rete
        net_info_layout = QHBoxLayout()
        net_info_layout.setSpacing(20)

        # Colonna sinistra: Disk Read/Write
        disk_info_layout = QVBoxLayout()
        disk_info_layout.setSpacing(4)

        # Disk Read
        read_layout = QHBoxLayout()
        read_layout.setSpacing(4)

        icon_read = QIcon(FluentIcon.BOOK_SHELF.path(Theme.AUTO))
        pixmap_read = icon_read.pixmap(9, 9)
        read_icon = QLabel()
        read_icon.setPixmap(pixmap_read)

        self.disk_read_speed_label = CaptionLabel("0 KB/s")
        read_layout.addWidget(read_icon)
        read_layout.addWidget(self.disk_read_speed_label)
        read_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        disk_info_layout.addLayout(read_layout)

        # Disk Write
        write_layout = QHBoxLayout()
        write_layout.setSpacing(4)

        icon_write = QIcon(FluentIcon.SAVE.path(Theme.AUTO))
        pixmap_write = icon_write.pixmap(9, 9)
        write_icon = QLabel()
        write_icon.setPixmap(pixmap_write)

        self.disk_write_speed_label = CaptionLabel("0 KB/s")
        write_layout.addWidget(write_icon)
        write_layout.addWidget(self.disk_write_speed_label)
        write_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        disk_info_layout.addLayout(write_layout)

        # Colonna destra: Upload/Download
        net_info_right_layout = QVBoxLayout()
        net_info_right_layout.setSpacing(4)

        # Upload
        upload_layout = QHBoxLayout()
        upload_layout.setSpacing(4)

        icon_up = QIcon(FluentIcon.UP.path(Theme.AUTO))
        pixmap_up = icon_up.pixmap(9, 9)
        upload_icon = QLabel()
        upload_icon.setPixmap(pixmap_up)

        self.upload_speed_label = CaptionLabel("0 KB/s")
        upload_layout.addWidget(upload_icon)
        upload_layout.addWidget(self.upload_speed_label)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_info_right_layout.addLayout(upload_layout)

        # Download
        download_layout = QHBoxLayout()
        download_layout.setSpacing(4)

        icon_down = QIcon(FluentIcon.DOWN.path(Theme.AUTO))
        pixmap_down = icon_down.pixmap(9, 9)
        download_icon = QLabel()
        download_icon.setPixmap(pixmap_down)

        self.download_speed_label = CaptionLabel("0 KB/s")
        download_layout.addWidget(download_icon)
        download_layout.addWidget(self.download_speed_label)
        download_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        net_info_right_layout.addLayout(download_layout)

        # Aggiungi entrambe le colonne al layout principale
        net_info_layout.addLayout(disk_info_layout)
        net_info_layout.addLayout(net_info_right_layout)

        # Aggiungi infine al layout superiore
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

        # --- Scaricato e stato ---
        info_layout = QHBoxLayout()
        info_layout.setSpacing(6)

        status_icon = QLabel()
        status_icon.hide()
        status_text = QLabel("Aggiornamento in corso...")
        status_text.hide()

        status_layout = QHBoxLayout()
        status_layout.setSpacing(4)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)

        # --- Layout download (a destra) ---
        download_icon = QLabel()
        download_icon.hide()
        download_text = QLabel()
        download_text.hide()

        download_layout = QHBoxLayout()
        download_layout.setSpacing(4)
        download_layout.addWidget(download_icon)
        download_layout.addWidget(download_text)
        download_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        hl.addLayout(status_layout)
        hl.addStretch()
        hl.addLayout(download_layout)

        # --- Toggle ---
        toggle = SwitchButton()
        toggle.setChecked(active)
        toggle.checkedChanged.connect(
            lambda checked, launcher=name: self._on_toggle_launcher(launcher, checked)
        )
        hl.addWidget(toggle)

        self.apps_list_layout.addWidget(item)

        # Salva riferimenti per aggiornamento live
        self.launcher_widgets[name] = {
            "status_icon": status_icon,
            "status_text": status_text,
            "download_icon": download_icon,
            "download_text": download_text,
        }

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
            self.updater.on_complete = self.on_update_complete
            self.updater.start()

            self.status_timer.start()
            self.toggle_all_switches(False)
        else:
            self.updater.cancelled = True
            self.updater.mark_cancelled_launchers()
            self.is_updating = False

            self.updater.stop()
            self.update_gui_from_updater()
            self.status_timer.stop()

            self.toggle_all_switches(True)
            self.reset_speed_indicators()
            self.start_button.setText("Avvia sequenza aggiornamenti")
            self.progress_label.setText("Aggiornamenti interrotti.")

    def update_gui_from_updater(self):
        if not self.updater or not self.updater.current_status:
            return

        data = self.updater.current_status
        launcher = data["launcher"]
        net_sent = 0
        speed_recv = data["speed_recv"]
        speed_read = data.get("speed_read", 0)
        speed_write = data.get("speed_write", 0)
        inactive_for = data["inactive_for"]

        if self.is_updating:
            self.upload_speed_label.setText(f"{get_size(net_sent)}/s")
            self.download_speed_label.setText(f"{get_size(speed_recv)}/s")
            self.disk_read_speed_label.setText(f"{get_size(speed_read)}/s")
            self.disk_write_speed_label.setText(f"{get_size(speed_write)}/s")

            self.progress_label.setText(
                f"{launcher} attivo - inattivo da {inactive_for}s"
            )

        # 🔁 Aggiorna anche ogni launcher
        for name, status_data in self.updater.launcher_status.items():
            if name not in self.launcher_widgets:
                continue

            bytes_downloaded = status_data.get("download", 0.0)
            status = status_data.get("status", "not_active")

            widget = self.launcher_widgets[name]
            print(status)

            # --- Stato aggiornamento (sinistra) ---
            if status == "in_progress":
                widget["status_icon"].setPixmap(self.pixmap_sync)
                widget["status_text"].setText("Aggiornamento in corso...")
                widget["status_icon"].show()
                widget["status_text"].show()

            elif status == "done":
                widget["status_icon"].setPixmap(self.pixmap_done)
                widget["status_text"].setText("Completato")
                widget["status_icon"].show()
                widget["status_text"].show()

            elif status == "cancelled":
                widget["status_icon"].setPixmap(self.pixmap_error)
                widget["status_text"].setText("Interrotto")
                widget["status_icon"].show()
                widget["status_text"].show()

            else:
                widget["status_icon"].hide()
                widget["status_text"].hide()

            # --- Download (destra) ---
            if status in ("in_progress", "done") and bytes_downloaded > 0:
                widget["download_icon"].setPixmap(self.pixmap_down)
                widget["download_icon"].show()
                widget["download_text"].setText(get_size(bytes_downloaded))
                widget["download_text"].show()
            else:
                widget["download_icon"].hide()
                widget["download_text"].hide()

    def reset_speed_indicators(self):
        self.upload_speed_label.setText("0 KB/s")
        self.download_speed_label.setText("0 KB/s")
        self.disk_read_speed_label.setText("0 KB/s")
        self.disk_write_speed_label.setText("0 KB/s")

    def on_update_complete(self):
        self.is_updating = False
        self.start_button.setText("Avvia sequenza aggiornamenti")
        self.progress_label.setText("Aggiornamenti completati.")
        self.toggle_all_switches(True)
        self.reset_speed_indicators()
        QTimer.singleShot(100, self.update_gui_from_updater)
        QTimer.singleShot(100, self.status_timer.stop)
        