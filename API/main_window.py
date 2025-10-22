from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QMessageBox
from PySide6.QtCore import Qt

from dataclasses import asdict
from API.src.TempSensor import TempSensor
from kernel.apitest.LxDrTemp import SimTempError

from API.views.side_menu import SideMenu
from API.views.work_area import WorkArea

api_information = {
    "name": "Temperature Panel Control",
    "version": "0.0.1"
}

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
        self.work_area.set_welcome_page_info(api_information, self.temperature.info) # Pasa la info del sensor
        self.work_area.set_settings_page_info(self.temperature.driverconfig)

        self.side_menu.signal_show_welcome.connect(lambda: self.work_area.goto("welcome"))
        self.side_menu.signal_show_settings.connect(lambda: self.work_area.goto("settings"))
        self.side_menu.signal_show_logs.connect(lambda: self.work_area.goto("logs"))

        # self.work_area.start_logging_requested.connect(self.temperature.start_logging)
        # self.work_area.stop_logging_requested.connect(self.temperature.stop_logging)
        self.work_area.read_now_requested.connect(self._handle_read_now)

        self.work_area.settings_to_write.connect(self._apply_driver_settings)
        self.side_menu.signal_toggle_menu.connect(self._toggle_menu_width)

        try:
            with open("API/styles/app.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            pass

    def _handle_read_now(self):
        """Maneja la solicitud de lectura one-shot desde la UI."""
        try:
            # Esta es una llamada bloqueante. Para una UI más compleja,
            # se podría mover a un QThread.
            sample = self.temperature.read_once(timeout=2.0)
            if sample:
                # Pasa el resultado de vuelta a la UI a través de WorkArea
                self.work_area.on_one_shot_sample_received(asdict(sample))
        except SimTempError as e:
            # Maneja errores (ej. timeout) y notifica al usuario
            QMessageBox.critical(self, "Read Error", f"Failed to read one-shot sample: {e}")
            # Envía un diccionario vacío para que la UI pueda resetear su estado
            self.work_area.on_one_shot_sample_received({})

    def _apply_driver_settings(self, settings: dict):
        """Aplica la configuración recibida desde la UI al driver."""
        errors: list[str] = []
        for key, value in settings.items():
            try:
                if key == "operation_mode":
                    self.temperature.set_operation_mode(value)
                elif key == "simulation_mode":
                    self.temperature.set_simulation_mode(value)
                elif key == "sampling_period_ms":
                    self.temperature.set_sampling_period_ms(int(value))
                elif key == "threshold_mc":
                    self.temperature.set_threshold_mc(int(value))
            except SimTempError as exc:
                errors.append(f"{key}: {exc}")

        # Refrescar la información de configuración en la UI después de aplicar los cambios
        self.work_area.set_settings_page_info(self.temperature.driverconfig)

        if errors:
            QMessageBox.warning(
                self,
                "Configuración no aplicada",
                "No se pudieron aplicar algunos ajustes:\n- " + "\n- ".join(errors),
            )

    def _toggle_menu_width(self):
        w = self.side_menu.width()
        if w > 60:
            self._last_menu_width = w
            self.side_menu.setFixedWidth(56)
        else:
            self.side_menu.setFixedWidth(getattr(self, "_last_menu_width", 220))
