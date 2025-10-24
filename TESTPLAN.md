# Test Plan — pyAPITemp / nxp_simtemp

## 1. Scope
This plan covers verification for the simulated temperature sensor stack:
- Kernel module `nxp_simtemp` (Device Tree path and ACPI stub path).
- Command-line utility `apitest`.
- Automated self-test harness and packaging scripts.
- PySide6 GUI smoke tests (basic connectivity and controls).

It aligns with the functional requirements in `kernel/docs/Requirements/Requirements.md` and focuses on demonstrable acceptance criteria.

## 2. Test Environments
| Environment | Hardware | OS / Kernel | Notes |
|-------------|----------|-------------|-------|
| Raspberry Pi 4/5 | 64-bit SoC | `6.12.47+rpt-rpi-v8` + headers | Native target; Device Tree overlay required. |
| x86_64 dev host | Laptop/desktop | Ubuntu 22.04 LTS (`uname -r`) | Build host & self-test using ACPI stub. |

Required dependencies:
- `build-essential`, `linux-headers-$(uname -r)`, `libelf-dev`, `dtc`.
- Python 3.8+, PySide6, virtualenv.
- Optional: `shellcheck`, `clang-format`, `python3-venv`.

## 3. Test Artifacts & Tools
| Artifact | Command |
|----------|---------|
| Build helper | `scripts/build.sh [--target rpi --kdir <path>]` |
| Automated demo | `scripts/run_demo.sh` (calls build + kernel self-test) |
| Kernel self-test | `kernel/scripts/run_selftest.sh` |
| CLI regression | `kernel/apitest/apitest --test` |
| Lint suite | `scripts/lint.sh` |
| Packaging | `scripts/create_simtemp_rpi_package.sh` |
| Permission setup | `scripts/setup_simtemp_permissions.sh` |

## 4. Test Matrix
### 4.1 Functional Tests
| ID | Requirement | Procedure | Expected Result | Tool |
|----|-------------|-----------|-----------------|------|
| FT-01 | RQ-CTRL-01, RQ-TIME-01 | Load module; write valid/invalid values to `sampling_ms`, `threshold_mC`, `mode`, `operation_mode`. | Valid writes succeed and persist; invalid writes return `-EINVAL`; busy rejects while running. | Manual shell, `apitest` |
| FT-02 | RQ-DATA-01 | Start sampler, `dd` or `apitest read`, inspect sample size. | Reads multiples of 16 bytes, data includes timestamp/temp/flags. | Shell / CLI |
| FT-03 | RQ-EVT-01 | Run `apitest --test` or custom script with `poll()`. | `POLLIN` for new samples, `POLLPRI` on threshold crossing. | `apitest`, `kernel/scripts/run_selftest.sh` |
| FT-04 | RQ-THR-01 | Set threshold just below ambient; inspect sample flags. | `SIMTEMP_FLAG_THR_EDGE` set when threshold breached. | CLI |
| FT-05 | RQ-MODE-01 | Switch `mode` between normal/noisy/ramp; observe generated trend. | Temperature sequence matches mode semantics. | CLI/GUI |
| FT-06 | RQ-STATE-01 | `cat stats` before/after sampling; verify counters. | Counters increment for samples, alerts, overflow flags. | Shell |
| FT-07 | RQ-DT-01 | Deploy overlay (`make dtbo`, copy to `/boot/overlays/`, apply). | Probe succeeds, defaults follow DT values (logged in dmesg). | `kernel/scripts/run_selftest.sh` |
| FT-08 | RQ-SAFE-01 | `rmmod simtemp` while running and after stop. | No kernel warnings, resources freed. | Shell, `dmesg` |
| FT-09 | RQ-CLI-01 | Use CLI to configure, read sample list with timestamps. | Command output matches configuration. | `apitest` |
| FT-10 | RQ-CLI-02 | Execute `apitest --test`. | PASS message, exit code 0 when alert flagged; non-zero on failure. | `apitest` |

