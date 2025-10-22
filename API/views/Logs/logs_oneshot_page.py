from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QCheckBox,
    QLineEdit,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Slot, Signal, QPointF
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter
from pathlib import Path
from collections import deque


class LogsOneShotPage(QWidget):
    """Página con un botón para solicitar una lectura en modo One-Shot."""
    read_now_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples = deque(maxlen=10)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        header_panel = self._create_header_panel()
        layout.addWidget(header_panel)

        # Data Main Layout principal
        data_layout = QHBoxLayout()
        layout.addLayout(data_layout)

        # --- Samples Register---
        self._sample_panel = self._create_sample_panel()
        data_layout.addWidget(self._sample_panel, 1) #first secttion panel

        # --- Samples Graphic ---
        self._graph_panel = self._create_graph_panel()
        data_layout.addWidget(self._graph_panel, 3)

        self._read_now_button.clicked.connect(self.read_now)
        self._sample_toggle.toggled.connect(self._on_sample_toggle_changed)

    def _create_header_panel(self) -> QWidget:

        """Crea el panel superior que contiene el título, modo y botón de control."""
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 10) # Margen inferior

        title = QLabel("Logging Control")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)

        # Botón de lectura (centro)
        self._read_now_button = QPushButton("Read Now")
        self._read_now_button.setStyleSheet("""
            QPushButton {
                background-color: #5a9bde; color: white; border: none;
                padding: 8px 16px; font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #6aa7e8; }
            QPushButton:pressed { background-color: #4a8ac8; }
        """)

        # Interruptor para las muestras
        self._sample_toggle = QCheckBox("Samples")
        self._sample_toggle.setStyleSheet("font-size: 14px;")

        # Etiqueta de modo (derecha)
        mode_label = QLabel("Mode: <b>One-Shot</b>")
        mode_label.setStyleSheet("font-size: 16px; font-style: italic;")
        
        controls_layout = QHBoxLayout()

        # Añadir widgets al layout
        controls_layout.addWidget(mode_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._read_now_button, alignment=Qt.AlignCenter | Qt.AlignVCenter)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._sample_toggle, alignment=Qt.AlignRight | Qt.AlignVCenter)

        # --- Controles para guardar archivo ---
        file_controls_layout = QHBoxLayout()
        path_label = QLabel("Save Path:")
        self._path_line_edit = QLineEdit()
        self._path_line_edit.setPlaceholderText("Select a file to save results...")
        self._path_line_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")

        file_controls_layout.addWidget(path_label)
        file_controls_layout.addWidget(self._path_line_edit)
        file_controls_layout.addWidget(browse_button)
        
        panel_layout.addWidget(title)
        panel_layout.addLayout(controls_layout)
        panel_layout.addLayout(file_controls_layout)

        browse_button.clicked.connect(self._on_browse_clicked)
        return panel

    def _create_sample_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 10, 10, 0)
        title = QLabel("Last 10 Readings")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        self._history_list = QListWidget()
        layout.addWidget(title)
        layout.addWidget(self._history_list)
        return panel

    def _create_graph_panel(self) -> QWidget:
        self._series = QLineSeries()
        chart = QChart()
        chart.addSeries(self._series)
        chart.setTitle("Readings History")
        chart.setTheme(QChart.ChartThemeDark)
        chart.legend().hide()

        self._axis_x = QValueAxis()
        self._axis_x.setLabelFormat("%d")
        self._axis_x.setTitleText("Sample #")
        chart.addAxis(self._axis_x, Qt.AlignBottom)
        self._series.attachAxis(self._axis_x)

        self._axis_y = QValueAxis()
        self._axis_y.setLabelFormat("%.2f °C")
        self._axis_y.setTitleText("Temperature (°C)")
        chart.addAxis(self._axis_y, Qt.AlignLeft)
        self._series.attachAxis(self._axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view

    def read_now(self):
        """Se ejecuta al presionar el botón 'Read Now'."""
        print("Iniciando lectura en modo One-Shot")
        self._read_now_button.setEnabled(False)
        self.read_now_requested.emit()

    @Slot(dict)
    def display_sample(self, sample: dict):
        """Muestra la temperatura de la muestra recibida."""
        if sample and "temp_mC" in sample:
            self._samples.append(sample)
            self._update_ui()

        self._read_now_button.setEnabled(True)

    def _update_ui(self):
        """Actualiza la lista de historial y el gráfico con los datos actuales."""
        # Actualizar lista
        self._history_list.clear()
        for i, sample in enumerate(reversed(self._samples)):
            temp_c = sample.get("temp_mC", 0) / 1000.0
            self._history_list.insertItem(0, f"#{len(self._samples) - i}: {temp_c:.3f} °C")

        # Actualizar gráfico
        points = [ (i, s.get("temp_mC", 0) / 1000.0) for i, s in enumerate(self._samples) ]
        self._series.replace([QPointF(p[0], p[1]) for p in points])

        # Ajustar ejes
        if points:
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            self._axis_x.setRange(0, max(9, len(points) - 1))
            self._axis_y.setRange(min_y - 0.5, max_y + 0.5)

    def _on_browse_clicked(self):
        """Abre un diálogo para seleccionar una ruta de archivo donde guardar."""
        # Abre un diálogo para guardar, sugiriendo un nombre de archivo y tipo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Samples As",
            str(Path.home() / "samples.csv"),  # Directorio y nombre de archivo por defecto
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self._path_line_edit.setText(file_path)

    def _on_sample_toggle_changed(self, checked: bool):
        """Muestra un pop-up para alertar sobre la activación/desactivación del guardado."""
        file_path = self._path_line_edit.text()
        if checked:
            if not file_path:
                QMessageBox.warning(self, "No File Selected", "Please select a file path before enabling storage.")
                self._sample_toggle.setChecked(False)  # Revertir el cambio
                return
            message = f"Samples will be stored in:\n{file_path}"
        else:
            message = "Sample storage is now OFF."
        QMessageBox.information(self, "Sample Storage", message)