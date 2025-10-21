from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QFrame
from PySide6.QtCore import Qt, Signal

class WelcomePage(QWidget):
    """Widget to display general welcome information and driver metadata."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomePage")
        # Estilo básico para que se vea bien, puedes ajustarlo con QSS
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

        # Contenedor para la información dinámica
        self._info_container = QWidget()
        self._main_layout.addWidget(self._info_container)
        self._main_layout.addStretch(1)

    def _create_info_group(self, title: str, info_dict: dict[str, str]) -> QWidget:
        """Crea un widget para un bloque de información (ej. 'API' o 'Driver')."""
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("InfoGroupTitle")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        group_layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(15, 0, 0, 0) # Indentación
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
        Muestra bloques de información con alineación vertical u horizontal.
        Ejemplo: set_info("API", api_dict, "Driver", driver_dict, alignment="horizontal")
        """
        # Limpia el contenedor anterior
        if self._info_container.layout() is not None:
            # Elimina el layout y su contenido de forma segura
            QWidget().setLayout(self._info_container.layout())

        if alignment == "horizontal":
            container_layout = QHBoxLayout(self._info_container)
            container_layout.setAlignment(Qt.AlignTop)
        else: # "vertical" por defecto
            container_layout = QVBoxLayout(self._info_container)

        # Procesa los argumentos en pares (título, diccionario)
        for i in range(0, len(args), 2):
            title = args[i]
            info_dict = args[i+1]
            group_widget = self._create_info_group(title, info_dict)
            container_layout.addWidget(group_widget)

        if alignment == "horizontal":
            container_layout.addStretch(1)

    def set_sensor_info(self, info: dict[str, str]):
        """Mantiene la compatibilidad con el método anterior."""
        self.set_info("Driver", info, alignment="vertical")

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    # Crea la aplicación
    app = QApplication(sys.argv)

    # Crea una instancia de la página de bienvenida
    welcome_widget = WelcomePage()

    # Proporciona datos de prueba para la depuración
    dummy_api_info = {"name": "Temperature Panel Control", "version": "0.0.1"}

    # Proporciona datos de prueba para la depuración, imitando la estructura de `sensor.info`
    dummy_driver_info = {
        "name": "SimTempDriver (Debug)",
        "version": "v0.1-debug",
        "description": "This is a standalone test of the WelcomePage widget. It shows how text can wrap if it is very long.",
    }

    # --- Prueba de la nueva función ---
    # Cambia "vertical" por "horizontal" para ver el otro layout
    alignment_mode = "vertical"
    welcome_widget.set_info("API", dummy_api_info, "Driver", dummy_driver_info, alignment=alignment_mode)

    # Muestra el widget y ejecuta la aplicación
    welcome_widget.resize(800, 400)
    welcome_widget.show()
    sys.exit(app.exec())