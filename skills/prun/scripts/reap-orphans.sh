#!/usr/bin/env bash
# reap-orphans.sh -- reap prun worker trees whose recorded dispatcher is gone.
#
# This tool acts by default because it replaces the unsafe practice of killing
# every process with a worker executable's name, which previously killed two
# live workers. A dry-run-only default would invite callers to bypass it again.
# Safety comes from the bounded target set: only PIDs read from prun state directories
# with dead dispatchers are eligible, and processes are never listed by name.
# This differs from guard.py, which requires human confirmation for arbitrary
# process-destruction commands because their affected set cannot be inferred
# from command text. Here the affected set is enumerable and test-covered.
#
# Usage: reap-orphans.sh [--dry-run] [--state-dir <path>]...
# Exit: 0 after classification/reaping, 2 on usage error.

set -u

DRY_RUN=0
EXPLICIT_STATE_DIRS=0
STATE_DIRS=()

_usage() {
    echo "Usage: reap-orphans.sh [--dry-run] [--state-dir <path>]..." >&2
}

_need_val() { [ "$1" -ge 2 ] || { echo "reap-orphans: $2 needs a value" >&2; _usage; exit 2; }; }
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --state-dir)
            _need_val "$#" --state-dir
            STATE_DIRS+=("$2")
            EXPLICIT_STATE_DIRS=1
            shift 2 ;;
        *)
            echo "reap-orphans: unknown argument: $1" >&2
            _usage
            exit 2 ;;
    esac
done

TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"

case "$(uname -s 2>/dev/null || true)" in
    MINGW*|MSYS*|CYGWIN*) REAPER_SCHEME="msys" ;;
    *) REAPER_SCHEME="posix" ;;
esac

CANDIDATES=()
if [ "$EXPLICIT_STATE_DIRS" -eq 1 ]; then
    for state_dir in ${STATE_DIRS[@]+"${STATE_DIRS[@]}"}; do
        CANDIDATES+=("$state_dir")
    done
else
    for state_dir in "$TMP_BASE"/prun-task-*; do
        [ -d "$state_dir" ] || continue
        CANDIDATES+=("$state_dir")
    done
fi

CANDIDATE_COUNT=0
for state_dir in ${CANDIDATES[@]+"${CANDIDATES[@]}"}; do
    CANDIDATE_COUNT=$((CANDIDATE_COUNT + 1))
done
printf 'REAP-START base=%s candidates=%s\n' "$TMP_BASE" "$CANDIDATE_COUNT"

_process_start() {
    local process_pid="$1"
    local proc_stat="/proc/$process_pid/stat"
    local proc_line proc_rest
    if [ -r "$proc_stat" ]; then
        proc_line="$(sed -n '1p' "$proc_stat" 2>/dev/null)"
        proc_rest="${proc_line##*)}"
        [ "$proc_rest" != "$proc_line" ] || return 0
        set -- $proc_rest
        [ "$#" -ge 20 ] || return 0
        shift 19
        case "$1" in ''|*[!0-9]*) return 0 ;; esac
        printf '%s\n' "$1"
        return 0
    fi
    ps -o lstart= -p "$process_pid" 2>/dev/null \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

_process_parent() {
    local process_pid="$1"
    local proc_stat="/proc/$process_pid/stat"
    local proc_line proc_rest
    if [ -r "$proc_stat" ]; then
        proc_line="$(sed -n '1p' "$proc_stat" 2>/dev/null)"
        proc_rest="${proc_line##*)}"
        [ "$proc_rest" != "$proc_line" ] || return 0
        set -- $proc_rest
        [ "$#" -ge 2 ] || return 0
        case "$2" in ''|*[!0-9]*) return 0 ;; esac
        printf '%s\n' "$2"
        return 0
    fi
    ps -o ppid= -p "$process_pid" 2>/dev/null | tr -d '[:space:]'
}

