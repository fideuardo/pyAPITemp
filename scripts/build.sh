#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage: build.sh [options]

Build the simtemp kernel module, overlay, and user-space utilities.

Options:
  --target <native|rpi>    Select build target (default: native).
  --kdir <path>            Kernel build directory for cross builds.
  --cross-prefix <prefix>  Cross-compiler prefix (e.g. aarch64-linux-gnu-).
  --clean                  Run "make clean" before building.
  -h, --help               Show this help and exit.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="native"
KDIR=""
CROSS_PREFIX=""
DO_CLEAN=false

while [[ $# -gt 0 ]]; do
	case "$1" in
		--target)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			TARGET="$2"
			shift 2
			;;
		--kdir)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			KDIR="$2"
			shift 2
			;;
		--cross-prefix)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			CROSS_PREFIX="$2"
			shift 2
			;;
		--clean)
			DO_CLEAN=true
			shift
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

pushd "${ROOT_DIR}/kernel" >/dev/null

if [[ "${DO_CLEAN}" == true ]]; then
	echo "[build] Cleaning previous artifacts"
	make clean
fi

case "${TARGET}" in
	native)
		echo "[build] Building for native host"
		make
		;;
	rpi)
		[[ -n "${KDIR}" ]] || { echo "[build] --kdir is required for --target rpi" >&2; exit 1; }
		echo "[build] Building for Raspberry Pi kernel at ${KDIR}"
		if [[ -n "${CROSS_PREFIX}" ]]; then
			make modules_rpi KDIR="${KDIR}" CROSS_COMPILE="${CROSS_PREFIX}"
		else
			make modules_rpi KDIR="${KDIR}"
		fi
		make apitest
		;;
	*)
		echo "[build] Unknown target: ${TARGET}" >&2
		exit 1
		;;
esac

popd >/dev/null
