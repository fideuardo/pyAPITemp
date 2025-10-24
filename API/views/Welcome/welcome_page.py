from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QFrame
from PySide6.QtCore import Qt, Signal

class WelcomePage(QWidget):
    """Widget to display general welcome information and driver metadata."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomePage")
        # Basic styling; feel free to refine it via QSS
        self.setStyleSheet("background-color: #3a404a; color: white;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setAlignment(Qt.AlignTop)
        self._main_layout.setContentsMargins(20, 20, 20, 20)
        self._main_layout.setSpacing(15)

        title = QLabel("Welcome to the Instrument Panel")
        title.setObjectName("WelcomeTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        self._main_layout.addWidget(title)

        # Container for dynamic information blocks
        self._info_container = QWidget()
        self._main_layout.addWidget(self._info_container)
        self._main_layout.addStretch(1)

    def _create_info_group(self, title: str, info_dict: dict[str, str]) -> QWidget:
        """Create a widget for an information block (e.g., 'API' or 'Driver')."""
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("InfoGroupTitle")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        group_layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(15, 0, 0, 0)  # Indentation
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(5)

        for key, value in info_dict.items():
            key_label = QLabel(f"{key.capitalize()}:")
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            form_layout.addRow(key_label, value_label)

        group_layout.addLayout(form_layout)
        return group_widget

    def set_info(self, *args, alignment: str = "vertical"):
        """
        Display information blocks with either vertical or horizontal alignment.
        Example: set_info("API", api_dict, "Driver", driver_dict, alignment="horizontal")
        """
        # Clear any existing container
        layout = self._info_container.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        if alignment == "horizontal":
            container_layout = QHBoxLayout(self._info_container)
            container_layout.setAlignment(Qt.AlignTop)
        else:  # Defaults to "vertical"
            container_layout = QVBoxLayout(self._info_container)

        # Process arguments as (title, dictionary) pairs
        for i in range(0, len(args), 2):
            title = args[i]
            info_dict = args[i+1]
            group_widget = self._create_info_group(title, info_dict)
            container_layout.addWidget(group_widget)

        if alignment == "horizontal":
            container_layout.addStretch(1)

    def set_sensor_info(self, info: dict[str, str]):
        """Backward-compatible helper for the previous method name."""
        self.set_info("Driver", info, alignment="vertical")

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    # Create the application
    app = QApplication(sys.argv)

    # Create an instance of the welcome page
    welcome_widget = WelcomePage()

    # Provide sample data for debugging
    dummy_api_info = {"name": "Temperature Panel Control", "version": "0.0.1"}

    # Additional sample data mirroring the structure of `sensor.info`
    dummy_driver_info = {
        "name": "SimTempDriver (Debug)",
        "version": "v0.1-debug",
        "description": "This is a standalone test of the WelcomePage widget. It shows how text can wrap if it is very long.",
    }

    # --- Demo of the new helper ---
    # Change "vertical" to "horizontal" to preview the other layout
    alignment_mode = "vertical"
    welcome_widget.set_info("API", dummy_api_info, "Driver", dummy_driver_info, alignment=alignment_mode)

    # Show the widget and run the application
    welcome_widget.resize(800, 400)
    welcome_widget.show()
    sys.exit(app.exec())