_process_state() {
    local process_pid="$1"
    local proc_stat="/proc/$process_pid/stat"
    local proc_line proc_rest
    if [ -r "$proc_stat" ]; then
        proc_line="$(sed -n '1p' "$proc_stat" 2>/dev/null)"
        proc_rest="${proc_line##*)}"
        [ "$proc_rest" != "$proc_line" ] || return 0
        set -- $proc_rest
        [ "$#" -ge 1 ] || return 0
        printf '%s\n' "$1"
        return 0
    fi
    ps -o stat= -p "$process_pid" 2>/dev/null \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]].*$//'
}

_process_group() {
    local process_pid="$1"
    local proc_stat="/proc/$process_pid/stat"
    local proc_line proc_rest process_group
    if [ -d /proc ]; then
        [ -r "$proc_stat" ] || return 0
        IFS= read -r proc_line < "$proc_stat" || return 0
        proc_rest="${proc_line##*)}"
        [ "$proc_rest" != "$proc_line" ] || return 0
        set -- $proc_rest
        [ "$#" -ge 3 ] || return 0
        process_group="$3"
    else
        process_group="$(ps -o pgid= -p "$process_pid" 2>/dev/null \
            | tr -d '[:space:]')"
    fi
    case "$process_group" in ''|*[!0-9]*) return 0 ;; esac
    printf '%s\n' "$process_group"
}

_group_members() {
    local expected_group="$1"
    local proc_stat proc_line proc_rest process_pid process_rows saw_proc=0
    if [ -d /proc ]; then
        for proc_stat in /proc/[0-9]*/stat; do
            [ -r "$proc_stat" ] || continue
            saw_proc=1
            IFS= read -r proc_line < "$proc_stat" || continue
            proc_rest="${proc_line##*)}"
            [ "$proc_rest" != "$proc_line" ] || continue
            set -- $proc_rest
            [ "$#" -ge 3 ] || continue
            [ "$3" = "$expected_group" ] || continue
            case "$1" in Z*) continue ;; esac
            process_pid="${proc_stat#/proc/}"
            process_pid="${process_pid%/stat}"
            printf '%s\n' "$process_pid"
        done
        [ "$saw_proc" -eq 1 ]
        return
    fi

    # macOS has no /proc. Its ps supports these fields; MSYS does not, so this
    # branch must remain restricted to platforms without /proc.
    process_rows="$(ps -axo pid=,pgid=,stat= 2>/dev/null)" || return 1
    printf '%s\n' "$process_rows" | awk -v group="$expected_group" \
        '$2 == group && $3 !~ /^Z/ { print $1 }'
}

_group_alive() {
    local expected_group="$1"
    local members
    members="$(_group_members "$expected_group")" || return 2
    [ -n "$members" ]
}

_wait_group_gone() {
    local expected_group="$1"
    local attempt=0 group_status
    while [ "$attempt" -lt 10 ]; do
        _group_alive "$expected_group"
        group_status=$?
        [ "$group_status" -eq 1 ] && return 0
        [ "$group_status" -eq 2 ] && return 2
        sleep 0.1
        attempt=$((attempt + 1))
    done
    _group_alive "$expected_group"
    group_status=$?
    [ "$group_status" -eq 1 ] && return 0
    [ "$group_status" -eq 2 ] && return 2
    return 1
}

_kill_descendants() {
    local parent="$1"
    local expected_start="$2"
    local expected_parent="$3"
    local signal_name="$4"
    local children child child_start child_parent current_parent

    _same_process "$parent" "$expected_start" || return 1
    if [ -n "$expected_parent" ]; then
        current_parent="$(_process_parent "$parent")"
        [ "$current_parent" = "$expected_parent" ] || return 1
    fi

    children="$(pgrep -P "$parent" 2>/dev/null || true)"
    for child in $children; do
        child_start="$(_process_start "$child")"
        child_parent="$(_process_parent "$child")"
        [ -n "$child_start" ] && [ "$child_parent" = "$parent" ] || continue
        _kill_descendants "$child" "$child_start" "$parent" "$signal_name" || true
    done

    # Descendant identities are not stored in the state directory. Capturing
    # start time and parentage here narrows PID-reuse exposure, but POSIX has no
    # retained process handle that can close the final check-to-signal race.
    _same_process "$parent" "$expected_start" || return 1
    if [ -n "$expected_parent" ]; then
        current_parent="$(_process_parent "$parent")"
        [ "$current_parent" = "$expected_parent" ] || return 1
    fi
    kill "-$signal_name" "$parent" 2>/dev/null
}

