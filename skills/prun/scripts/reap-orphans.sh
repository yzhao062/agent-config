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

_read_stat_line() {
    local stat_path="$1"
    local stat_line
    if type _prun_reap_read_stat >/dev/null 2>&1; then
        _prun_reap_read_stat "$stat_path"
        return
    fi
    IFS= read -r stat_line < "$stat_path" || return 1
    printf '%s\n' "$stat_line"
}

_pid_still_present() {
    local process_pid="$1"
    [ -d "/proc/$process_pid" ] || kill -0 "$process_pid" 2>/dev/null
}

# Set PROC_ROW_* globals. Return 1 when the PID disappeared during the read and
# 2 when a live PID cannot be read or parsed.
_load_proc_row() {
    local process_pid="$1"
    local proc_line proc_rest process_state process_parent process_group process_start read_status
    if type _prun_reap_read_stat >/dev/null 2>&1; then
        proc_line="$(_read_stat_line "/proc/$process_pid/stat" 2>/dev/null)"
        read_status=$?
    else
        IFS= read -r proc_line < "/proc/$process_pid/stat" 2>/dev/null
        read_status=$?
    fi
    if [ "$read_status" -ne 0 ] || [ -z "$proc_line" ]; then
        _pid_still_present "$process_pid" && return 2
        return 1
    fi
    proc_rest="${proc_line##*)}"
    if [ "$proc_rest" = "$proc_line" ]; then
        _pid_still_present "$process_pid" && return 2
        return 1
    fi
    set -- $proc_rest
    if [ "$#" -lt 20 ]; then
        _pid_still_present "$process_pid" && return 2
        return 1
    fi
    process_state="$1"
    process_parent="$2"
    process_group="$3"
    shift 19
    process_start="$1"
    case "$process_state" in [A-Za-z]) ;; *) _pid_still_present "$process_pid" && return 2; return 1 ;; esac
    case "$process_parent" in ''|*[!0-9]*) _pid_still_present "$process_pid" && return 2; return 1 ;; esac
    case "$process_group" in ''|*[!0-9]*) _pid_still_present "$process_pid" && return 2; return 1 ;; esac
    case "$process_start" in ''|*[!0-9]*) _pid_still_present "$process_pid" && return 2; return 1 ;; esac
    PROC_ROW_PID="$process_pid"
    PROC_ROW_PARENT="$process_parent"
    PROC_ROW_GROUP="$process_group"
    PROC_ROW_STATE="$process_state"
    PROC_ROW_START="$process_start"
}

# Output: pid, parent PID, process group, state, start time.
_proc_row() {
    _load_proc_row "$1" || return $?
    printf '%s\t%s\t%s\t%s\t%s\n' \
        "$PROC_ROW_PID" "$PROC_ROW_PARENT" "$PROC_ROW_GROUP" "$PROC_ROW_STATE" "$PROC_ROW_START"
}

_process_start() {
    local process_pid="$1"
    local process_row row_pid row_parent row_group row_state row_start
    if [ -d /proc ]; then
        process_row="$(_proc_row "$process_pid")" || return 0
        IFS="$tab" read -r row_pid row_parent row_group row_state row_start <<EOF
$process_row
EOF
        printf '%s\n' "$row_start"
        return 0
    fi
    ps -o lstart= -p "$process_pid" 2>/dev/null \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

_process_state() {
    local process_pid="$1"
    local process_row row_pid row_parent row_group row_state row_start
    if [ -d /proc ]; then
        process_row="$(_proc_row "$process_pid")" || return 0
        IFS="$tab" read -r row_pid row_parent row_group row_state row_start <<EOF
$process_row
EOF
        printf '%s\n' "$row_state"
        return 0
    fi
    ps -o stat= -p "$process_pid" 2>/dev/null \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]].*$//'
}

_process_group() {
    local process_pid="$1"
    local process_row row_pid row_parent row_group row_state row_start
    if [ -d /proc ]; then
        process_row="$(_proc_row "$process_pid")" || return 0
        IFS="$tab" read -r row_pid row_parent row_group row_state row_start <<EOF
$process_row
EOF
        printf '%s\n' "$row_group"
        return 0
    fi
    ps -o pgid= -p "$process_pid" 2>/dev/null | tr -d '[:space:]'
}

