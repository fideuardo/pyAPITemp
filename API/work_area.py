from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from .welcome_page import WelcomePage # Importa la nueva página

class WorkArea(QWidget):
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

        self._welcome_page = WelcomePage() # Instancia la nueva página
        self._add_page("welcome", self._welcome_page)
        self._add_page("settings", self._make_label("Work Area — Settings"))
        self._add_page("logs", self._make_label("Work Area — Logs"))
        self.goto("welcome")

    def _make_label(self, text: str) -> QWidget:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def set_welcome_page_info(self, api_info: dict[str, str], driver_info: dict[str, str]):
        """Establece la información del sensor a mostrar en la página de bienvenida."""
        self._welcome_page.set_info("API", api_info, "Driver", driver_info)

    def _add_page(self, name: str, widget: QWidget):
        idx = self.stack.addWidget(widget)
        self._pages[name] = idx

    def goto(self, name: str):
        if name in self._pages:
            self.stack.setCurrentIndex(self._pages[name])