_same_process() {
    local expected_pid="$1"
    local expected_start="$2"
    local current_start
    current_start="$(_process_start "$expected_pid")"
    [ -n "$current_start" ] && [ "$current_start" = "$expected_start" ]
}

_original_gone() {
    local expected_pid="$1"
    local expected_start="$2"
    local current_start current_state
    current_start="$(_process_start "$expected_pid")"
    if [ -n "$current_start" ]; then
        [ "$current_start" != "$expected_start" ] && return 0
        current_state="$(_process_state "$expected_pid")"
        case "$current_state" in Z*) return 0 ;; esac
        return 1
    fi
    kill -0 "$expected_pid" 2>/dev/null && return 1
    return 0
}

_wait_original_gone() {
    local expected_pid="$1"
    local expected_start="$2"
    local attempt=0
    while [ "$attempt" -lt 10 ]; do
        _original_gone "$expected_pid" "$expected_start" && return 0
        sleep 0.1
        attempt=$((attempt + 1))
    done
    _original_gone "$expected_pid" "$expected_start"
}

_left() {
    printf 'LEFT %s %s\n' "$1" "$2"
    LEFT_COUNT=$((LEFT_COUNT + 1))
}

REAPED_COUNT=0
LEFT_COUNT=0
tab="$(printf '\t')"