### 4.2 Automation & Scripts
| ID | Requirement | Procedure | Expected Result |
|----|-------------|-----------|-----------------|
| AT-01 | RQ-SCR-01 | Run `scripts/build.sh` (native & `--target rpi`). | Modules, overlay, CLI built; cross build uses provided `--kdir`. |
| AT-02 | RQ-SCR-01 | Run `scripts/run_demo.sh`. | Builds (unless skipped) and executes kernel self-test end-to-end. |
| AT-03 | RQ-SCR-01 | Run `scripts/lint.sh`. | Python compilation plus shell lint; zero exit on clean run. |
| AT-04 | Packaging | Run `scripts/create_simtemp_rpi_package.sh`. | Tarball containing ko/dtbo/GUI/install scripts produced in `dist/`. |
| AT-05 | Permissions | Run `scripts/setup_simtemp_permissions.sh`. | Udev rule installed; group membership updated; sysfs nodes accessible. |

### 4.3 GUI Smoke Tests
| ID | Requirement | Procedure | Expected Result |
|----|-------------|-----------|-----------------|
| GT-01 | GUI connectivity | Load module; run GUI; switch to continuous mode. | Chart updates with sample stream; no errors in console. |
| GT-02 | GUI configuration | Use GUI controls to change sampling period, mode, threshold. | Sysfs values reflect changes; alerts highlighted. |
| GT-03 | GUI one-shot | Select one-shot mode and trigger measurement. | Single reading appears; driver stops afterwards. |

## 5. Execution Guidance
1. **Environment prep**: Ensure overlay is in `/boot/overlays/` and `dtoverlay=simtemp` is set (or allow `run_selftest.sh` to apply it temporarily). Install build prerequisites and Python dependencies.
2. **Build**: `scripts/build.sh [--target rpi --kdir <kernel_build>]`.
3. **Automation smoke**: `scripts/run_demo.sh` (verifies threshold alert path). Capture console output.
4. **Manual deep tests**: Follow FT table for specific sysfs/ioctl behaviours, verify `dmesg` after each scenario.
5. **GUI**: Activate Python virtualenv, launch `python main.py`, perform GT tests.
6. **Packaging**: Run packaging script and validate resulting tarball on target device.

Artifacts to collect:
- Console logs (`run_demo.sh`, `apitest --test`).
- `dmesg` snippets for driver load/unload.
- Screenshots or recordings for GUI verification (optional for video requirement).

## 6. Reporting & Exit Criteria
- Each test case must be marked PASS/FAIL with evidence (command output, dmesg logs, screenshots).
- Blocking defects: kernel warnings/oops, CLI self-test failure, overlay/apply failure, inability to configure driver via sysfs/GUI.
- QA exit criteria: all FT and AT tests pass on Raspberry Pi; CLI self-test integrated in automation; GUI smoke passes; packaging tested on target once per release candidate.

## 7. Traceability Reference
- Requirements cross-check: see matrix in `kernel/docs/Requirements/Requirements.md` and the functional coverage table above.
- Detailed historical MTS document: `kernel/docs/MTS_SimTemp.md`.
- Recorded automation and environment instructions duplicated in `kernel/README.md` and packaging README.

## 8. Test Evidence Summary
Recent execution logs captured during development (see session transcripts) include:
- **Kernel build outputs** showing successful compilation of `simtemp.ko`, `simtemp_pdev_stub.ko`, and `simtemp.dtbo` via `make` on Raspberry Pi (`6.12.47+rpt-rpi-v8`).
- **Self-test harness** runs (`kernel/scripts/run_selftest.sh`) demonstrating overlay refresh, module load, `apitest --test` PASS results, stats reporting, and clean unload.
- **Manual CLI tests** on the Pi (`apitest /dev/nxp_simtemp --test`) confirming threshold alerts (`flags=0x00020001`).
- **Automation script packaging** logs (`scripts/create_simtemp_rpi_package.sh`) verifying installer/uninstaller generation.
- **Overlay application diagnostics** (dtoverlay success/failure messages) validating handling for pre-configured overlays.

These logs serve as evidence for FT-02/03/04/08/10 and AT-01/02/03 coverage. Additional screenshots or dmesg snippets should be archived alongside release notes when preparing for formal review.
