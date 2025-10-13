from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy

class SideMenu(QWidget):
    signal_show_dashboard = Signal()
    signal_show_logs = Signal()
    signal_show_settings = Signal()
    signal_toggle_menu = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setObjectName("SideMenu")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        title = QLabel("Menu")
        title.setObjectName("MenuTitle")
        title.setAlignment(Qt.AlignHCenter)

        btn_dashboard = QPushButton("Dashboard")
        btn_logs = QPushButton("Logs")
        btn_settings = QPushButton("Settings")

        for b in (btn_dashboard, btn_logs, btn_settings):
            b.setObjectName("MenuButton")
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setMinimumHeight(36)

        btn_collapse = QPushButton("⟨⟩")
        btn_collapse.setObjectName("CollapseButton")
        btn_collapse.setToolTip("Colapsar/expandir menú")
        btn_collapse.setMinimumHeight(28)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(btn_dashboard)
        layout.addWidget(btn_logs)
        layout.addWidget(btn_settings)
        layout.addSpacing(6)
        layout.addWidget(sep)
        layout.addWidget(btn_collapse, alignment=Qt.AlignHCenter)
        layout.addStretch(1)

        btn_dashboard.clicked.connect(self.signal_show_dashboard.emit)
        btn_logs.clicked.connect(self.signal_show_logs.emit)
        btn_settings.clicked.connect(self.signal_show_settings.emit)
        btn_collapse.clicked.connect(self.signal_toggle_menu.emit)
