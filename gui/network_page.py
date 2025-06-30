from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QLabel
from qfluentwidgets import TitleLabel, CardWidget, PrimaryPushButton, FluentIcon, Theme
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QCloseEvent
from gui.network_graph import NetworkGraph
from core.network import NetUsageMonitor, NetUsagePerProcess
from utils.functions import get_size, get_icon_from_exe
from scapy.all import AsyncSniffer
from threading import Thread
import psutil

class NetworkPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("network")
        self.net_monitor: NetUsageMonitor = NetUsageMonitor()
        self.process_monitor: NetUsagePerProcess = NetUsagePerProcess()

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Processo", "PID", "Download Speed", "Upload Speed", "Totale Download", "Totale Upload"])
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

        self.conn_thread = Thread(target=self.process_monitor.get_connections, daemon=True)
        self.conn_thread.start()

        # Sniffer async
        self.sniffer = AsyncSniffer(prn=self.process_monitor.process_packet, store=False)
        self.sniffer.start()

        self.net_timer = QTimer(self)
        self.net_timer.timeout.connect(self.update_global_net_stats)
        self.net_timer.start(1000)

        self.proc_timer = QTimer(self)
        self.proc_timer.timeout.connect(self.update_process_table)
        self.proc_timer.start(1000)

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

    def update_process_table(self):
        self.process_monitor.print_pid2traffic()
        df = self.process_monitor.global_df
        if df is None or df.empty:
            return

        self.table.setRowCount(len(df))
        for row, (pid, proc) in enumerate(df.iterrows()):
            raw_name = proc.get("name", "Unknown")
            if len(raw_name) > 28:
                name = raw_name[:25] + ".exe"
            else:
                name = raw_name
            exe_path = proc.get("exe", "")  # ← Assicurati che questo campo esista
            icon = get_icon_from_exe(exe_path) if exe_path else QIcon()

            total_download = get_size(proc.get("Download", 0))
            total_upload = get_size(proc.get("Upload", 0))
            download_speed = get_size(proc.get("Download Speed", 0)) + "/s"
            upload_speed = get_size(proc.get("Upload Speed", 0)) + "/s"

            self.table.setItem(row, 0, QTableWidgetItem(icon, name))
            self.table.setItem(row, 1, QTableWidgetItem(str(pid)))
            self.table.setItem(row, 2, QTableWidgetItem(download_speed))
            self.table.setItem(row, 3, QTableWidgetItem(upload_speed))
            self.table.setItem(row, 4, QTableWidgetItem(total_download))
            self.table.setItem(row, 5, QTableWidgetItem(total_upload))

    def closeEvent(self, event: QCloseEvent):
        self.sniffer.stop()
        self.process_monitor.is_monitoring = False
        event.accept()