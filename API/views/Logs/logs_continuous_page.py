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
    QComboBox,
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter, QIntValidator

from kernel.apitest.LxDrTemp import SIMTEMP_FLAG_THR_EDGE
from pathlib import Path
from collections import deque
from typing import Optional
import time


class LogsContinuousPage(QWidget):
    """View for displaying and controlling continuous data logging."""
    start_logging_requested = Signal(dict)
    stop_logging_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples = deque(maxlen=10)
        self._is_logging = False
        self._sampling_timer = QTimer(self)
        self._sampling_timer.setSingleShot(True)
        self._sampling_timer.timeout.connect(self.__expiredtime)
        self._indicator_off_color = "#2c313c"
        self._indicator_on_color = "#c62828"
        self._indicator_active: Optional[bool] = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        header_panel = self._create_header_panel()
        layout.addWidget(header_panel)

        # Main data layout
        data_layout = QHBoxLayout()
        layout.addLayout(data_layout)

        # --- Samples Register ---
        self._sample_panel = self._create_sample_panel()
        data_layout.addWidget(self._sample_panel, 1)

        # --- Samples Graphic ---
        self._series = QLineSeries()
        self._series.setName("Temperature")
        chart = QChart()
        chart.addSeries(self._series)
        chart.setTitle("Live Temperature Data")
        chart.setTheme(QChart.ChartThemeDark)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        self._graph_panel = QChartView(chart)
        self._graph_panel.setRenderHint(QPainter.Antialiasing)
        data_layout.addWidget(self._graph_panel, 3)

        self._setup_chart_axes(chart)

        self._stateButton.clicked.connect(self._on_state_button_clicked)
        self._sample_toggle.toggled.connect(self._on_sample_toggle_changed)

    def _create_header_panel(self) -> QWidget:
        """Creates the top panel containing the title, mode, and control buttons."""
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 10)

        # --- Title ---
        title = QLabel("Logging Control")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(title)

        # --- Main Controls Layout (Horizontal) ---
        main_controls_layout = QHBoxLayout()

        # --- Left Side: Mode and Use Case ---
        params_layout = QVBoxLayout()
        params_layout.setAlignment(Qt.AlignTop)

        mode_label = QLabel("Mode: <b>Continuous</b>")
        mode_label.setStyleSheet("font-size: 16px; font-style: italic;")


        # --- Init Settings Layout ---
        settings_layout = QHBoxLayout()
        
        # --- Period ---
        self._periodLabel = QLabel("Period [ms]:")
        self._period = QLineEdit("100")
        self._period.setValidator(QIntValidator(0, 5000, self)) # Range from 5 to 5000
        
        #--- Sampling Time ---
        self._samplingTimeLabel = QLabel("Sampling Time [ms]:")
        self._samplingTime = QLineEdit("1000") # Default value
        self._samplingTime.setValidator(QIntValidator(0, 100000, self)) # Range from 1 to 10000
        
        #--- simulation_mode
        self._simulationModeLabel = QLabel("Simulation Mode:")
        self._simulationMode = QComboBox()
        self._simulationMode.addItems(["normal",
                                       "noisy",
                                       "ramp",])
        #--- ThresHold ----
        self._thresholdLabel = QLabel("ThresHold [mC]:")
        self._threshold = QLineEdit("0") # Default value
        self._threshold.setValidator(QIntValidator(0, 100000, self)) # Range from 1 to 10000
        #---       Settings Layout   ---
        settings_layout.addWidget(self._periodLabel)
        settings_layout.addWidget(self._period)

        settings_layout.addWidget(self._samplingTimeLabel)
        settings_layout.addWidget(self._samplingTime)

        settings_layout.addWidget(self._simulationModeLabel)
        settings_layout.addWidget(self._simulationMode)
        settings_layout.addWidget(self._thresholdLabel)
        settings_layout.addWidget(self._threshold)

        params_layout.addWidget(mode_label)
        params_layout.addLayout(settings_layout)

        main_controls_layout.addLayout(params_layout)
        main_controls_layout.addStretch(1)

        panel_layout.addLayout(main_controls_layout)

        # --- File Saving Controls (Bottom) ---
        self._sample_toggle = QCheckBox("Save Samples")
        self._sample_toggle.setStyleSheet("font-size: 14px;")

        file_controls_layout = QHBoxLayout()
        self._path_line_edit = QLineEdit()
        self._path_line_edit.setPlaceholderText("Select a file to save results...")
        self._path_line_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")

        file_controls_layout.addWidget(self._sample_toggle)
        file_controls_layout.addWidget(QLabel("Save Path:"))
        file_controls_layout.addWidget(self._path_line_edit)
        file_controls_layout.addWidget(browse_button)

        panel_layout.addLayout(file_controls_layout)

        # --- Control Section ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        self._stateButton = QPushButton()
        buttons_layout.addWidget(self._stateButton)
        buttons_layout.addStretch(1)
        panel_layout.addLayout(buttons_layout)
        self._update_state_button_style() # Set initial state

        browse_button.clicked.connect(self._on_browse_clicked)
        return panel

    def _create_sample_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 10, 10, 0)
        title = QLabel("Last 10 Readings")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        indicator_layout = QHBoxLayout()
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(6)
        self._status_indicator = QLabel()
        self._status_indicator.setFixedSize(14, 14)
        self.set_threshold_indicator(False)
        indicator_layout.addWidget(self._status_indicator, alignment=Qt.AlignLeft)
        indicator_layout.addWidget(QLabel("Threshold Alert"), alignment=Qt.AlignLeft)
        indicator_layout.addStretch(1)
        layout.addLayout(indicator_layout)
        self._history_list = QListWidget()
        layout.addWidget(title)
        layout.addWidget(self._history_list)
        return panel

    def _set_indicator_color(self, color: str) -> None:
        self._status_indicator.setStyleSheet(
            f"""
            QLabel {{
                border-radius: 7px;
                background-color: {color};
            }}
            """
        )

    def _setup_chart_axes(self, chart: QChart):
        """Configures and attaches axes to the chart."""
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

        self._start_time = time.time()
        self._max_graph_points = 100  # Max points to show on the graph

    @Slot(dict)
    def add_sample(self, sample: dict):
        """Adds a new sample to the UI."""
        if not self._is_logging:
            return

        self._samples.append(sample)
        self._add_sample_to_history_list(sample)

        current_time = time.time() - self._start_time
        temp = sample.get("temp_mC", 0) / 1000.0

        # --- Caso de Uso 3: Detección de Alertas ---
        is_alert = bool(sample.get("flags", 0) & SIMTEMP_FLAG_THR_EDGE)
        if is_alert:
            # Cambia el color de la serie temporalmente si hay una alerta
            alert_pen = self._series.pen()
            alert_pen.setColor(Qt.red)
            self._series.setPen(alert_pen)

        if self._series.count() > self._max_graph_points:
            self._series.remove(0)

        self._series.append(current_time, temp)
        self._update_axes(current_time, temp)

        if is_alert:
            original_pen = self._series.pen()
            original_pen.setColor(Qt.white) # O el color que uses por defecto
            self._series.setPen(original_pen)

        if self._sample_toggle.isChecked():
            self._write_sample_to_file(sample)

    def _add_sample_to_history_list(self, sample: dict):
        """Adds a single sample to the top of the history list."""
        temp_c = sample.get("temp_mC", 0) / 1000.0
        is_alert = bool(sample.get("flags", 0) & SIMTEMP_FLAG_THR_EDGE)
        prefix = "⚠️ " if is_alert else ""
        self._history_list.insertItem(0, f"{prefix}{temp_c:.3f} °C")
        
        if self._history_list.count() > self._samples.maxlen:
            self._history_list.takeItem(self._history_list.count() - 1)
    def _update_axes(self, current_time: float, temp: float):
        """Adjusts chart axes ranges for better visualization."""
        if self._series.count() > self._max_graph_points:
            points = self._series.pointsVector()
            if points:
                self._axis_x.setRange(points[0].x(), current_time)
        else:
            if current_time > self._axis_x.max():
                self._axis_x.setMax(current_time)

        if temp < self._axis_y.min() or temp > self._axis_y.max():
            temps = [p.y() for p in self._series.pointsVector()]
            self._axis_y.setRange(min(temps) - 1, max(temps) + 1)

    def clear_data(self):
        """Clears all data from the graph and list."""
        self._series.clear()
        self._samples.clear()
        self._history_list.clear()
        self._start_time = time.time()
        self._axis_x.setRange(0, 10)
        self._axis_y.setRange(20, 30)

    def _on_state_button_clicked(self):
        """Toggles the logging state when the state button is clicked."""
        self._is_logging = not self._is_logging

        if self._is_logging:
            # --- Get settings from UI and emit request ---
            self.clear_data()
            try:
                settings = {
                    "operation_mode": "continuous",
                    "simulation_mode": self._simulationMode.currentText(),
                    "sampling_period_ms": int(self._period.text()),
                    "threshold_mc": 0,
                }
                #Config Threshold
                threshold = int(self._threshold.text())
                if threshold < 0:
                    raise ValueError("Threshold must be zero or greater.")
                settings["threshold_mc"] = threshold
                
                #Config Sampling Time
                sampling_time = int(self._samplingTime.text())
                if sampling_time < 0:
                    raise ValueError("Sampling time must be zero or greater.")
                self._sampling_timer.stop()
                if sampling_time > 0:
                    self._sampling_timer.start(sampling_time)
                self.set_threshold_indicator(False)

                self.start_logging_requested.emit(settings)
            except ValueError:
                QMessageBox.critical(self, "Invalid Input", "Please ensure all settings are valid numbers.")
                self._is_logging = False # Revert state
        else:
            self._sampling_timer.stop()
            self.stop_logging_requested.emit()
            self.set_threshold_indicator(False)
        
        self._update_state_button_style()
    
    def __expiredtime(self) -> None:
        self._sampling_timer.stop()
        if not self._is_logging:
            return
        self._is_logging = False # Actualiza el estado primero
        self.stop_logging_requested.emit()
        self._update_state_button_style()
        self.set_threshold_indicator(False)

    def _update_state_button_style(self):
        """Updates the text and color of the state button based on the logging state."""
        if self._is_logging:
            self._stateButton.setText("Stop")
            self._stateButton.setStyleSheet("background-color: #c62828; color: white;") # Red
        else:
            self._stateButton.setText("Start")
            self._stateButton.setStyleSheet("background-color: #2e7d32; color: white;") # Green

    @Slot()
    def stop_logging_from_external(self) -> None:
        """Stops logging when an external trigger requests it."""
        if not self._is_logging:
            return
        self._sampling_timer.stop()
        self._is_logging = False
        self.stop_logging_requested.emit()
        self._update_state_button_style()
        self.set_threshold_indicator(False)

    def _on_browse_clicked(self):
        """Opens a dialog to select a file path for saving."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Samples As",
            str(Path.home() / "continuous_samples.csv"),
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self._path_line_edit.setText(file_path)

    def _on_sample_toggle_changed(self, checked: bool):
        """Shows a pop-up to alert about enabling/disabling saving."""
        file_path = self._path_line_edit.text()
        if checked:
            if not file_path:
                QMessageBox.warning(self, "No File Selected", "Please select a file path before enabling storage.")
                self._sample_toggle.setChecked(False)
                return
            message = f"Samples will be stored in:\n{file_path}"
            path = Path(file_path)
            if not path.exists():
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("timestamp_ns,temperature_c\n")
                except OSError as e:
                    QMessageBox.critical(self, "File Error", f"Could not write header to file:\n{e}")
                    self._sample_toggle.setChecked(False)
                    return
        else:
            message = "Sample storage is now OFF."
        QMessageBox.information(self, "Sample Storage", message)

    def _write_sample_to_file(self, sample: dict):
        """Appends a single sample to the log file."""
        file_path = self._path_line_edit.text()
        if not file_path:
            return

        temp_c = sample.get("temp_mC", 0) / 1000.0
        timestamp_ns = sample.get("timestamp_ns", 0)
        line = f"{timestamp_ns},{temp_c:.3f}\n"
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as e:
            print(f"Error writing to file: {e}")

    @Slot(bool)
    def set_threshold_indicator(self, active: bool) -> None:
        if not hasattr(self, "_status_indicator"):
            return
        if self._indicator_active is not None and self._indicator_active == active:
            return
        self._indicator_active = active
        self._set_indicator_color(self._indicator_on_color if active else self._indicator_off_color)
