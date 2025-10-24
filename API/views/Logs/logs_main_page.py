from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, Slot
from .logs_oneshot_page import LogsOneShotPage
from .logs_continuous_page import LogsContinuousPage
 

class LogsMainPage(QWidget):
    """Página principal para la sección de Logs con controles de inicio/parada."""
    read_now_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogsMainPage")
        self.setStyleSheet("background-color: #3a404a; color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- Paneles de Datos (intercambiables) ---
        self._data_panel_stack = QStackedWidget()
        main_layout.addWidget(self._data_panel_stack)

        # Panel para modo One-Shot
        self._oneshot_panel = LogsOneShotPage()
        self._data_panel_stack.addWidget(self._oneshot_panel)

        # Panel para modo Continuo (gráfico)
        self._continuous_panel = LogsContinuousPage()
        self._data_panel_stack.addWidget(self._continuous_panel)
        # ------------------------------------------

        main_layout.addStretch(1)

        self._oneshot_panel.read_now_requested.connect(self.read_now_requested.emit)

    @Slot(str)
    def set_operation_mode(self, mode: str):
        """Actualiza la etiqueta que muestra el modo de operación actual."""
        is_continuous = (mode == "continuous")

        # Cambiar entre el panel one-shot y el panel de gráfico
        self._data_panel_stack.setCurrentWidget(self._continuous_panel if is_continuous else self._oneshot_panel)

    @Slot(dict)
    def on_sample_received(self, sample: dict):
        self._oneshot_panel.display_sample(sample)

    @Slot(dict)
    def on_continuous_sample_received(self, sample: dict):
        self._continuous_panel.add_sample(sample)
