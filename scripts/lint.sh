#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS=0

log() {
	printf '[lint] %s\n' "$*"
}

lint_python() {
	if command -v python3 >/dev/null 2>&1; then
		log "Compiling Python sources"
		if ! python3 -m compileall "${ROOT_DIR}/main.py" "${ROOT_DIR}/API"; then
			log "Python byte-compilation failed"
			STATUS=1
		fi
	else
		log "python3 not found; skipping Python checks"
	fi
}

lint_shell() {
	local shells=(scripts/*.sh kernel/scripts/*.sh)
	for script in "${shells[@]}"; do
		[[ -f "$script" ]] || continue
		if ! bash -n "$script"; then
			log "bash -n failed for $script"
			STATUS=1
		fi
	done

	if command -v shellcheck >/dev/null 2>&1; then
		log "Running shellcheck"
		if ! shellcheck "${shells[@]}" 2>/dev/null; then
			log "shellcheck reported issues"
			STATUS=1
		fi
	else
		log "shellcheck not found; skipping advanced shell lint"
	fi
}

lint_headers() {
	local headers
	headers=()
	while IFS= read -r -d '' file; do
		headers+=("$file")
	done < <(find "${ROOT_DIR}/kernel" -name '*.c' -o -name '*.h' -print0)

	if command -v clang-format >/dev/null 2>&1; then
		log "Checking kernel sources with clang-format (dry run)"
		for file in "${headers[@]}"; do
			if ! diff -u "$file" <(clang-format "$file") >/dev/null 2>&1; then
				log "clang-format suggests updates for $file"
				STATUS=1
			fi
		done
	else
		log "clang-format not found; skipping C style check"
	fi
}

lint_python
lint_shell
lint_headers

if [[ "$STATUS" -eq 0 ]]; then
	log "All checks passed"
else
	log "Lint detected issues"
fi

exit "$STATUS"