_scan_process_rows() {
    local proc_dir process_pid process_row row_status incomplete=0
    local process_rows row_pid row_parent row_group row_state start_day start_month
    local start_date start_clock start_year
    if [ -d /proc ]; then
        for proc_dir in /proc/[0-9]*; do
            [ -d "$proc_dir" ] || continue
            process_pid="${proc_dir#/proc/}"
            case "$process_pid" in ''|*[!0-9]*) continue ;; esac
            _load_proc_row "$process_pid"
            row_status=$?
            if [ "$row_status" -eq 0 ]; then
                printf '%s\t%s\t%s\t%s\t%s\n' \
                    "$PROC_ROW_PID" "$PROC_ROW_PARENT" "$PROC_ROW_GROUP" \
                    "$PROC_ROW_STATE" "$PROC_ROW_START"
            elif [ "$row_status" -eq 2 ]; then
                incomplete=1
            fi
        done
        [ "$incomplete" -eq 0 ] || return 2
        return 0
    fi

    # macOS has no /proc. Its ps supports these fields; MSYS does not, so this
    # branch must remain restricted to platforms without /proc.
    process_rows="$(ps -axo pid=,ppid=,pgid=,stat=,lstart= 2>/dev/null)" || return 2
    while read -r row_pid row_parent row_group row_state start_day start_month \
        start_date start_clock start_year; do
        case "$row_pid" in ''|*[!0-9]*) continue ;; esac
        case "$row_parent" in ''|*[!0-9]*) return 2 ;; esac
        case "$row_group" in ''|*[!0-9]*) return 2 ;; esac
        [ -n "$row_state" ] && [ -n "$start_year" ] || return 2
        printf '%s\t%s\t%s\t%s\t%s %s %s %s %s\n' \
            "$row_pid" "$row_parent" "$row_group" "$row_state" \
            "$start_day" "$start_month" "$start_date" "$start_clock" "$start_year"
    done <<EOF
$process_rows
EOF
}

_group_members() {
    local expected_group="$1"
    local process_rows scan_status row_pid row_parent row_group row_state row_start
    process_rows="$(_scan_process_rows)"
    scan_status=$?
    while IFS="$tab" read -r row_pid row_parent row_group row_state row_start; do
        [ -n "$row_pid" ] || continue
        [ "$row_group" = "$expected_group" ] || continue
        case "$row_state" in Z*) continue ;; esac
        printf '%s\n' "$row_pid"
    done <<EOF
$process_rows
EOF
    [ "$scan_status" -eq 0 ] || return 2
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

_lookup_retained_start() {
    local wanted_pid="$1"
    local retained_index=0
    while [ "$retained_index" -lt "${#RETAINED_PIDS[@]}" ]; do
        if [ "${RETAINED_PIDS[$retained_index]}" = "$wanted_pid" ]; then
            RETAINED_LOOKUP_START="${RETAINED_STARTS[$retained_index]}"
            return 0
        fi
        retained_index=$((retained_index + 1))
    done
    return 1
}

_lookup_row_start() {
    local process_rows="$1"
    local wanted_pid="$2"
    local row_pid row_parent row_group row_state row_start
    while IFS="$tab" read -r row_pid row_parent row_group row_state row_start; do
        if [ "$row_pid" = "$wanted_pid" ]; then
            ROW_LOOKUP_START="$row_start"
            return 0
        fi
    done <<EOF
$process_rows
EOF
    return 1
}

_add_reachable_rows() {
    local process_rows="$1"
    local changed=1 row_pid row_parent row_group row_state row_start
    local retained_start parent_start current_parent_start
    while [ "$changed" -eq 1 ]; do
        changed=0
        while IFS="$tab" read -r row_pid row_parent row_group row_state row_start; do
            [ -n "$row_pid" ] || continue
            if _lookup_retained_start "$row_pid"; then
                retained_start="$RETAINED_LOOKUP_START"
                [ "$retained_start" = "$row_start" ] || DESCENDANT_SCAN_COMPLETE=0
                continue
            fi
            _lookup_retained_start "$row_parent" || continue
            parent_start="$RETAINED_LOOKUP_START"
            if ! _lookup_row_start "$process_rows" "$row_parent"; then
                DESCENDANT_SCAN_COMPLETE=0
                continue
            fi
            current_parent_start="$ROW_LOOKUP_START"
            if [ "$current_parent_start" != "$parent_start" ]; then
                DESCENDANT_SCAN_COMPLETE=0
                continue
            fi
            RETAINED_PIDS+=("$row_pid")
            RETAINED_STARTS+=("$row_start")
            changed=1
        done <<EOF
$process_rows
EOF
    done
}

_validate_retained_rows() {
    local process_rows="$1"
    local retained_index=0
    while [ "$retained_index" -lt "${#RETAINED_PIDS[@]}" ]; do
        if ! _lookup_row_start "$process_rows" "${RETAINED_PIDS[$retained_index]}"; then
            return 1
        fi
        [ "$ROW_LOOKUP_START" = "${RETAINED_STARTS[$retained_index]}" ] || return 1
        retained_index=$((retained_index + 1))
    done
    return 0
}

