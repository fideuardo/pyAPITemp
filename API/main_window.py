from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal

from dataclasses import asdict
import selectors
import threading
from API.src.TempSensor import TempSensor
from kernel.apitest.LxDrTemp import SimTempError, SimTempTimeoutError

from API.views.side_menu import SideMenu
from API.views.work_area import WorkArea


class _ContinuousStreamWorker(QThread):
    """Background worker that listens for POLLIN events and emits samples."""

    sample_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, sensor: TempSensor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sensor = sensor
        self._stop_event = threading.Event()

    def start_stream(self) -> None:
        """Initialize and start the worker thread if not running."""
        if self.isRunning():
            return
        self._stop_event.clear()
        self.start()

    def stop_stream(self) -> None:
        """Signal the worker to stop and wait for completion."""
        if not self.isRunning():
            return
        self._stop_event.set()
        self.wait(1000)

    def run(self) -> None:
        try:
            fd = self._sensor.driver.fileno()
        except SimTempError as exc:
            self.error.emit(f"No se pudo obtener el descriptor del driver: {exc}")
            return

        selector = selectors.DefaultSelector()
        try:
            selector.register(fd, selectors.EVENT_READ)
        except OSError as exc:
            selector.close()
            self.error.emit(f"Fallo al registrar el descriptor para lectura: {exc}")
            return

        try:
            while not self._stop_event.is_set():
                events = selector.select(timeout=0.5)
                if not events:
                    continue

                for _, mask in events:
                    if mask & selectors.EVENT_READ:
                        try:
                            sample = self._sensor.driver.read_sample(timeout=0)
                        except SimTempTimeoutError:
                            continue
                        except SimTempError as exc:
                            self.error.emit(f"Error al leer muestras: {exc}")
                            self._stop_event.set()
                            return
                        self.sample_ready.emit(asdict(sample))
        finally:
            try:
                selector.unregister(fd)
            except Exception:
                pass
            selector.close()

api_information = {
    "name": "Temperature Panel Control",
    "version": "0.0.1"
}


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Instrument Panel – UI")

        self.temperature = TempSensor()
        self._stream_worker = _ContinuousStreamWorker(self.temperature, self)

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
        #logs continoues page
        self.work_area.start_logging_requested.connect(self._handle_start_logging)
        self.work_area.stop_logging_requested.connect(self._handle_stop_logging)
        #oneshot page
        self.work_area.read_now_requested.connect(self._handle_read_now)
        #settings page
        self.work_area.settings_to_write.connect(self._apply_driver_settings)
        #side menu
        self.side_menu.signal_toggle_menu.connect(self._toggle_menu_width)

        self._stream_worker.sample_ready.connect(self.work_area.on_continuous_sample_received)

        self._stream_worker.error.connect(self._handle_stream_error)

        try:
            with open("API/styles/app.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            pass

    def _handle_start_logging(self, settings: dict):
        """Applies settings and starts continuous logging."""
        self._stream_worker.stop_stream()
        self.temperature.stop()
        self._apply_driver_settings(settings)
        try:
            if not self.temperature.driver.is_open:
                self.temperature.open()
            self.temperature.start()
        except SimTempError as exc:
            QMessageBox.critical(
                self,
                "Error al iniciar",
                f"No se pudo iniciar la captura continua: {exc}",
            )
            return

        self._stream_worker.start_stream()

    def _handle_read_now(self):
        """Maneja la solicitud de lectura one-shot desde la UI."""
        try:
            # Esta es una llamada bloqueante. Para una UI más compleja,
            # se podría mover a un QThread.
            sample = self.temperature.read_once(timeout=2.0)
            if sample:
                self.work_area.on_one_shot_sample_received(asdict(sample))
            else:
                # Enviar un diccionario vacío si no se recibe muestra pero no hay error
                self.work_area.on_one_shot_sample_received({})
        except SimTempError as e:
            # Maneja errores (ej. timeout) y notifica al usuario
            QMessageBox.warning(self, "Read Error", f"Failed to read one-shot sample: {e}")
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

    def _handle_stop_logging(self) -> None:
        self._stream_worker.stop_stream()
        try:
            self.temperature.stop()
        except SimTempError as exc:
            QMessageBox.warning(
                self,
                "Aviso",
                f"No se pudo detener el driver correctamente: {exc}",
            )

    def _handle_stream_error(self, message: str) -> None:
        self._stream_worker.stop_stream()
        try:
            self.temperature.stop()
        except SimTempError:
            pass
        QMessageBox.critical(self, "Lectura continua", message)

    def closeEvent(self, event) -> None:
        self._stream_worker.stop_stream()
        try:
            self.temperature.stop()
        except SimTempError:
            pass
        self.temperature.close()
        super().closeEvent(event)
