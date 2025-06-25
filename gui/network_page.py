from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QLabel
from qfluentwidgets import TitleLabel, CardWidget, PrimaryPushButton, FluentIcon, Theme
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from gui.network_graph import NetworkGraph
from core.network import NetUsageMonitor
from utils.functions import get_size
import psutil

class NetworkPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("network")
        self.net_monitor: NetUsageMonitor = NetUsageMonitor()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(24)

        # Titolo
        self.title = TitleLabel("Monitor di rete")
        self.main_layout.addWidget(self.title)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(32)

        # Download corrente
        self.dl_speed_label = self._create_stat_widget("Download", FluentIcon.DOWN, "0 KB/s")

        # Upload corrente
        self.ul_speed_label = self._create_stat_widget("Upload", FluentIcon.UP, "0 KB/s")

        # Totale scaricato
        self.total_dl_label = self._create_stat_widget("Totale Download", FluentIcon.CLOUD_DOWNLOAD, "0 MB")

        # Totale inviato
        self.total_ul_label = self._create_stat_widget("Totale Upload", FluentIcon.SEND, "0 MB")

        stats_layout.addWidget(self.dl_speed_label)
        stats_layout.addWidget(self.ul_speed_label)
        stats_layout.addWidget(self.total_dl_label)
        stats_layout.addWidget(self.total_ul_label)

        self.main_layout.addLayout(stats_layout)

        # Card contenente grafico e tabella
        self.network_card = CardWidget()
        self.main_layout.addWidget(self.network_card)

        card_layout = QVBoxLayout(self.network_card)
        card_layout.setContentsMargins(24, 16, 24, 16)
        card_layout.setSpacing(24)

        self.graph = NetworkGraph(self.net_monitor)
        self.graph.setFixedHeight(175)
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

        self.net_timer = QTimer(self)
        self.net_timer.timeout.connect(self.update_global_net_stats)
        self.net_timer.start(1000)

        # Dati finti per ora
        self.load_mock_data()

    def _create_stat_widget(self, label_text, icon_type, value_text) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setStyleSheet("font-size: 11px;")

        icon = QIcon(FluentIcon(icon_type).path(Theme.AUTO))
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(12, 12))

        value = QLabel(value_text)
        value.setStyleSheet("font-weight: bold; font-size: 14px;")

        h_layout = QHBoxLayout()
        h_layout.addWidget(icon_label)
        h_layout.addWidget(value)
        h_layout.setSpacing(4)
        h_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(h_layout)

        # 👉 Ritorna solo il contenitore principale ma salviamo accesso al QLabel interno
        widget.value_label = value
        return widget
    
    def update_global_net_stats(self):
        net = self.net_monitor.active_interface
        io = psutil.net_io_counters(pernic=True, nowrap=True)
        bytes_in, bytes_out = self.net_monitor.get_net_speed()

        self.graph.append_data_point(bytes_in, bytes_out)

        # Totale ricevuti/inviati in assoluto
        self.total_dl_label.value_label.setText(get_size(io[net].bytes_recv))
        self.total_ul_label.value_label.setText(get_size(io[net].bytes_sent))

        # Velocità di download/upload attuale
        self.dl_speed_label.value_label.setText(f"{get_size(bytes_in)}/s")
        self.ul_speed_label.value_label.setText(f"{get_size(bytes_out)}/s")

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
