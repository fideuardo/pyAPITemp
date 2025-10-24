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
    """Page with a button to request a one-shot reading."""
    read_now_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples = deque(maxlen=10)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        header_panel = self._create_header_panel()
        layout.addWidget(header_panel)

        # Main data layout
        data_layout = QHBoxLayout()
        layout.addLayout(data_layout)

        # --- Samples Register ---
        self._sample_panel = self._create_sample_panel()
        data_layout.addWidget(self._sample_panel, 1) # first section panel

        # --- Samples Graphic ---
        self._graph_panel = self._create_graph_panel()
        data_layout.addWidget(self._graph_panel, 3)

        self._read_now_button.clicked.connect(self.read_now)
        self._sample_toggle.toggled.connect(self._on_sample_toggle_changed)

    def _create_header_panel(self) -> QWidget:

        """Creates the top panel containing the title, mode, and control button."""
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 10) # Bottom margin

        title = QLabel("Logging Control")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)

        # Read button (centered)
        self._read_now_button = QPushButton("Read Now")
        self._read_now_button.setStyleSheet("""
            QPushButton {
                background-color: #5a9bde; color: white; border: none;
                padding: 8px 16px; font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #6aa7e8; }
            QPushButton:pressed { background-color: #4a8ac8; }
        """)

        # Samples toggle switch
        self._sample_toggle = QCheckBox("Samples")
        self._sample_toggle.setStyleSheet("font-size: 14px;")

        # Mode label (right)
        mode_label = QLabel("Mode: <b>One-Shot</b>")
        mode_label.setStyleSheet("font-size: 16px; font-style: italic;")
        
        controls_layout = QHBoxLayout()

        # Add widgets to the layout
        controls_layout.addWidget(mode_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._read_now_button, alignment=Qt.AlignCenter | Qt.AlignVCenter)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._sample_toggle, alignment=Qt.AlignRight | Qt.AlignVCenter)

        # --- File saving controls ---
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
        """Executes when the 'Read Now' button is pressed."""
        self._read_now_button.setEnabled(False)
        self.read_now_requested.emit()

    @Slot(dict)
    def display_sample(self, sample: dict):
        """Displays the temperature of the received sample."""
        
        if sample and "temp_mC" in sample:
            self._samples.append(sample)
            self._update_ui()
            
            # Write to file if the toggle is enabled
            if self._sample_toggle.isChecked():
                self._write_sample_to_file(sample)

        self._read_now_button.setEnabled(True)

    def _update_ui(self):
        """Updates the history list and the chart with the current data."""
        # Update list
        self._history_list.clear()
        for i, sample in enumerate(reversed(self._samples)):
            temp_c = sample.get("temp_mC", 0) / 1000.0
            self._history_list.insertItem(0, f"#{len(self._samples) - i}: {temp_c:.3f} °C")

        # Update chart
        points = [ (i, s.get("temp_mC", 0) / 1000.0) for i, s in enumerate(self._samples) ]
        self._series.replace([QPointF(p[0], p[1]) for p in points])

        # Adjust axes
        if points:
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            self._axis_x.setRange(0, max(9, len(points) - 1))
            self._axis_y.setRange(min_y - 0.5, max_y + 0.5)

    def _on_browse_clicked(self):
        """Opens a dialog to select a file path for saving."""
        # Open a save dialog, suggesting a filename and type
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Samples As",
            str(Path.home() / "samples.csv"),  # Default directory and filename
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
                self._sample_toggle.setChecked(False)  # Revert the change
                return
            message = f"Samples will be stored in:\n{file_path}"
            # Check if the file is new to write the header
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
            with open(file_path, "a", encoding="utf-8") as f: # 'a' for append
                f.write(line)
        except OSError as e:
            print(f"Error writing to file: {e}")
            # Optional: Disable the toggle and notify the user if writing fails repeatedly.
            # self._sample_toggle.setChecked(False)
            # QMessageBox.critical(self, "File Error", f"Failed to write to file:\n{e}")
