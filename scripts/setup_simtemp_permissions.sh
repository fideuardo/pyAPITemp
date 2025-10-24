#!/usr/bin/env bash
# Configure permissions so the nxp_simtemp driver can be used without root.

set -euo pipefail

RULE_FILE="/etc/udev/rules.d/99-nxp-simtemp.rules"
TARGET_GROUP="${SIMTEMP_GROUP:-plugdev}"
TARGET_USER="${SIMTEMP_USER:-${SUDO_USER:-}}"
PROJECT_ROOT="${SIMTEMP_PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

log() {
    printf '[simtemp-setup] %s\n' "$*"
}

require_root() {
    if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
        echo "This script must be run with administrative privileges. Use: sudo $0" >&2
        exit 1
    fi
}

ensure_group() {
    if ! getent group "$TARGET_GROUP" >/dev/null; then
        log "Creating group '$TARGET_GROUP'"
        groupadd "$TARGET_GROUP"
    fi
}

ensure_user_in_group() {
    if [[ -z "$TARGET_USER" ]]; then
        log "Could not detect the user to add to group '$TARGET_GROUP'."
        log "Add it manually with: sudo usermod -a -G $TARGET_GROUP <user>"
        return
    fi
    if id -nG "$TARGET_USER" | tr ' ' '\n' | grep -qx "$TARGET_GROUP"; then
        log "User '$TARGET_USER' already belongs to group '$TARGET_GROUP'."
    else
        log "Adding user '$TARGET_USER' to group '$TARGET_GROUP'"
        usermod -a -G "$TARGET_GROUP" "$TARGET_USER"
        log "You must log out and back in for the group change to take effect."
    fi
}

install_udev_rule() {
    log "Instalando regla udev en $RULE_FILE"
    cat <<EOF >"$RULE_FILE"
SUBSYSTEM=="misc", KERNEL=="nxp_simtemp", GROUP="$TARGET_GROUP", MODE="0660"
SUBSYSTEM=="misc", KERNEL=="nxp_simtemp", ACTION=="add", RUN+="/bin/chgrp $TARGET_GROUP /sys/class/misc/nxp_simtemp"
SUBSYSTEM=="misc", KERNEL=="nxp_simtemp", ACTION=="add", RUN+="/bin/chmod 0755 /sys/class/misc/nxp_simtemp"
SUBSYSTEM=="misc", KERNEL=="nxp_simtemp", ACTION=="add", RUN+="/bin/sh -c 'for f in mode sampling_ms threshold_mC state operation_mode; do if [ -e /sys/class/misc/nxp_simtemp/\$f ]; then chgrp $TARGET_GROUP /sys/class/misc/nxp_simtemp/\$f; chmod 0660 /sys/class/misc/nxp_simtemp/\$f; fi; done'"
EOF
    chmod 644 "$RULE_FILE"
}

reload_udev() {
    log "Reloading udev rules"
    udevadm control --reload
    udevadm trigger --subsystem-match=misc --attr-match=name=nxp_simtemp || true
}

fix_existing_nodes() {
    local devices=(/dev/nxp_simtemp)
    local sysfs_dir="/sys/class/misc/nxp_simtemp"
    local sysfs_entries=(mode sampling_ms threshold_mC state operation_mode)

    for dev in "${devices[@]}"; do
        if [[ -e "$dev" ]]; then
            chgrp "$TARGET_GROUP" "$dev" || true
            chmod 0660 "$dev" || true
        fi
    done

    if [[ -d "$sysfs_dir" ]]; then
        chgrp "$TARGET_GROUP" "$sysfs_dir" || true
        chmod 0755 "$sysfs_dir" || true
        for entry in "${sysfs_entries[@]}"; do
            local path="$sysfs_dir/$entry"
            if [[ -e "$path" ]]; then
                chgrp "$TARGET_GROUP" "$path" || true
                chmod 0660 "$path" || true
            fi
        done
    fi
}

print_summary() {
    cat <<EOF
Done. If user '$TARGET_USER' was added to the '$TARGET_GROUP' group,
you will need to log out and log back in for the new permissions to take effect.

Afterward, you can run the UI without elevated privileges:

    cd "$PROJECT_ROOT"
    source .venv/bin/activate
    python main.py

EOF
}

main() {
    require_root
    ensure_group
    ensure_user_in_group
    install_udev_rule
    reload_udev
    fix_existing_nodes
    print_summary
}

main "$@"
