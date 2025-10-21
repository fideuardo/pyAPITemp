from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget
from PySide6.QtCore import Qt

from API.src.TempSensor import TempSensor

from .side_menu import SideMenu
from .work_area import WorkArea

class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        self.temperature = TempSensor()

        super().__init__(parent)
        self.setWindowTitle("Instrument Panel – UI")

        self.splitter = QSplitter(Qt.Horizontal, self)
        self.side_menu = SideMenu()
        self.work_area = WorkArea()

        self.splitter.addWidget(self.side_menu)
        self.splitter.addWidget(self.work_area)
        self.splitter.setSizes([220, 580])
        self.splitter.setHandleWidth(1)

        self.side_menu.setMinimumWidth(180)
        self.side_menu.setMaximumWidth(320)
        self.setCentralWidget(self.splitter)

        self.side_menu.signal_show_dashboard.connect(lambda: self.work_area.goto("dashboard"))
        self.side_menu.signal_show_settings.connect(lambda: self.work_area.goto("settings"))
        self.side_menu.signal_show_logs.connect(lambda: self.work_area.goto("logs"))
        self.side_menu.signal_toggle_menu.connect(self._toggle_menu_width)

        try:
            with open("styles/app.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            pass

    def _toggle_menu_width(self):
        w = self.side_menu.width()
        if w > 60:
            self._last_menu_width = w
            self.side_menu.setFixedWidth(56)
        else:
            self.side_menu.setFixedWidth(getattr(self, "_last_menu_width", 220))
