from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QFormLayout,
    QLabel,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter, QColor
import time


class OneShotView(QWidget):
    """Vista para mostrar una única muestra de datos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("One-Shot Sample")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self._form_layout = QFormLayout()
        self._form_layout.setContentsMargins(15, 0, 0, 0)
        self._form_layout.setLabelAlignment(Qt.AlignLeft)
        self._form_layout.setFormAlignment(Qt.AlignLeft)
        layout.addLayout(self._form_layout)

        self._timestamp_label = QLabel("N/A")
        self._temp_label = QLabel("N/A")
        self._flags_label = QLabel("N/A")

        self._form_layout.addRow("Timestamp:", self._timestamp_label)
        self._form_layout.addRow("Temperature:", self._temp_label)
        self._form_layout.addRow("Flags:", self._flags_label)

    @Slot(dict)
    def update_data(self, sample: dict):
        """Actualiza los campos con los datos de una nueva muestra."""
        if not sample:
            self._timestamp_label.setText("N/A")
            self._temp_label.setText("N/A")
            self._flags_label.setText("N/A")
            return

        ts = sample.get("timestamp_ns", 0) / 1e9
        temp = sample.get("temp_mC", 0) / 1000.0
        flags = sample.get("flags", 0)

        self._timestamp_label.setText(f"{ts:.3f} s")
        self._temp_label.setText(f"{temp:.3f} °C")
        self._flags_label.setText(f"0x{flags:04X}")


class ContinuousView(QWidget):
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

        # Mantiene un número máximo de puntos en el gráfico
        if self._series.count() > self._max_samples:
            self._series.remove(0)

        self._series.append(current_time, temp)

        # Ajusta los ejes dinámicamente
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
        self._axis_x.setRange(0, 10) # Rango inicial
        self._axis_y.setRange(20, 30) # Rango inicial


class LogsPage(QWidget):
    """Página que contiene y gestiona las vistas de datos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogsPage")
        self.setStyleSheet("background-color: #3a404a; color: white;")

        self._stack = QStackedWidget(self)
        self._one_shot_view = OneShotView()
        self._continuous_view = ContinuousView()

        self._stack.addWidget(self._one_shot_view)
        self._stack.addWidget(self._continuous_view)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._stack)

    @Slot(str)
    def set_operation_mode(self, mode: str):
        """Cambia la vista activa según el modo de operación."""
        if mode == "one-shot":
            self._stack.setCurrentWidget(self._one_shot_view)
        elif mode == "continuous":
            self._continuous_view.clear_data() # Limpia el gráfico al cambiar a modo continuo
            self._stack.setCurrentWidget(self._continuous_view)

    @Slot(dict)
    def update_data(self, sample: dict):
        """Envía los datos a la vista apropiada."""
        # Ambas vistas tienen un slot para recibir datos, así que podemos conectarnos a ambas.
        # O podemos dirigirlo explícitamente.
        self._one_shot_view.update_data(sample)
        self._continuous_view.add_sample(sample)