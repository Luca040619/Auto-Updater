# gui/first_launch_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel,
    BodyLabel,
    CardWidget,
    PrimaryPushButton,
    StrongBodyLabel,
    SwitchButton,
    InfoBarPosition,
    InfoBar
)
from utils.eula import EULA  # Assicurati di avere un file EULA.py con il testo dell'EULA

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

        # Card per Termini e EULA
        self.terms_card = CardWidget()
        self.terms_card.setMaximumHeight(300)
        layout.addWidget(self.terms_card)

        terms_layout = QVBoxLayout(self.terms_card)
        terms_layout.setContentsMargins(24, 16, 24, 16)
        terms_layout.setSpacing(16)

        terms_layout.addWidget(StrongBodyLabel("Termini e condizioni"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        eula_text = BodyLabel(EULA)
        eula_text.setWordWrap(True)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(eula_text)
        container_layout.addStretch()
        scroll.setWidget(container)
        terms_layout.addWidget(scroll)

        # Switch accettazione EULA
        self.accept_switch = SwitchButton("Accetto i termini e condizioni")
        self.accept_switch.setOnText("Accetto i termini e condizioni")
        self.accept_switch.setOffText("Accetto i termini e condizioni")
        terms_layout.addWidget(self.accept_switch)

        self.launcher_card = CardWidget()
        self.launcher_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout.addWidget(self.launcher_card)
        launcher_layout = QVBoxLayout(self.launcher_card)
        launcher_layout.setContentsMargins(24, 16, 24, 16)
        launcher_layout.setSpacing(16)

        launcher_title = StrongBodyLabel("Launcher rilevati automaticamente")
        launcher_layout.addWidget(launcher_title)

        # Scroll area per lista launcher
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_widget = QWidget()
        self.launcher_list_layout = QVBoxLayout(scroll_widget)
        self.launcher_list_layout.setContentsMargins(0, 0, 0, 0)
        self.launcher_list_layout.setSpacing(14)
        scroll_area.setWidget(scroll_widget)

        launcher_layout.addWidget(scroll_area)

        # Launcher fittizi simulati
        launchers = [
            ("Steam", True),
            ("Epic Games", True),
            ("Battle.net", True),
            ("GOG Galaxy", False),
            ("Ubisoft Connect", False)
        ]

        for name, enabled in launchers:
            self.add_launcher_item(name, enabled)

        # Pulsante continua
        self.continue_btn = PrimaryPushButton("Continua")
        self.continue_btn.setEnabled(False)
        layout.addWidget(self.continue_btn)

        # Abilita il pulsante solo se accettano
        self.accept_switch.checkedChanged.connect(self.continue_btn.setEnabled)

        # Messaggio info bar se provano a cliccare senza accettare
        def try_continue():
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
        self.continue_btn.clicked.connect(try_continue)

    def add_launcher_item(self, name: str, enabled: bool):
        item = QFrame()
        item.setObjectName("launcherItem")
        item.setStyleSheet("QFrame#launcherItem { border-radius: 8px; }")

        hl = QHBoxLayout(item)
        hl.setContentsMargins(12, 6, 12, 6)
        hl.setSpacing(10)

        name_label = StrongBodyLabel(name)
        hl.addWidget(name_label)
        hl.addStretch()

        toggle = SwitchButton()
        toggle.setChecked(enabled)
        hl.addWidget(toggle)

        self.launcher_list_layout.addWidget(item)
