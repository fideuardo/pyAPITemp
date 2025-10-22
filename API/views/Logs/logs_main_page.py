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
    start_requested = Signal()
    stop_requested = Signal()
    read_now_requested = Signal()

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
        
        # Nuevo layout horizontal para la etiqueta de modo y los botones
        mode_and_buttons_layout = QHBoxLayout()
        mode_and_buttons_layout.setContentsMargins(0, 0, 0, 0)
        mode_and_buttons_layout.setSpacing(20) # Espacio entre la etiqueta y los botones
        
        self._mode_label = QLabel("Mode: N/A")
        self._mode_label.setStyleSheet("font-size: 16px; font-style: italic; margin-bottom: 20px;")
        self._mode_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Alinear a la izquierda y centrar verticalmente
        mode_and_buttons_layout.addWidget(self._mode_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter) # Alinear a la derecha y centrar verticalmente
        self._start_button = QPushButton("Start Logging")
        self._stop_button = QPushButton("Stop Logging")
        
        button_layout.addWidget(self._start_button)
        button_layout.addWidget(self._stop_button)

        mode_and_buttons_layout.addLayout(button_layout)
        main_layout.addLayout(mode_and_buttons_layout) # Añadir el nuevo layout al layout principal

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

        self._start_button.clicked.connect(self._on_start_clicked)
        self._stop_button.clicked.connect(self._on_stop_clicked)
        self._set_initial_state()
        self._oneshot_panel.read_now_requested.connect(self.read_now_requested.emit)

    @Slot(str)
    def set_operation_mode(self, mode: str):
        """Actualiza la etiqueta que muestra el modo de operación actual."""
        is_continuous = (mode == "continuous")

        # Mostrar/ocultar botones de control de logging continuo
        self._start_button.setVisible(is_continuous)
        self._stop_button.setVisible(is_continuous)

        # Cambiar entre el panel one-shot y el panel de gráfico
        self._data_panel_stack.setCurrentWidget(self._continuous_panel if is_continuous else self._oneshot_panel)
        self._mode_label.setText(f"Mode: <b>{mode.capitalize()}</b>") # Actualiza la etiqueta

    def _set_initial_state(self):
        """Establece el color inicial de los botones (estado detenido)."""
        self._update_button_styles(is_running=False)

    def _update_button_styles(self, is_running: bool):
        """Actualiza los estilos de los botones según el estado de logging."""
        running_style = "background-color: #2e7d32;"  # Verde
        stopped_style = "background-color: #c62828;"  # Rojo
        self._start_button.setStyleSheet(running_style if is_running else stopped_style)
        self._stop_button.setStyleSheet(stopped_style if is_running else running_style)

    def _on_start_clicked(self):
        self._update_button_styles(is_running=True)
        print("start press")
        self.start_requested.emit()

    def _on_stop_clicked(self):
        print("stop press")
        self._update_button_styles(is_running=False)
        self.stop_requested.emit()

    @Slot(dict)
    def on_sample_received(self, sample: dict):
        self._oneshot_panel.display_sample(sample)

    @Slot(dict)
    def on_continuous_sample_received(self, sample: dict):
        self._continuous_panel.add_sample(sample)