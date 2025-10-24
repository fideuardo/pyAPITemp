#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage: create_simtemp_rpi_package.sh [options]

Assembles the prebuilt simtemp kernel module and overlay into a tarball
ready to install on a Raspberry Pi.

Options:
  --kernel-version <ver>   Kernel release the module was compiled against
                           (default: 6.12.47+rpt-rpi-v8).
  --kofile-archive <path>  Path to archive with simtemp artifacts
                           (default: ../input/kofiles.tar.gz).
  --output <path>          Path to output tar.gz (default: ../dist/simtemp-rpi-<ver>.tar.gz).
  -h, --help               Show this message.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_KERNEL_VERSION="6.12.47+rpt-rpi-v8"
KERNEL_VERSION="$DEFAULT_KERNEL_VERSION"
SRC_ARCHIVE="${ROOT_DIR}/input/kofiles.tar.gz"
OUT_DIR="${ROOT_DIR}/dist"
OUTPUT_TAR=""

while [[ $# -gt 0 ]]; do
	case "$1" in
		--kernel-version)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			KERNEL_VERSION="$2"
			shift 2
			;;
		--kofile-archive)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			SRC_ARCHIVE="$(realpath "$2")"
			shift 2
			;;
		--output)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			OUTPUT_TAR="$(realpath "$2")"
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 1
			;;
	esac
done

[[ -f "$SRC_ARCHIVE" ]] || { echo "Archive not found: $SRC_ARCHIVE" >&2; exit 1; }
PACKAGE_NAME="simtemp-rpi-${KERNEL_VERSION}"
[[ -n "$OUTPUT_TAR" ]] || OUTPUT_TAR="${OUT_DIR}/${PACKAGE_NAME}.tar.gz"
mkdir -p "$(dirname "$OUTPUT_TAR")"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

tar -xzf "$SRC_ARCHIVE" -C "$tmpdir"
if [[ -d "${tmpdir}/kofiles" ]]; then
	kofiles_dir="${tmpdir}/kofiles"
else
	kofiles_dir="$tmpdir"
fi

module_path="${kofiles_dir}/simtemp.ko"
dtbo_path="${kofiles_dir}/simtemp.dtbo"
stub_module_path="${kofiles_dir}/simtemp_pdev_stub.ko"

[[ -f "$module_path" ]] || { echo "Missing simtemp.ko in archive" >&2; exit 1; }
[[ -f "$dtbo_path" ]] || { echo "Missing simtemp.dtbo in archive" >&2; exit 1; }

pkg_root="${tmpdir}/${PACKAGE_NAME}"
module_dest="${pkg_root}/lib/modules/${KERNEL_VERSION}/extra"
dtbo_dest="${pkg_root}/boot/overlays"
extras_dest="${pkg_root}/opt/simtemp"
app_dest="${pkg_root}/opt/simtemp-ui"
scripts_dest="${pkg_root}/scripts"
mkdir -p "$module_dest" "$dtbo_dest" "$extras_dest" "$app_dest" "$scripts_dest"

cp "$module_path" "${module_dest}/simtemp.ko"
cp "$dtbo_path" "${dtbo_dest}/simtemp.dtbo"
if [[ -f "$stub_module_path" ]]; then
	cp "$stub_module_path" "${extras_dest}/simtemp_pdev_stub.ko"
fi

cp "${ROOT_DIR}/main.py" "$app_dest/"
cp "${ROOT_DIR}/requirements.txt" "$app_dest/"
cp -r "${ROOT_DIR}/API" "$app_dest/"
mkdir -p "$app_dest/kernel"
cp -r "${ROOT_DIR}/kernel/apitest" "$app_dest/kernel/"
touch "$app_dest/kernel/__init__.py"
touch "$app_dest/kernel/apitest/__init__.py"
cp "${ROOT_DIR}/scripts/setup_simtemp_permissions.sh" "${scripts_dest}/"
chmod +x "${scripts_dest}/setup_simtemp_permissions.sh"
find "$app_dest" -name '__pycache__' -type d -prune -exec rm -rf {} +

cat > "${pkg_root}/install.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail

