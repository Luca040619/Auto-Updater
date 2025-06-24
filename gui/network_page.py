from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem
from qfluentwidgets import TitleLabel, CardWidget, PrimaryPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from gui.network_graph import NetworkGraph


class NetworkPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("network")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(24)

        # Titolo
        self.title = TitleLabel("Monitor di rete")
        self.main_layout.addWidget(self.title)

        # Card contenente grafico e tabella
        self.network_card = CardWidget()
        self.main_layout.addWidget(self.network_card)

        card_layout = QVBoxLayout(self.network_card)
        card_layout.setContentsMargins(24, 16, 24, 16)
        card_layout.setSpacing(24)

        self.graph = NetworkGraph()
        self.graph.setFixedHeight(160)
        card_layout.addWidget(self.graph)

        # Tabella dei processi
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Processo", "PID", "Download", "Upload"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("QTableWidget { background-color: transparent; }")
        card_layout.addWidget(self.table)

        # Pulsante Termina (in basso a destra)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.end_button = PrimaryPushButton("Termina")
        btn_layout.addWidget(self.end_button)
        card_layout.addLayout(btn_layout)

        # Dati finti per ora
        self.load_mock_data()

    def load_mock_data(self):
        data = [
            ("chrome.exe", "4284", "1,53 MB/s", "25,6 KB/s", "assets/icons/chrome.png"),
            ("Steam", "7016", "476 KB/s", "6,9 KB/s", "assets/icons/steam.png"),
            ("Epic Games.exe", "1216", "218 KB/s", "0,8 KB/s", "assets/icons/epic_games.png"),
            ("svchost.exe", "940", "142 KB/s", "3,4 KB/s", "assets/icons/exec.png"),
        ]
        self.table.setRowCount(len(data))
        for row, (proc, pid, down, up, icon_path) in enumerate(data):
            icon_item = QTableWidgetItem(QIcon(QPixmap(icon_path)), proc)
            self.table.setItem(row, 0, icon_item)
            self.table.setItem(row, 1, QTableWidgetItem(pid))
            self.table.setItem(row, 2, QTableWidgetItem(down))
            self.table.setItem(row, 3, QTableWidgetItem(up))
