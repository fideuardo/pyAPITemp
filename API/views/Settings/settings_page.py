from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox, QPushButton, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator


class SettingsPage(QWidget):
    """Widget to display driver configuration."""

    # Signal that emits a dictionary with the configuration to write
    settings_to_write = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self.setStyleSheet("background-color: #3a404a; color: white;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setAlignment(Qt.AlignTop)
        self._main_layout.setContentsMargins(20, 20, 20, 20)
        self._main_layout.setSpacing(15)

        title = QLabel("Driver Configuration")
        title.setObjectName("SettingsTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        self._main_layout.addWidget(title)

        self._form_layout = QFormLayout()
        self._main_layout.addLayout(self._form_layout)

        # Button to apply the changes
        self._write_button = QPushButton("Write Settings")
        self._write_button.clicked.connect(self._on_write_settings)
        self._main_layout.addWidget(self._write_button, alignment=Qt.AlignRight)

        self._main_layout.addStretch(1)

        # Store a reference to the input widgets
        self._input_widgets: dict[str, QWidget] = {}

        # Definition of the form structure, order, and widget types
        self._form_layout_definition = [
            {"key": "name", "widget": "label"},
            {"key": "version", "widget": "label"},
            {"key": "state", "widget": "label"},
            {
                "key": "operation_mode",
                "widget": "combobox",
                "options": ["one-shot", "continuous"],
            },
            {
                "key": "simulation_mode",
                "widget": "combobox",
                "options": ["normal", "noisy", "ramp"],
            },
            {
                "key": "threshold_mc",
                "widget": "lineedit",
                "validator": QIntValidator(0, 150000, self),
            },
            {
                "key": "sampling_period_ms",
                "widget": "lineedit",
                "validator": QIntValidator(5, 5000, self),
            },
        ]

    def set_config_info(self, config: dict[str, str]):
        """Updates the displayed sensor configuration information."""
        # Clear existing layout
        # Use a more robust way to clear the layout to avoid Qt warnings.
        while self._form_layout.count() > 0:
            item = self._form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._input_widgets.clear()

        for field_def in self._form_layout_definition:
            key = field_def["key"]
            if key not in config:
                continue

            value = config[key]
            key_label = QLabel(f"{key.replace('_', ' ').capitalize()}:")
            widget_type = field_def["widget"]

            if widget_type == "combobox":
                combo = QComboBox()
                combo.addItems(field_def["options"])
                combo.setCurrentText(str(value))
                self._form_layout.addRow(key_label, combo)
                self._input_widgets[key] = combo
            elif widget_type == "lineedit":
                line_edit = QLineEdit(str(value))
                line_edit.setValidator(field_def["validator"])
                self._form_layout.addRow(key_label, line_edit)
                self._input_widgets[key] = line_edit
            else:  # "label"
                value_label = QLabel(str(value) if value is not None else "N/A")
                self._form_layout.addRow(key_label, value_label)

    def _on_write_settings(self):
        """Collect values from the widgets and emit the signal."""
        settings = {}
        for key, widget in self._input_widgets.items():
            if isinstance(widget, QComboBox):
                settings[key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                # Only add non-empty values
                if widget.text():
                    settings[key] = widget.text()

        if settings:
            self.settings_to_write.emit(settings)
