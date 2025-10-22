from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, Slot


class LogsMainPage(QWidget):
    """Página principal para la sección de Logs con controles de inicio/parada."""
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogsMainPage")
        self.setStyleSheet("background-color: #3a404a; color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Logging Control")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        self._mode_label = QLabel("Mode: N/A")
        self._mode_label.setStyleSheet("font-size: 16px; font-style: italic; margin-bottom: 20px;")
        self._mode_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self._mode_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setAlignment(Qt.AlignCenter)

        self._start_button = QPushButton("Start Logging")
        self._stop_button = QPushButton("Stop Logging")

        button_layout.addWidget(self._start_button)
        button_layout.addWidget(self._stop_button)

        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)

        self._start_button.clicked.connect(self._on_start_clicked)
        self._stop_button.clicked.connect(self._on_stop_clicked)

        self._set_initial_state()

    @Slot(str)
    def set_operation_mode(self, mode: str):
        """Actualiza la etiqueta que muestra el modo de operación actual."""
        self._mode_label.setText(f"Mode: <b>{mode.capitalize()}</b>")

    def _set_initial_state(self):
        """Establece el color inicial de los botones (estado detenido)."""
        self._start_button.setStyleSheet("background-color: #c62828;") # Rojo
        self._stop_button.setStyleSheet("background-color: #2e7d32;")  # Verde

    def _on_start_clicked(self):
        self._start_button.setStyleSheet("background-color: #2e7d32;") # Verde
        self._stop_button.setStyleSheet("background-color: #c62828;")  # Rojo
        self.start_requested.emit()

    def _on_stop_clicked(self):
        self._start_button.setStyleSheet("background-color: #c62828;") # Rojo
        self._stop_button.setStyleSheet("background-color: #2e7d32;")  # Verde
        self.stop_requested.emit()