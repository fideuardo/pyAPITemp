#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage: run_demo.sh [options]

Build the project (unless skipped) and execute the automated kernel demo.

Options:
  --skip-build             Do not invoke build.sh before running the demo.
  --target <native|rpi>    Forwarded to build.sh (default: native).
  --kdir <path>            Forwarded to build.sh for cross builds.
  --cross-prefix <prefix>  Forwarded to build.sh for cross builds.
  -h, --help               Show this message and exit.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_BUILD=false
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
	case "$1" in
		--skip-build)
			SKIP_BUILD=true
			shift
			;;
		--target|--kdir|--cross-prefix)
			[[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
			BUILD_ARGS+=("$1" "$2")
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

if [[ "${SKIP_BUILD}" == false ]]; then
	echo "[demo] Building project"
	"${ROOT_DIR}/scripts/build.sh" "${BUILD_ARGS[@]}"
else
	echo "[demo] Skipping build step"
fi

echo "[demo] Running automated self-test"
"${ROOT_DIR}/kernel/scripts/run_selftest.sh"

echo "[demo] Demo completed. The module has been removed."
echo "[demo] To launch the GUI, reinstall using the packaged tarball or re-run the installer:"
echo "       sudo ./dist/simtemp-rpi-<version>/install.sh"