DEFAULT_KERNEL_VERSION="${KERNEL_VERSION}"
TARGET_KERNEL="\${1:-\${DEFAULT_KERNEL_VERSION}}"

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
MODULE_SRC="\${SCRIPT_DIR}/lib/modules/\${TARGET_KERNEL}/extra/simtemp.ko"
DTBO_SRC="\${SCRIPT_DIR}/boot/overlays/simtemp.dtbo"
STUB_SRC="\${SCRIPT_DIR}/opt/simtemp/simtemp_pdev_stub.ko"

MODULE_DEST="/lib/modules/\${TARGET_KERNEL}/extra"
DTBO_DEST="/boot/overlays"
STUB_DEST="/usr/lib/simtemp"

if [[ "\$EUID" -ne 0 ]]; then
	echo "Please run this script with sudo (root privileges required)." >&2
	exit 1
fi

install -d "\${MODULE_DEST}" "\${DTBO_DEST}" "\${STUB_DEST}"
install -m 644 "\${MODULE_SRC}" "\${MODULE_DEST}/simtemp.ko"
install -m 644 "\${DTBO_SRC}" "\${DTBO_DEST}/simtemp.dtbo"

if [[ -f "\${STUB_SRC}" ]]; then
	install -m 644 "\${STUB_SRC}" "\${STUB_DEST}/simtemp_pdev_stub.ko"
fi

APP_SRC="\${SCRIPT_DIR}/opt/simtemp-ui"
APP_DEST="/opt/simtemp-ui"
LAUNCHER_PATH="/usr/local/bin/API_SimTemp"

if [[ ! -d "\${APP_SRC}" ]]; then
	echo "Application sources missing inside the package." >&2
	exit 1
fi

rm -rf "\${APP_DEST}"
install -d "\${APP_DEST}"
cp -r "\${APP_SRC}/." "\${APP_DEST}/"

PYTHON_BIN="\$(command -v python3 || true)"
if [[ -z "\${PYTHON_BIN}" ]]; then
	echo "python3 not found. Please install python3 before running this installer." >&2
	exit 1
fi

if ! "\${PYTHON_BIN}" -m venv "\${APP_DEST}/.venv"; then
	echo "Failed to create Python virtual environment. Install python3-venv and retry." >&2
	exit 1
fi

"\${APP_DEST}/.venv/bin/pip" install --upgrade pip
"\${APP_DEST}/.venv/bin/pip" install -r "\${APP_DEST}/requirements.txt"

PERM_SCRIPT="\${SCRIPT_DIR}/scripts/setup_simtemp_permissions.sh"
PERM_GROUP="\${SIMTEMP_GROUP:-plugdev}"
PERM_USER="\${SIMTEMP_USER:-\${SUDO_USER:-}}"
if [[ -x "\${PERM_SCRIPT}" ]]; then
	SIMTEMP_PROJECT_ROOT="\${APP_DEST}" SIMTEMP_GROUP="\${PERM_GROUP}" SIMTEMP_USER="\${PERM_USER}" bash "\${PERM_SCRIPT}"
else
	echo "WARNING: Permission setup script missing; adjust sysfs permissions manually." >&2
fi

cat > "\${LAUNCHER_PATH}" <<'LAUNCHER'
#!/usr/bin/env bash
APP_HOME="/opt/simtemp-ui"
VENV_PY="\${APP_HOME}/.venv/bin/python"
if [[ ! -x "\${VENV_PY}" ]]; then
	echo "simtemp UI virtualenv missing. Re-run install.sh." >&2
	exit 1
fi
exec "\${VENV_PY}" "\${APP_HOME}/main.py" "\$@"
LAUNCHER
chmod +x "\${LAUNCHER_PATH}"

BOOT_CONFIG=""
if [[ -f /boot/firmware/config.txt ]]; then
	BOOT_CONFIG=/boot/firmware/config.txt
elif [[ -f /boot/config.txt ]]; then
	BOOT_CONFIG=/boot/config.txt
fi

if [[ -n "\${BOOT_CONFIG}" ]]; then
	if ! grep -Eq '^[[:space:]]*dtoverlay=simtemp([[:space:]]|\$)' "\${BOOT_CONFIG}"; then
		echo "dtoverlay=simtemp" >> "\${BOOT_CONFIG}"
		echo "Added dtoverlay=simtemp to \${BOOT_CONFIG}."
	else
		echo "dtoverlay=simtemp already present in \${BOOT_CONFIG}."
	fi
else
	echo "WARNING: Could not find /boot/config.txt or /boot/firmware/config.txt to persist overlay." >&2
fi

