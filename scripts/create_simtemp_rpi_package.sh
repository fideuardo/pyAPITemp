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
mkdir -p "$module_dest" "$dtbo_dest" "$extras_dest"

cp "$module_path" "${module_dest}/simtemp.ko"
cp "$dtbo_path" "${dtbo_dest}/simtemp.dtbo"
if [[ -f "$stub_module_path" ]]; then
	cp "$stub_module_path" "${extras_dest}/simtemp_pdev_stub.ko"
fi

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

depmod "\${TARGET_KERNEL}"

cat <<'MSG'
Installation complete.

To load the overlay (if not already active):
  sudo dtoverlay simtemp

To insert the kernel module:
  sudo insmod /lib/modules/$(uname -r)/extra/simtemp.ko

If you require the ACPI stub (mostly x86 only), it was installed at /usr/lib/simtemp/simtemp_pdev_stub.ko.
MSG
EOF
chmod +x "${pkg_root}/install.sh"

cat > "${pkg_root}/README.txt" <<EOF
simtemp kernel module package for Raspberry Pi

Contents:
  - lib/modules/${KERNEL_VERSION}/extra/simtemp.ko
  - boot/overlays/simtemp.dtbo
  - opt/simtemp/simtemp_pdev_stub.ko (optional stub for non-Device Tree systems)
  - install.sh helper script

Usage:
  1. Copy ${PACKAGE_NAME}.tar.gz to the Raspberry Pi.
  2. On the Raspberry Pi, extract it: tar -xzf ${PACKAGE_NAME}.tar.gz
  3. Run sudo ./${PACKAGE_NAME}/install.sh
     (you may pass a kernel version as the first argument if different from ${KERNEL_VERSION})
EOF

(cd "$tmpdir" && tar -czf "$OUTPUT_TAR" "$PACKAGE_NAME")
echo "Created package: $OUTPUT_TAR"
