from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

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

        self._add_page("dashboard", self._make_label("Work Area — Dashboard"))
        self._add_page("logs", self._make_label("Work Area — Logs"))
        self._add_page("settings", self._make_label("Work Area — Settings"))
        self.goto("dashboard")

    def _make_label(self, text: str) -> QWidget:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def _add_page(self, name: str, widget: QWidget):
        idx = self.stack.addWidget(widget)
        self._pages[name] = idx

    def goto(self, name: str):
        if name in self._pages:
            self.stack.setCurrentIndex(self._pages[name])
