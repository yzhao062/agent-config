#!/usr/bin/env bash
# Thin launcher for `prun_state.py report-state`.
#
# READ-ONLY. This command inspects unit directories and writes nothing. The
# separate entry point is the point: a reader auditing whether the reporter can
# mutate anything only has to read this file and the report path in
# prun_state.py.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Reject the Windows Store alias, which exits 9009 without running anything and
# is the failure recorded in AGENTS.md under Environment Notes.
_usable() {
    local candidate="$1"
    case "$candidate" in
        *WindowsApps*|*windowsapps*) return 1 ;;
    esac
    "$candidate" -I -c 'import sys; sys.exit(0)' >/dev/null 2>&1
}

resolve_python() {
    local explicit="${PRUN_PYTHON:-${ANYWHERE_AGENTS_PYTHON:-}}"
    if [ -n "$explicit" ]; then
        if _usable "$explicit"; then printf '%s\n' "$explicit"; return 0; fi
        printf 'report-state: PRUN_PYTHON/ANYWHERE_AGENTS_PYTHON is not usable: %s\n' \
            "$explicit" >&2
        return 1
    fi
    local candidate resolved
    for candidate in python3 python; do
        resolved="$(command -v "$candidate" 2>/dev/null || true)"
        [ -n "$resolved" ] || continue
        if _usable "$resolved"; then printf '%s\n' "$resolved"; return 0; fi
    done
    return 1
}

if ! python_bin="$(resolve_python)"; then
    printf 'report-state: no usable Python interpreter found. Set PRUN_PYTHON.\n' >&2
    exit 2
fi

exec "$python_bin" "$here/prun_state.py" report-state "$@"
