# pyAPITemp

**pyAPITemp** is an instrument control panel developed in Python with PySide6. This graphical user interface lets you interact in real time with the `simtemp` Linux kernel driver, a simulated temperature sensor.

The project demonstrates a full vertical integration, from the low-level kernel driver to a modern desktop application.

## Features

- **Graphical Control Panel:** An intuitive interface to configure and visualize sensor data.
- **Continuous Mode:** Displays real-time data on a chart and a list of recent readings.
- **One-Shot Mode:** Performs a single temperature reading on demand.
- **Dynamic Configuration:** Allows real-time adjustment of driver parameters such as:
    - Sampling period.
    - Simulation mode (`normal`, `noisy`, `ramp`).
    - Temperature threshold for alerts.
- **Visual Alerts:** The chart and the list of readings highlight when the temperature exceeds the configured threshold.
- **Data Saving:** Option to save temperature samples to a CSV file.

## Prerequisites

Before you begin, ensure you have the following software installed on your Linux system:

- **Python 3.8+** and `pip`.
- **Build tools** for kernel modules:
  ```bash
  sudo apt update
  sudo apt install build-essential linux-headers-$(uname -r) libelf-dev dkms
  ```
- **PySide6:** the GUI toolkit used by the application.

## Installation

The installation is divided into two parts: building and loading the kernel module, and configuring the Python environment.

### 1. Kernel Module (`simtemp`)

First, compile the driver.

```bash
# 1. Navega al directorio del kernel
cd kernel/

# 2. Compila el driver y el Device Tree Overlay
make
```

This produces the files `simtemp.ko` (the driver) and `simtemp.dtbo` (the device-tree overlay for boards such as the Raspberry Pi).

### 2. Python Application

Using a virtual environment for Python dependencies is recommended.

```bash
# 1. Create a virtual environment in the project root directory
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install the required dependencies
pip install PySide6
```

## Usage

To run the application, load the kernel module first and then start the GUI.

### 1. Load the Kernel Module

How you load the driver depends on your platform.

**Option A: Systems with Device Tree (e.g., Raspberry Pi)**

```bash
# Load the Device Tree overlay and then the module
sudo dtoverlay simtemp.dtbo
sudo insmod kernel/simtemp.ko
```

**Option B: x86/ACPI systems (without Device Tree)**

An auxiliary module is required to register the device.

```bash
# Carga primero el stub que simula el platform device
sudo insmod kernel/simtemp_pdev_stub.ko

# Luego, carga el driver principal
sudo insmod kernel/simtemp.ko
```

**Verification:** After loading the module, you should see the device node:
`ls -l /dev/nxp_simtemp`

### 2. Start the GUI

With the virtual environment active and the driver loaded, run the application:

```bash
python main.py
```

That’s it! The temperature control panel should now be on your screen.
