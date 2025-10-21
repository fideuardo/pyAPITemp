from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox, QPushButton
from PySide6.QtCore import Qt, Signal


class SettingsPage(QWidget):
    """Widget to display driver configuration."""

    # Nueva señal que emite un diccionario con la configuración a escribir
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

        # Botón para aplicar los cambios
        self._write_button = QPushButton("Write Settings")
        self._write_button.clicked.connect(self._on_write_settings)
        self._main_layout.addWidget(self._write_button, alignment=Qt.AlignRight)

        self._main_layout.addStretch(1)

        # Diccionario para mantener una referencia a los widgets de entrada
        self._input_widgets: dict[str, QWidget] = {}
        # Lista para mantener los widgets de la fila de sampling_period_ms
        self._sampling_period_row_widgets: list[QWidget] = []


    def set_config_info(self, config: dict[str, str]):
        """Updates the displayed sensor configuration information."""
        # Clear existing layout
        while (item := self._form_layout.takeAt(0)) is not None:
            if item.widget():
                item.widget().deleteLater()
        self._input_widgets.clear()
        self._sampling_period_row_widgets.clear()

        # Define el orden explícito en el que se deben mostrar los campos
        field_order = [
            "name",
            "version",
            "state",
            "operation_mode",
            "simulation_mode",
            "threshold_mc",
            "sampling_period_ms",
        ]

        operation_mode_combo = None

        # Iterar sobre la lista ordenada para construir la UI
        for key in field_order:
            if key not in config:
                continue  # Si por alguna razón un campo no viene, lo saltamos

            value = config[key]
            key_label = QLabel(f"{key.replace('_', ' ').capitalize()}:")

            if key == "operation_mode":
                combo = QComboBox()
                combo.addItems(["oneshot", "continuous"])
                combo.setCurrentText(str(value))
                self._form_layout.addRow(key_label, combo)
                self._input_widgets[key] = combo
                operation_mode_combo = combo
            else:
                value_label = QLabel(str(value) if value is not None else "N/A")
                self._form_layout.addRow(key_label, value_label)
                if key == "sampling_period_ms":
                    self._sampling_period_row_widgets = [key_label, value_label]

        # Conectar la señal y establecer la visibilidad inicial
        if operation_mode_combo:
            operation_mode_combo.currentTextChanged.connect(self._update_sampling_period_visibility)
            self._update_sampling_period_visibility(operation_mode_combo.currentText())

    def _on_write_settings(self):
        """Recopila los valores de los widgets de entrada y emite la señal."""
        settings = {}
        for key, widget in self._input_widgets.items():
            if isinstance(widget, QComboBox):
                settings[key] = widget.currentText()
            # Aquí se pueden añadir otros tipos de widgets (QLineEdit, QSpinBox, etc.)
            # elif isinstance(widget, QLineEdit):
            #     settings[key] = widget.text()

        if settings:
            self.settings_to_write.emit(settings)

    def _update_sampling_period_visibility(self, mode: str):
        """Muestra u oculta la fila de 'sampling_period_ms'."""
        is_visible = (mode == "continuous")
        for widget in self._sampling_period_row_widgets:
            widget.setVisible(is_visible)