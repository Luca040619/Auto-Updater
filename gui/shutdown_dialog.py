from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDialog
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    Dialog, SwitchButton, StrongBodyLabel, BodyLabel,
    PrimaryPushButton, PushButton, FluentIcon, IconWidget, CardWidget
)


class ShutdownSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(
            parent=parent
        )
        self.setWindowTitle("Spegnimento automatico")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(520, 440)
        self.setFixedSize(self.size())
        self._init_ui()

    def _init_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)

        header_card = CardWidget()
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(16)

        # Icona a sinistra
        icon = IconWidget(FluentIcon.HISTORY, parent=self)
        icon.setFixedSize(36, 36)

        # Testo descrittivo a destra
        desc_container = QWidget()
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(4)

        desc_title = StrongBodyLabel("Spegnimento automatico")
        desc_body = BodyLabel("Il PC verrà spento automaticamente quando non verrà rilevata attività di rete o disco secondo i criteri selezionati.")
        desc_body.setWordWrap(True)

        desc_layout.addWidget(desc_title)
        desc_layout.addWidget(desc_body)

        # Aggiungi al layout
        header_layout.addWidget(icon)
        header_layout.addWidget(desc_container, 1)

        # Aggiungi la card all’interfaccia
        layout.addWidget(header_card)

        layout.addSpacing(12)

        def create_switch_row(icon_enum, title: str, description: str):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)
            row_layout.setSpacing(12)

            icon_widget = IconWidget(icon_enum)
            icon_widget.setFixedSize(20, 20)
            row_layout.addWidget(icon_widget)

            label_container = QWidget()
            label_layout = QVBoxLayout(label_container)
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(2)
            label_layout.addWidget(StrongBodyLabel(title))
            label_layout.addWidget(BodyLabel(description))

            row_layout.addWidget(label_container, 1)

            switch = SwitchButton()
            switch.setOnText("")
            switch.setOffText("")
            row_layout.addWidget(switch)

            layout.addWidget(row)
            return switch

        self.download_switch = create_switch_row(
            FluentIcon.DOWN, "Monitor download", "Controlla se ci sono dati in entrata (es. streaming, aggiornamenti)"
        )
        self.upload_switch = create_switch_row(
            FluentIcon.UP, "Monitor upload", "Controlla se ci sono dati in uscita (es. backup, invio file)"
        )
        self.read_switch = create_switch_row(
            FluentIcon.SAVE, "Monitor lettura disco", "Controlla se ci sono letture da disco in corso"
        )
        self.write_switch = create_switch_row(
            FluentIcon.SAVE_AS, "Monitor scrittura disco", "Controlla se ci sono scritture su disco in corso"
        )

        for sw in (
            self.download_switch,
            self.upload_switch,
            self.read_switch,
            self.write_switch
        ):
            sw.checkedChanged.connect(self._update_confirm_button_state)

        # Pulsanti in basso
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.addStretch()

        self.cancel_button = PushButton("Annulla")
        self.cancel_button.clicked.connect(self.reject)

        self.confirm_button = PrimaryPushButton("Conferma")
        self.confirm_button.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.confirm_button)
        layout.addWidget(button_row)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self._update_confirm_button_state()
        
        main_layout.addWidget(content)

    def _update_confirm_button_state(self):
        is_any_checked = (
            self.download_switch.isChecked() or
            self.upload_switch.isChecked() or
            self.read_switch.isChecked() or
            self.write_switch.isChecked()
        )
        self.confirm_button.setEnabled(is_any_checked)

    def get_config(self):
        return {
            "monitor_download": self.download_switch.isChecked(),
            "monitor_upload": self.upload_switch.isChecked(),
            "monitor_disk_read": self.read_switch.isChecked(),
            "monitor_disk_write": self.write_switch.isChecked(),
        }