_collect_descendant_identities() {
    local root_pid="$1"
    local root_start="$2"
    local pass=0 before_count process_rows scan_status
    RETAINED_PIDS=("$root_pid")
    RETAINED_STARTS=("$root_start")
    DESCENDANT_SCAN_COMPLETE=1
    while [ "$pass" -lt 32 ]; do
        before_count="${#RETAINED_PIDS[@]}"
        process_rows="$(_scan_process_rows)"
        scan_status=$?
        [ "$scan_status" -eq 0 ] || DESCENDANT_SCAN_COMPLETE=0
        _add_reachable_rows "$process_rows"
        _validate_retained_rows "$process_rows" || DESCENDANT_SCAN_COMPLETE=0
        if [ "${#RETAINED_PIDS[@]}" -eq "$before_count" ]; then
            [ "$DESCENDANT_SCAN_COMPLETE" -eq 1 ] && return 0
            return 2
        fi
        pass=$((pass + 1))
    done
    DESCENDANT_SCAN_COMPLETE=0
    return 2
}

_signal_retained() {
    local signal_name="$1"
    local retained_index=0 retained_pid retained_start
    while [ "$retained_index" -lt "${#RETAINED_PIDS[@]}" ]; do
        retained_pid="${RETAINED_PIDS[$retained_index]}"
        retained_start="${RETAINED_STARTS[$retained_index]}"
        if _same_process "$retained_pid" "$retained_start"; then
            kill "-$signal_name" "$retained_pid" 2>/dev/null && signalled=1
        fi
        retained_index=$((retained_index + 1))
    done
}

_all_retained_gone() {
    local retained_index=0
    while [ "$retained_index" -lt "${#RETAINED_PIDS[@]}" ]; do
        _original_gone "${RETAINED_PIDS[$retained_index]}" \
            "${RETAINED_STARTS[$retained_index]}" || return 1
        retained_index=$((retained_index + 1))
    done
    return 0
}

_wait_retained_gone() {
    local attempt=0
    while [ "$attempt" -lt 10 ]; do
        _all_retained_gone && return 0
        sleep 0.1
        attempt=$((attempt + 1))
    done
    _all_retained_gone
}

_left() {
    printf 'LEFT %s %s\n' "$1" "$2"
    LEFT_COUNT=$((LEFT_COUNT + 1))
}

# REAPED is reserved for kernel-backed containment (anywhere-agents#29) and is
# intentionally unreachable while descendant discovery relies on snapshots.
TERMINATED_COUNT=0
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

    RETAINED_PIDS=()
    RETAINED_STARTS=()
    descendant_scan_complete=0
    if _collect_descendant_identities "$worker_pid" "$worker_start"; then
        descendant_scan_complete=1
    fi

    worker_pgid="$(_process_group "$worker_pid")"
    group_target_valid=0
    if [ -n "$worker_pgid" ] && [ "$worker_pgid" = "$worker_pid" ]; then
        group_target_valid=1
    fi
    signalled=0
    if [ "$group_target_valid" -eq 1 ] && _same_process "$worker_pid" "$worker_start"; then
        kill -TERM "-$worker_pgid" 2>/dev/null && signalled=1
    fi
    _signal_retained TERM

    sleep 2
    if [ "$group_target_valid" -eq 1 ]; then
        _group_alive "$worker_pgid"
        group_status=$?
        if [ "$group_status" -ne 1 ]; then
            kill -KILL "-$worker_pgid" 2>/dev/null && signalled=1
        fi
    fi
    _signal_retained KILL

    group_gone=0
    if [ "$group_target_valid" -eq 1 ]; then
        _wait_group_gone "$worker_pgid"
        wait_status=$?
        [ "$wait_status" -eq 0 ] && group_gone=1
    fi
    retained_gone=0
    _wait_retained_gone && retained_gone=1

    if [ "$group_gone" -eq 1 ] && \
            [ "$descendant_scan_complete" -eq 1 ] && \
            [ "$retained_gone" -eq 1 ]; then
        if [ "$signalled" -eq 1 ]; then
            printf 'TERMINATED %s pid=%s\n' "$state_name" "$worker_pid"
            TERMINATED_COUNT=$((TERMINATED_COUNT + 1))
        else
            _left "$state_name" "worker-exited"
        fi
    else
        _left "$state_name" "kill-failed"
    fi
done

printf 'REAP-DONE terminated=%s left=%s\n' "$TERMINATED_COUNT" "$LEFT_COUNT"
exit 0
