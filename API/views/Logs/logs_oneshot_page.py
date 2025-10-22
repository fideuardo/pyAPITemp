from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, Slot, Signal


class LogsOneShotPage(QWidget):
    """Página con un botón para solicitar una lectura en modo One-Shot."""
    read_now_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("One-Shot Sample")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self._read_now_button = QPushButton("Read Now")
        self._read_now_button.setStyleSheet("""
            QPushButton {
                background-color: #5a9bde; color: white; border: none;
                padding: 8px 16px; font-size: 14px; border-radius: 4px;
                margin-top: 15px;
            }
            QPushButton:hover { background-color: #6aa7e8; }
            QPushButton:pressed { background-color: #4a8ac8; }
        """)
        layout.addWidget(self._read_now_button, alignment=Qt.AlignCenter)
        self._read_now_button.clicked.connect(self.read_now_requested.emit)