for state_dir in ${CANDIDATES[@]+"${CANDIDATES[@]}"}; do
    state_name="$(basename "$state_dir")"
    dispatch_pid=""
    if [ -f "$state_dir/dispatch-pid" ]; then
        dispatch_pid="$(sed -n '1{s/\r$//;p;}' "$state_dir/dispatch-pid" 2>/dev/null)"
    fi
    case "$dispatch_pid" in
        ''|*[!0-9]*)
            _left "$state_name" "no-dispatch-record"
            continue ;;
    esac

    if [ ! -s "$state_dir/worker-roots" ]; then
        _left "$state_name" "no-worker-record"
        continue
    fi

    worker_record="$(sed -n '1{s/\r$//;p;}' "$state_dir/worker-roots" 2>/dev/null)"
    worker_rest="${worker_record#*"$tab"}"
    if [ "$worker_rest" = "$worker_record" ]; then
        _left "$state_name" "unknown-identity"
        continue
    fi
    worker_fields="${worker_rest#*"$tab"}"
    if [ "$worker_fields" = "$worker_rest" ]; then
        # The legacy two-field PID/token format has no namespace.
        _left "$state_name" "unknown-identity"
        continue
    fi
    worker_scheme="${worker_record%%"$tab"*}"
    if [ "$worker_scheme" != "$REAPER_SCHEME" ]; then
        _left "$state_name" "foreign-scheme"
        continue
    fi
    worker_pid="${worker_rest%%"$tab"*}"
    worker_start="${worker_fields%%"$tab"*}"
    case "$worker_pid" in ''|*[!0-9]*) worker_pid="" ;; esac
    if [ -z "$worker_pid" ] || [ -z "$worker_start" ]; then
        _left "$state_name" "unknown-identity"
        continue
    fi

    if [ ! -s "$state_dir/dispatch-roots" ]; then
        _left "$state_name" "unknown-identity"
        continue
    fi
    dispatch_record="$(sed -n '1{s/\r$//;p;}' "$state_dir/dispatch-roots" 2>/dev/null)"
    dispatch_rest="${dispatch_record#*"$tab"}"
    dispatch_fields="${dispatch_rest#*"$tab"}"
    if [ "$dispatch_rest" = "$dispatch_record" ] || [ "$dispatch_fields" = "$dispatch_rest" ]; then
        _left "$state_name" "unknown-identity"
        continue
    fi
    dispatch_scheme="${dispatch_record%%"$tab"*}"
    if [ "$dispatch_scheme" != "$REAPER_SCHEME" ]; then
        _left "$state_name" "foreign-scheme"
        continue
    fi
    identity_dispatch_pid="${dispatch_rest%%"$tab"*}"
    dispatch_start="${dispatch_fields%%"$tab"*}"
    case "$identity_dispatch_pid" in ''|*[!0-9]*) identity_dispatch_pid="" ;; esac
    if [ -z "$identity_dispatch_pid" ] || [ -z "$dispatch_start" ] || [ "$identity_dispatch_pid" != "$dispatch_pid" ]; then
        _left "$state_name" "unknown-identity"
        continue
    fi

    if kill -0 "$identity_dispatch_pid" 2>/dev/null; then
        current_dispatch_start="$(_process_start "$identity_dispatch_pid")"
        if [ -z "$current_dispatch_start" ]; then
            _left "$state_name" "unknown-identity"
            continue
        fi
        if [ "$current_dispatch_start" = "$dispatch_start" ]; then
            _left "$state_name" "dispatcher-alive"
            continue
        fi
    fi

    if ! kill -0 "$worker_pid" 2>/dev/null; then
        _left "$state_name" "worker-exited"
        continue
    fi
    current_start="$(_process_start "$worker_pid")"
    if [ -z "$current_start" ]; then
        _left "$state_name" "unknown-identity"
        continue
    fi
    if [ "$current_start" != "$worker_start" ]; then
        _left "$state_name" "identity-mismatch"
        continue
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        printf 'WOULD-REAP %s pid=%s\n' "$state_name" "$worker_pid"
        LEFT_COUNT=$((LEFT_COUNT + 1))
        continue
    fi

    if [ ! -e "$state_dir/reap-reason" ]; then
        printf '%s\n' 'orphan-reap' > "$state_dir/reap-reason" 2>/dev/null || true
    fi

    worker_pgid="$(_process_group "$worker_pid")"
    signalled=0
    if [ "$worker_pgid" = "$worker_pid" ]; then
        if _same_process "$worker_pid" "$worker_start"; then
            if kill -TERM "-$worker_pid" 2>/dev/null; then
                signalled=1
            elif _same_process "$worker_pid" "$worker_start" && kill -TERM "$worker_pid" 2>/dev/null; then
                signalled=1
            fi
        fi
        sleep 2
        _group_alive "$worker_pgid"
        group_status=$?
        if [ "$group_status" -eq 0 ]; then
            if kill -KILL "-$worker_pid" 2>/dev/null; then
                signalled=1
            elif _same_process "$worker_pid" "$worker_start" && kill -KILL "$worker_pid" 2>/dev/null; then
                signalled=1
            fi
        fi
    else
        if _kill_descendants "$worker_pid" "$worker_start" "" TERM; then
            signalled=1
        fi
        sleep 2
        if _same_process "$worker_pid" "$worker_start"; then
            if _kill_descendants "$worker_pid" "$worker_start" "" KILL; then
                signalled=1
            fi
        fi
    fi

    tree_gone=1
    if [ "$worker_pgid" = "$worker_pid" ]; then
        _wait_group_gone "$worker_pgid"
        wait_status=$?
        [ "$wait_status" -eq 0 ] && tree_gone=0
    elif _wait_original_gone "$worker_pid" "$worker_start"; then
        # Without an isolated process group, descendants cannot be identified
        # after the root exits. The signals above still act, but success cannot
        # prove that the complete tree disappeared.
        tree_gone=1
    fi

    if [ "$tree_gone" -eq 0 ]; then
        if [ "$signalled" -eq 1 ]; then
            printf 'REAPED %s pid=%s\n' "$state_name" "$worker_pid"
            REAPED_COUNT=$((REAPED_COUNT + 1))
        else
            _left "$state_name" "worker-exited"
        fi
    else
        _left "$state_name" "kill-failed"
    fi
done

printf 'REAP-DONE reaped=%s left=%s\n' "$REAPED_COUNT" "$LEFT_COUNT"
exit 0
