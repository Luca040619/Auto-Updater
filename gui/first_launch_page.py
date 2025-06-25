from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QFrame, QSizePolicy, QStackedLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from qfluentwidgets import (
    TitleLabel, BodyLabel, CardWidget, PrimaryPushButton, StrongBodyLabel,
    SwitchButton, InfoBarPosition, InfoBar, FluentIcon, Theme
)
from utils.eula import EULA
from utils.launchers import KNOWN_LAUNCHERS
from utils.functions import search_default_programs, get_icon_from_exe, get_config_path
import json

class FirstLaunchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("firstLaunch")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Titolo
        title = TitleLabel("Benvenuto in Auto Updater")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        title.setStyleSheet("margin: 0px; padding: 0px;")
        layout.addWidget(title)

        # Layout a pagine
        self.stack = QStackedLayout()
        layout.addLayout(self.stack)

        self.eula_page = self.create_eula_page()
        self.launcher_page = self.create_launcher_page()

        self.stack.addWidget(self.eula_page)
        self.stack.addWidget(self.launcher_page)

        # Pulsanti di navigazione
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self.back_btn = PrimaryPushButton("Indietro")
        self.back_btn.setVisible(False)
        self.back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_layout.addStretch()

        self.next_btn = PrimaryPushButton("Avanti")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.go_next)
        btn_layout.addWidget(self.next_btn)

        self.continue_btn = PrimaryPushButton("Fine")
        self.continue_btn.setVisible(False)
        self.continue_btn.setEnabled(True)  # ormai ha già accettato
        self.continue_btn.clicked.connect(self.try_continue)
        btn_layout.addWidget(self.continue_btn)

        layout.addLayout(btn_layout)

        # Abilita "Avanti" solo se accetta
        self.accept_switch.checkedChanged.connect(self.next_btn.setEnabled)

    def create_eula_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        card = CardWidget()
        card.setMaximumHeight(600)
        layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 16, 24, 16)
        card_layout.setSpacing(16)

        card_layout.addWidget(StrongBodyLabel("Termini e condizioni"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        eula_text = BodyLabel(EULA)
        eula_text.setWordWrap(True)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(eula_text)
        container_layout.addStretch()
        scroll.setWidget(container)

        card_layout.addWidget(scroll)

        self.accept_switch = SwitchButton("Ho letto e accetto i termini e condizioni")
        self.accept_switch.setOnText("Ho letto e accetto i termini e condizioni")
        self.accept_switch.setOffText("Ho letto e accetto i termini e condizioni")
        card_layout.addWidget(self.accept_switch)

        return page

    def create_launcher_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)  # aggiunta per separare bene le card

        # 🟦 Descrizione user-friendly dell'app
        info_card = CardWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 16, 24, 16)
        info_layout.setSpacing(8)

        info_label = BodyLabel(
            "Auto Updater ti aiuta ad aggiornare automaticamente i giochi dei tuoi launcher preferiti, "
            "monitorando l'attività della rete e del disco per capire quando l'attività è conclusa. "
            "Puoi persino impostare lo spegnimento automatico del PC al termine degli aggiornamenti!"
        )
        info_label.setWordWrap(True)

        info_layout.addWidget(info_label)
        layout.addWidget(info_card)

        self.launcher_card = CardWidget()
        self.launcher_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout.addWidget(self.launcher_card)

        launcher_layout = QVBoxLayout(self.launcher_card)
        launcher_layout.setContentsMargins(24, 16, 24, 16)
        launcher_layout.setSpacing(16)

        launcher_layout.addWidget(StrongBodyLabel("Aggiorna automaticamente i giochi su questi launcher:"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_widget = QWidget()
        self.launcher_list_layout = QVBoxLayout(scroll_widget)
        self.launcher_list_layout.setContentsMargins(0, 0, 0, 0)
        self.launcher_list_layout.setSpacing(14)

        scroll_area.setWidget(scroll_widget)
        launcher_layout.addWidget(scroll_area)

        self.found_launchers = search_default_programs()
        for name in KNOWN_LAUNCHERS:
            if name in self.found_launchers:
                self.add_launcher_item(name, True, self.found_launchers[name])

        warning_card = CardWidget()
        warning_layout = QHBoxLayout(warning_card)
        warning_layout.setContentsMargins(24, 16, 24, 16)
        warning_layout.setSpacing(20)
        warning_card.setMaximumHeight(60)

        # Icona warning (workaround ufficiale)
        icon_warning = QIcon(FluentIcon.HELP.path(Theme.DARK))
        pixmap_warning = icon_warning.pixmap(25, 25)

        warning_icon = QLabel()
        warning_icon.setPixmap(pixmap_warning)
        warning_icon.setMaximumWidth(25)

        # Nuovo: contenitore per il testo
        text_container = QVBoxLayout()
        text_container.setContentsMargins(0, 0, 0, 0)
        text_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        warning_text = BodyLabel(
            "Assicurati che gli aggiornamenti automatici dei giochi siano attivi nelle impostazioni dei launcher"
        )
        warning_text.setWordWrap(True)

        text_container.addWidget(warning_text)

        # Aggiungi tutto al layout principale
        warning_layout.addWidget(warning_icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        warning_layout.addLayout(text_container)

        layout.addWidget(warning_card)

        return page

    def add_launcher_item(self, name: str, enabled: bool, icon_path: str | None = None):
        item = QFrame()
        item.setObjectName("launcherItem")
        item.setStyleSheet("QFrame#launcherItem { border-radius: 8px; }")

        hl = QHBoxLayout(item)
        hl.setContentsMargins(12, 6, 12, 6)
        hl.setSpacing(10)

        # Icona se disponibile
        if icon_path:
            icon = get_icon_from_exe(icon_path)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(24, 24))
            hl.addWidget(icon_label)

        name_label = StrongBodyLabel(name)
        hl.addWidget(name_label)
        hl.addStretch()

        toggle = SwitchButton()
        toggle.setChecked(enabled)
        hl.addWidget(toggle)

        self.launcher_list_layout.addWidget(item)

    def go_next(self):
        self.stack.setCurrentIndex(1)
        self.back_btn.setVisible(True)
        self.continue_btn.setVisible(True)
        self.next_btn.setVisible(False)

    def go_back(self):
        self.stack.setCurrentIndex(0)
        self.back_btn.setVisible(False)
        self.continue_btn.setVisible(False)
        self.next_btn.setVisible(True)

    def try_continue(self):
        if not self.accept_switch.isChecked():
            InfoBar.error(
                title="Termini non accettati",
                content="Devi accettare i termini per continuare.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )
        
        self.save_launcher_config()

    def save_launcher_config(self):
        config = {"launchers": {}}

        for i in range(self.launcher_list_layout.count()):
            item = self.launcher_list_layout.itemAt(i).widget()
            name_label = item.findChild(StrongBodyLabel)
            toggle = item.findChild(SwitchButton)

            name = name_label.text()
            enabled = toggle.isChecked()
            path = self.found_launchers.get(name, "")

            config["launchers"][name] = {
                "path": path,
                "enabled": enabled
            }

        config_path = get_config_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
