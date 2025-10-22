from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from .Welcome.welcome_page import WelcomePage
from .Settings.settings_page import SettingsPage
from .Logs.logs_main_page import LogsMainPage

class  WorkArea(QWidget):

    settings_to_write = Signal(dict)
    read_now_requested = Signal()


    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages: dict[str, int] = {}
        self._build()

    def _build(self):
        self.setObjectName("WorkArea")
        self.setStyleSheet("background-color: #2c313c;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self._welcome_page = WelcomePage()
        self._settings_page = SettingsPage()
        self._logs_main_page = LogsMainPage()

        self._add_page("welcome", self._welcome_page)
        self._add_page("settings", self._settings_page)
        self._add_page("logs", self._logs_main_page)

        # Connect the signal from the settings page to this class's signal
        self._settings_page.settings_to_write.connect(self.settings_to_write)
        self._logs_main_page.read_now_requested.connect(self.read_now_requested.emit)

        self.goto("welcome")

    def _make_label(self, text: str) -> QWidget:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def set_welcome_page_info(self, api_info: dict[str, str], driver_info: dict[str, str]) -> None:
        """Establece la información del sensor a mostrar en la página de bienvenida."""
        self._welcome_page.set_info("API", api_info, "Driver", driver_info)

    def set_settings_page_info(self, config_info: dict[str, str]) -> None:
        self._settings_page.set_config_info(config_info)
        # Aprovechamos para informar a la página de logs sobre el modo actual
        if "operation_mode" in config_info:
            self._logs_main_page.set_operation_mode(config_info["operation_mode"])

    # --- Nuevos métodos para interactuar con LogsPage ---

    def _add_page(self, name: str, widget: QWidget):
        idx = self.stack.addWidget(widget)
        self._pages[name] = idx

    def goto(self, name: str):
        if name in self._pages:
            self.stack.setCurrentIndex(self._pages[name])

    def on_one_shot_sample_received(self, sample: dict):
        """Pasa la muestra recibida a la página de logs."""
        self._logs_main_page.on_sample_received(sample)
