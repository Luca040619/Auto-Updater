from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt, QMargins
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QLegend
import random


class NetworkGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.download_data = [0.1] * 60
        self.upload_data = [0.05] * 60

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
        self.axis_y.setRange(0, 2.0)
        self.axis_y.setLabelFormat("%.1f")
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

        # Timer per aggiornamento
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def update_data(self):
        new_down = round(random.uniform(0.3, 1.8), 2)
        new_up = round(new_down * random.uniform(0.1, 0.4), 2)

        self.download_data.append(new_down)
        self.upload_data.append(new_up)
        self.download_data.pop(0)
        self.upload_data.pop(0)

        self.download_series.clear()
        self.upload_series.clear()

        for i in range(60):
            self.download_series.append(i, self.download_data[i])
            self.upload_series.append(i, self.upload_data[i])

        max_y = max(max(self.download_data), max(self.upload_data)) * 1.2
        self.axis_y.setRange(0, max(1.0, round(max_y, 1)))
