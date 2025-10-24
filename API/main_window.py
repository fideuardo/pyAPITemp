from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal, Slot

from dataclasses import asdict
import selectors
import threading
from API.src.TempSensor import TempSensor
from kernel.apitest.LxDrTemp import SIMTEMP_FLAG_THR_EDGE, SimTempError, SimTempTimeoutError

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
            self.error.emit(f"Failed to obtain the driver file descriptor: {exc}")
            return

        selector = selectors.DefaultSelector()
        try:
            selector.register(fd, selectors.EVENT_READ)
        except OSError as exc:
            selector.close()
            self.error.emit(f"Failed to register the descriptor for reading: {exc}")
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
                            self.error.emit(f"Error while reading samples: {exc}")
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
        self._current_threshold_mc = 0

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
        self.work_area.set_welcome_page_info(api_information, self.temperature.info)  # Provide sensor info to the page
        driver_config = self.temperature.driverconfig
        self.work_area.set_settings_page_info(driver_config)
        try:
            threshold_value = driver_config.get("threshold_mc")
            self._current_threshold_mc = int(threshold_value) if threshold_value is not None else 0
        except (TypeError, ValueError):
            self._current_threshold_mc = 0

        self.side_menu.signal_show_welcome.connect(lambda: self.work_area.goto("welcome"))
        self.side_menu.signal_show_settings.connect(lambda: self.work_area.goto("settings"))
        self.side_menu.signal_show_logs.connect(lambda: self.work_area.goto("logs"))
        # Continuous logging page
        self.work_area.start_logging_requested.connect(self._handle_start_logging)
        self.work_area.stop_logging_requested.connect(self._handle_stop_logging)
        # One-shot page
        self.work_area.read_now_requested.connect(self._handle_read_now)
        # Settings page
        self.work_area.settings_to_write.connect(self._apply_driver_settings)
        # Side menu
        self.side_menu.signal_toggle_menu.connect(self._toggle_menu_width)

        self._stream_worker.sample_ready.connect(self._handle_continuous_sample)

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
        self.work_area.set_threshold_indicator(False)
        self._apply_driver_settings(settings)
        try:
            if not self.temperature.driver.is_open:
                self.temperature.open()
            self.temperature.start()
        except SimTempError as exc:
            QMessageBox.critical(
                self,
                "Start Error",
                f"Failed to start the continuous capture: {exc}",
            )
            return

        self._stream_worker.start_stream()
        self.work_area.set_threshold_indicator(False)
        threshold_setting = settings.get("threshold_mc")
        if threshold_setting is not None:
            try:
                self._current_threshold_mc = int(threshold_setting)
            except (TypeError, ValueError):
                pass

    def _handle_read_now(self):
        """Handle the one-shot read request coming from the UI."""
        try:
            # This is a blocking call; for a more complex UI we could delegate to a QThread.
            sample = self.temperature.read_once(timeout=2.0)
            if sample:
                self.work_area.on_one_shot_sample_received(asdict(sample))
            else:
                # Send an empty payload if no sample arrives but no error occurred
                self.work_area.on_one_shot_sample_received({})
        except SimTempError as e:
            # Handle errors (for example a timeout) and notify the user
            QMessageBox.warning(self, "Read Error", f"Failed to read one-shot sample: {e}")
            # Provide an empty payload so the UI can reset its state
            self.work_area.on_one_shot_sample_received({})

    def _apply_driver_settings(self, settings: dict):
        """Apply the configuration received from the UI to the driver."""
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
                    threshold_value = int(value)
                    self.temperature.set_threshold_mc(threshold_value)
                    self._current_threshold_mc = threshold_value
            except SimTempError as exc:
                errors.append(f"{key}: {exc}")
                
        # Refresh the configuration information in the UI after applying the changes
        self.work_area.set_settings_page_info(self.temperature.driverconfig)

        if errors:
            QMessageBox.warning(
                self,
                "Settings Not Applied",
                "Some adjustments could not be applied:\n- " + "\n- ".join(errors),
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
                "Warning",
                f"Failed to stop the driver correctly: {exc}",
            )
        finally:
            self.work_area.set_threshold_indicator(False)

    def _handle_stream_error(self, message: str) -> None:
        self._stream_worker.stop_stream()
        try:
            self.temperature.stop()
        except SimTempError:
            pass
        QMessageBox.critical(self, "Continuous Read", message)
        self.work_area.set_threshold_indicator(False)

    @Slot(dict)
    def _handle_continuous_sample(self, sample: dict) -> None:
        self.work_area.on_continuous_sample_received(sample)
        flags = sample.get("flags", 0)
        temp_mc = sample.get("temp_mC")
        threshold = self._current_threshold_mc
        above_threshold = (
            isinstance(temp_mc, (int, float))
            and isinstance(threshold, (int, float))
            and threshold > 0
            and temp_mc >= threshold
        )
        is_alert = bool(flags & SIMTEMP_FLAG_THR_EDGE) or above_threshold
        self.work_area.set_threshold_indicator(is_alert)

    def closeEvent(self, event) -> None:
        self._stream_worker.stop_stream()
        try:
            self.temperature.stop()
        except SimTempError:
            pass
        self.temperature.close()
        self.work_area.set_threshold_indicator(False)
        super().closeEvent(event)
