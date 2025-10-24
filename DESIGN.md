# System Design — pyAPITemp / nxp_simtemp

## 1. Solution Overview
pyAPITemp delivers a full-stack demo that spans a Linux kernel driver (`nxp_simtemp`), a command-line control utility, and a PySide6 desktop GUI. The driver simulates a temperature sensor with configurable sampling behaviour, while user-space applications consume the binary data stream, visualise readings, and automate regression tests.

```
 +-----------------------------+       +------------------------------+
 | PySide6 GUI (pyAPITemp)     | <---> | CLI Driver Wrapper (apitest) |
 +-------------+---------------+       +------------+-----------------+
               |                                         ^
               v                                         |
        +------+-------------------------------+         |
        | /dev/nxp_simtemp (miscdevice node)   |---------+
        +------+-------------------------------+
               |
               v
        +------+-------------------------------+
        | nxp_simtemp kernel module            |
        |  - hrtimer based sampler             |
        |  - ring buffer & wait queue          |
        |  - sysfs + ioctl control plane       |
        |  - DT overlay / ACPI stub support    |
        +------+-------------------------------+
               |
               v
        +------+-------------------------------+
        | Raspberry Pi 64-bit kernel (6.12.47) |
        +--------------------------------------+
```

## 2. Component Summary
| Component | Responsibility | Key Files |
|-----------|----------------|-----------|
| Kernel driver (`nxp_simtemp`) | Produce simulated samples, expose sysfs/ioctl settings, support DT / ACPI probe paths. | `kernel/core/*.c`, `kernel/include/*.h`, `kernel/nxp-simtemp-overlay.dts` |
| User CLI (`apitest`) | Simple runner for ioctl + regression, now featuring `--test` self-check. | `kernel/apitest/apitest.c` |
| GUI (`pyAPITemp`) | PySide6 interface for live graphs, configuration, alarms. | `main.py`, `API/**` |
| Automation scripts | Build, demo, packaging, permissions, lint helpers. | `scripts/*.sh`, `kernel/scripts/run_selftest.sh`, `scripts/create_simtemp_rpi_package.sh` |

## 3. Kernel Driver Architecture
### 3.1 Subsystems
- **Platform driver + Device Tree overlay**: `nxp-simtemp-overlay.dts` binds `compatible = "nxp,simtemp"` to instantiate the device. X86 testing reuses `simtemp_pdev_stub.ko`.
- **Sampling core**: `hrtimer` fires every `sampling_ms` ms, producing `simtemp_sample_v1` records with timestamp, milli-degree temperature, and flag bits (OK, threshold, overflow, one-shot done).
- **Ring buffer**: SPSC queue (`simtemp_ringbuf`) with overwrite-oldest policy tracks pending samples; wait-queue awakens readers.
- **Sysfs attributes**: `sampling_ms`, `threshold_mC`, `mode` (normal/noisy/ramp), `operation_mode` (continuous/one-shot), `state`, `stats`.
- **IOCTL interface**: Start/stop, get/set mode/period/threshold exposed via `_IO/_IOR/_IOW` macros (see `kernel/include/uapi/simtemp_uapi.h`).
- **Alert path**: Threshold crossing sets sticky `POLLPRI`, increments counters, and clears once user-space drains the queue.

### 3.2 Concurrency & State
- `hrtimer` callback operates under softirq context; writes to ring buffer under spin lock.
- Readers block on `wait_event_interruptible`; `poll()` supports `POLLIN|POLLPRI|POLLHUP`.
- Period and mode changes require the sampler to be stopped (`-EBUSY` guard).
- Safe unload cancels the timer, removes sysfs groups, deregisters miscdevice.

## 4. User-Space Architecture
### 4.1 PySide6 GUI
- Launch path: `main.py` → `API.main_window.MainWindow`.
- Uses `API/src/TempSensor.py` to interact with `SimTempDriver` (Python wrapper around CLI driver library).
- Features: live chart (continuous mode), one-shot capture, configuration panels, CSV export, threshold highlight.

### 4.2 CLI Utility (`apitest`)
- Compiled via `make apitest` or automatically through `kernel/scripts/run_selftest.sh`.
- Commands: `start`, `stop`, `read N`, `set/get_period`, `set/get_threshold`, `set/get_mode`, `--test`.
- `--test` flow: store current config, set 100 ms period + 1°C threshold, start sampler, poll for alerts, read sample, verify `SIMTEMP_FLAG_THR_EDGE`, restore configuration, emit PASS/FAIL.

## 5. Build & Deployment Flow
1. **Build helpers**: `scripts/build.sh` compiles module + overlay + CLI (native or cross). `make` inside `kernel/` already ensures `.dtbo` is in sync.
2. **Self-test**: `kernel/scripts/run_selftest.sh` rebuilds overlay/CLI if necessary, refreshes `/boot/overlays/simtemp.dtbo`, optionally applies overlay (if not already in `config.txt`), insmods the module, runs `apitest --test`, captures stats, and unloads.
3. **Packaging**: `scripts/create_simtemp_rpi_package.sh` consumes prebuilt `.ko/.dtbo` and GUI assets to produce a tarball with install/uninstall scripts, permission helper, and GUI launcher.
4. **Permissions**: `scripts/setup_simtemp_permissions.sh` (invoked by installer and standalone) sets udev rules, group membership, and sysfs mode to allow non-root interactions.

## 6. Interfaces & Contracts
| Interface | Description | Guarantee |
|-----------|-------------|-----------|
| `/dev/nxp_simtemp` | Blocking/non-blocking read of `struct simtemp_sample_v1` streams. | Atomic multiple-of-struct reads; errors for short buffers. |
| Sysfs (`/sys/class/misc/nxp_simtemp/`) | Control plane for state, operation mode, simulation mode, sampling period, threshold, stats. | Values validated (period 5–5000 ms, threshold 0–150000 mC). |
| IOCTL (`SIMTEMP_IOC_*`) | Start/stop sampler, get/set config. | `-EBUSY` when changing mode while running; returns `-EINVAL` for invalid options. |
| DT overlay (`simtemp.dtbo`) | Declares defaults: `sampling-ms`, `threshold-mC`, optional `operation-mode`. | Module logs chosen values; gracefully ignores out-of-range properties. |
| CLI `--test` | Regression check for threshold alerts. | Fails with non-zero status if alert bit not observed within 4 samples. |

## 7. Tooling & Automation
| Script | Purpose |
|--------|---------|
| `scripts/build.sh` | One-stop build entry point (native/cross). |
| `scripts/run_demo.sh` | Build (optional) + automated self-test for demo readiness. |
| `scripts/lint.sh` | Quick static checks (Python compile, shell syntax, optional `shellcheck`/`clang-format`). |
| `kernel/scripts/run_selftest.sh` | RasPi automation for overlay refresh, module load, CLI test, cleanup. |
| `scripts/create_simtemp_rpi_package.sh` | Produce redistributable tarball with install/uninstall + GUI. |

## 8. Related Documentation
- `kernel/docs/Requirements/Requirements.md` — detailed requirements & acceptance criteria.
- `kernel/docs/MSD_SimTemp.md` — in-depth module design (ring buffer, state machine, ABI).
- `kernel/docs/MTS_SimTemp.md` — historical module test specification.
- `kernel/docs/User Cases/nxp_simtemp_usecases.md` — workflow scenarios.
- `TESTPLAN.md` — current consolidated test plan (see repository root).
