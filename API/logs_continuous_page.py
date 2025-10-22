from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Slot
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter
import time


class LogsContinuousPage(QWidget):
    """Vista para mostrar un gráfico de datos continuos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._series = QLineSeries()
        self._series.setName("Temperature")

        chart = QChart()
        chart.addSeries(self._series)
        chart.setTitle("Live Temperature Data")
        chart.setTheme(QChart.ChartThemeDark)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        self._axis_x = QValueAxis()
        self._axis_x.setLabelFormat("%.1f s")
        self._axis_x.setTitleText("Time (s)")
        chart.addAxis(self._axis_x, Qt.AlignBottom)
        self._series.attachAxis(self._axis_x)

        self._axis_y = QValueAxis()
        self._axis_y.setLabelFormat("%.2f °C")
        self._axis_y.setTitleText("Temperature (°C)")
        chart.addAxis(self._axis_y, Qt.AlignLeft)
        self._series.attachAxis(self._axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        layout = QVBoxLayout(self)
        layout.addWidget(chart_view)

        self._start_time = time.time()
        self._max_samples = 100  # Número máximo de puntos a mostrar

    @Slot(dict)
    def add_sample(self, sample: dict):
        """Añade una nueva muestra al gráfico."""
        current_time = time.time() - self._start_time
        temp = sample.get("temp_mC", 0) / 1000.0

        if self._series.count() > self._max_samples:
            self._series.remove(0)

        self._series.append(current_time, temp)

        points = self._series.pointsVector()
        if points:
            min_x = points[0].x()
            max_x = points[-1].x()
            self._axis_x.setRange(min_x, max_x)

            temps = [p.y() for p in points]
            min_y = min(temps)
            max_y = max(temps)
            self._axis_y.setRange(min_y - 1, max_y + 1)

    def clear_data(self):
        """Limpia todos los datos del gráfico."""
        self._series.clear()
        self._start_time = time.time()
        self._axis_x.setRange(0, 10)
        self._axis_y.setRange(20, 30)