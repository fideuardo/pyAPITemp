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

        # Optimización: Solo ajustar los ejes si es necesario
        # El eje X se puede desplazar automáticamente
        if self._series.count() > self._max_samples:
            # Si se eliminó un punto, el rango del eje X debe actualizarse
            points = self._series.pointsVector()
            if points:
                self._axis_x.setRange(points[0].x(), current_time)
        else:
            # Si solo se añaden puntos, basta con extender el máximo del eje X
            if current_time > self._axis_x.max():
                self._axis_x.setMax(current_time)

        # Ajustar el eje Y solo si el nuevo valor está fuera del rango actual
        if temp < self._axis_y.min() or temp > self._axis_y.max():
            temps = [p.y() for p in self._series.pointsVector()]
            self._axis_y.setRange(min(temps) - 1, max(temps) + 1)

    def clear_data(self):
        """Limpia todos los datos del gráfico."""
        self._series.clear()
        self._start_time = time.time()
        self._axis_x.setRange(0, 10)
        self._axis_y.setRange(20, 30)