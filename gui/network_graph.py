from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, QMargins
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QLegend
from core.network import NetUsageMonitor


class NetworkGraph(QWidget):
    def __init__(self, net_monitor: NetUsageMonitor, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.net_monitor = net_monitor

        self.download_data = [0] * 60
        self.upload_data = [0] * 60

        self.chart = QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.setBackgroundBrush(Qt.GlobalColor.transparent)
        self.chart.setPlotAreaBackgroundVisible(False)
        self.chart.setBackgroundRoundness(0)
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.setContentsMargins(0, 0, 0, 0)
        self.chart.setPlotAreaBackgroundVisible(False)

        # Serie
        self.download_series = QLineSeries()
        self.download_series.setName("Download")
        self.download_series.setColor(QColor("#29b6f6"))
        self.download_series.setPointsVisible(False)

        self.upload_series = QLineSeries()
        self.upload_series.setName("Upload")
        self.upload_series.setColor(QColor("#66bb6a"))
        self.upload_series.setPointsVisible(False)

        self.chart.addSeries(self.download_series)
        self.chart.addSeries(self.upload_series)

        # Assi
        self.axis_x = QValueAxis()
        self.axis_x.setRange(0, 59)
        self.axis_x.setVisible(False)
        self.axis_x.setGridLineVisible(False)

        self.axis_y = QValueAxis()
        self.axis_y.setLabelFormat("%.1f MB/s") 
        self.axis_y.setTickCount(5)
        font = self.axis_y.labelsFont()
        font.setPointSize(8)
        self.axis_y.setLabelsFont(font)
        self.axis_y.setLabelsColor(QColor("#aaa"))
        self.axis_y.setGridLineColor(QColor(255, 255, 255, 25))  # griglia molto leggera
        self.axis_y.setLineVisible(False)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.download_series.attachAxis(self.axis_x)
        self.download_series.attachAxis(self.axis_y)
        self.upload_series.attachAxis(self.axis_x)
        self.upload_series.attachAxis(self.axis_y)

        # Legenda
        legend = self.chart.legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignmentFlag.AlignBottom)
        legend.setLabelColor(QColor("#bbb"))

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setStyleSheet("""
            background: transparent;
            border-radius: 12px;
        """)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chart_view)

    def append_data_point(self, delta_in, delta_out):
        new_down = round(delta_in / 1024 / 1024, 2)
        new_up = round(delta_out / 1024 / 1024, 2)

        self.download_data.append(new_down)
        self.upload_data.append(new_up)
        self.download_data.pop(0)
        self.upload_data.pop(0)

        self.download_series.clear()
        self.upload_series.clear()

        for i in range(60):
            self.download_series.append(i, self.download_data[i])
            self.upload_series.append(i, self.upload_data[i])

        current_max = max(max(self.download_data), max(self.upload_data))

        # Scale comode (puoi raffinarle)
        def nice_scale(value):
            if value <= 0.5:
                return 0.5
            elif value <= 1:
                return 1
            elif value <= 2:
                return 2
            elif value <= 5:
                return 5
            elif value <= 10:
                return 10
            elif value <= 15:
                return 15
            elif value <= 20:
                return 20
            elif value <= 50:
                return 50
            elif value <= 100:
                return 100
            elif value <= 200:
                return 200
            elif value <= 500:
                return 500
            else:
                return ((value // 100) + 1) * 100

        # Fai decadere lentamente la scala
        if not hasattr(self, "_last_max_y"):
            self._last_max_y = current_max
        else:
            decay_factor = 0.05  # più basso = più lento
            self._last_max_y = max(current_max, self._last_max_y * (1 - decay_factor))

        # Applica la scala "bella"
        smoothed_max_y = nice_scale(self._last_max_y)
        self.axis_y.setRange(0, smoothed_max_y)
