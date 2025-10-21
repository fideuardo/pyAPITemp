"""High-level temperature sensor helper built on top of the SimTemp driver."""

from __future__ import annotations

from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Optional

from kernel.apitest.LxDrTemp import (
    OperationMode,
    SIMTEMP_FLAG_ONESHOT_DONE,
    SimTempDriver,
    SimTempError,
    SimTempNotAvailableError,
    SimTempSample,
    SimTempStats,
    SimTempTimeoutError,
    SimulationMode,
)

__all__ = ["TempSensor"]


class TempSensor:
    """Convenience wrapper that exposes one-shot and streaming reads."""

    def __init__(
        self,
        *,
        device_path: str | None = None,
        sysfs_base: str | None = None,
        auto_open: bool = False,
    ) -> None:
        self._ensure_driver_loaded()

        driver_kwargs = {}
        if device_path:
            driver_kwargs["device_path"] = device_path
        if sysfs_base:
            driver_kwargs["sysfs_base"] = sysfs_base

        self._driver = SimTempDriver(auto_open=auto_open, **driver_kwargs)
        self._info = {
            "name": "SimTempDriver",
            "description": "Simulated temperature sensor driver for Linux.",
        }

    def __enter__(self) -> "TempSensor":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    def driver(self) -> SimTempDriver:
        """Return the underlying low-level driver."""
        return self._driver

    @property
    def info(self) -> dict[str, str]:
        """Return metadata about the driver."""
        # Combine static info with dynamic version info from the driver.
        return {
            **self._info,
            "version": self._driver.get_driver_version(),
        }

    def open(self) -> None:
        """Open the underlying device if it is not already open."""
        self._driver.open()

    def close(self) -> None:
        """Close the underlying device descriptor."""
        self._driver.close()

    def read_once(self, *, timeout: float = 1.0) -> SimTempSample:
        """
        Perform a one-shot measurement and return the resulting sample.

        Raises:
            SimTempTimeoutError: if the measurement does not complete in time.
            SimTempError: for driver-level failures.
        """
        self._ensure_open()
        self._driver.stop()
        self._driver.set_operation_mode(OperationMode.ONE_SHOT)
        self._driver.start()
        try:
            sample = self._driver.read_sample(timeout=timeout)
        finally:
            # One-shot mode auto-stops but explicitly stopping guarantees a clean slate.
            try:
                self._driver.stop()
            except SimTempError:
                # Ignore stop failures so the original exception, if any, surfaces.
                pass

        if not sample.has_flag(SIMTEMP_FLAG_ONESHOT_DONE):
            raise SimTempError("one-shot measurement completed without DONE flag set")
        return sample

    def stream(
        self,
        *,
        limit: Optional[int] = None,
        timeout: float = 1.0,
    ) -> Generator[SimTempSample, None, None]:
        """
        Stream samples in continuous mode.

        Args:
            limit: Stop after yielding this many samples. None means no limit.
            timeout: Max seconds to wait for each sample.

        Yields:
            SimTempSample instances as they become available.

        Raises:
            SimTempTimeoutError: if waiting for a sample exceeds the timeout.
            SimTempError: for driver-level failures.
        """
        self._ensure_open()
        self._driver.stop()
        self._driver.set_operation_mode(OperationMode.CONTINUOUS)
        self._driver.start()
        yielded = 0
        try:
            while limit is None or yielded < limit:
                sample = self._driver.read_sample(timeout=timeout)
                yielded += 1
                yield sample
        finally:
            self._driver.stop()

    def iter_samples(
        self,
        count: int,
        *,
        timeout: float = 1.0,
    ) -> Iterable[SimTempSample]:
        """Convenience wrapper that collects a bounded number of samples."""
        if count <= 0:
            return []
        return list(self.stream(limit=count, timeout=timeout))

    def get_stats(self) -> SimTempStats:
        """Fetch statistics from sysfs."""
        self._ensure_open()
        return self._driver.read_stats()

    def set_simulation_mode(self, mode: SimulationMode | str) -> None:
        """Proxy to the driver for adjusting simulation characteristics."""
        self._ensure_open()
        self._driver.set_simulation_mode(mode)

    def set_sampling_period_ms(self, period_ms: int) -> None:
        """Adjust the continuous sampling period."""
        self._ensure_open()
        self._driver.set_sampling_period_ms(period_ms)

    def set_threshold_mc(self, threshold_mc: int) -> None:
        """Configure the temperature threshold for alert notifications."""
        self._ensure_open()
        self._driver.set_threshold_mc(threshold_mc)

    def _ensure_open(self) -> None:
        if not self._driver.is_open:
            self._driver.open()

    def _ensure_driver_loaded(self) -> None:
        """Validate that the simtemp kernel module is loaded before use."""
        modules_path = Path("/proc/modules")
        try:
            for line in modules_path.read_text(encoding="ascii").splitlines():
                if line.startswith("simtemp "):
                    return
        except OSError:
            # Fall back to deferring the error to the driver open call.
            return
        raise SimTempNotAvailableError("Kernel module 'simtemp' is not loaded.")