depmod "\${TARGET_KERNEL}"

cat <<'MSG'
Installation complete.

To load the overlay (if not already active):
  sudo dtoverlay simtemp

To insert the kernel module:
  sudo insmod /lib/modules/\$(uname -r)/extra/simtemp.ko

If you require the ACPI stub (mostly x86 only), it was installed at /usr/lib/simtemp/simtemp_pdev_stub.ko.
To launch the GUI:
  API_SimTemp
To uninstall later, run sudo ./uninstall.sh [kernel-version]
MSG
EOF
chmod +x "${pkg_root}/install.sh"

cat > "${pkg_root}/uninstall.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail

DEFAULT_KERNEL_VERSION="${KERNEL_VERSION}"
TARGET_KERNEL="\${1:-\${DEFAULT_KERNEL_VERSION}}"

MODULE_DEST="/lib/modules/\${TARGET_KERNEL}/extra/simtemp.ko"
DTBO_DEST="/boot/overlays/simtemp.dtbo"
STUB_PATH="/usr/lib/simtemp/simtemp_pdev_stub.ko"
APP_DEST="/opt/simtemp-ui"
LAUNCHER_PATH="/usr/local/bin/API_SimTemp"

if [[ "\$EUID" -ne 0 ]]; then
	echo "Please run this script with sudo (root privileges required)." >&2
	exit 1
fi

modprobe -r simtemp 2>/dev/null || true
modprobe -r simtemp_pdev_stub 2>/dev/null || true

rm -f "\${MODULE_DEST}"
rm -f "\${DTBO_DEST}"
rm -f "\${STUB_PATH}"
rm -f "\${LAUNCHER_PATH}"
rm -rf "\${APP_DEST}"

rmdir --ignore-fail-on-non-empty /usr/lib/simtemp 2>/dev/null || true
rmdir --ignore-fail-on-non-empty "/lib/modules/\${TARGET_KERNEL}/extra" 2>/dev/null || true

UDEV_RULE="/etc/udev/rules.d/99-nxp-simtemp.rules"
if [[ -f "\${UDEV_RULE}" ]]; then
	rm -f "\${UDEV_RULE}"
	udevadm control --reload || true
	udevadm trigger --subsystem-match=misc --attr-match=name=nxp_simtemp || true
fi

BOOT_CONFIG=""
if [[ -f /boot/firmware/config.txt ]]; then
	BOOT_CONFIG=/boot/firmware/config.txt
elif [[ -f /boot/config.txt ]]; then
	BOOT_CONFIG=/boot/config.txt
fi

if [[ -n "\${BOOT_CONFIG}" ]]; then
	sed -i '/^[[:space:]]*dtoverlay=simtemp$/d' "\${BOOT_CONFIG}"
fi

depmod "\${TARGET_KERNEL}"

echo "simtemp files removed for kernel \${TARGET_KERNEL}."
EOF
chmod +x "${pkg_root}/uninstall.sh"

cat > "${pkg_root}/README.txt" <<EOF
simtemp kernel module package for Raspberry Pi

Contents:
  - lib/modules/${KERNEL_VERSION}/extra/simtemp.ko
  - boot/overlays/simtemp.dtbo
  - opt/simtemp-ui/* (Python GUI sources and requirements)
  - opt/simtemp/simtemp_pdev_stub.ko (optional stub for non-Device Tree systems)
  - scripts/setup_simtemp_permissions.sh (applied during install)
  - install.sh helper script
  - uninstall.sh helper script

Usage:
  1. Copy ${PACKAGE_NAME}.tar.gz to the Raspberry Pi.
  2. On the Raspberry Pi, extract it: tar -xzf ${PACKAGE_NAME}.tar.gz
  3. Run sudo ./${PACKAGE_NAME}/install.sh
     (you may pass a kernel version as the first argument if different from ${KERNEL_VERSION})
  4. The script ensures dtoverlay=simtemp is present in the Raspberry Pi boot config so it loads on boot.
  5. Launch the GUI afterwards with API_SimTemp.
  6. To remove the installation, run sudo ./${PACKAGE_NAME}/uninstall.sh [kernel-version].
     (You may need to log out/in once so new group membership takes effect.)
EOF

(cd "$tmpdir" && tar -czf "$OUTPUT_TAR" "$PACKAGE_NAME")
echo "Created package: $OUTPUT_TAR"
