#!/usr/bin/env bash
# stall-watch.sh -- Background failure and stall observer for Auto-terminal.
#
# Watches <state-dir>/tail and <state-dir>/tail.stderr-tmp. A terminal Codex
# response-stream failure is recorded immediately and the captured worker tree
# is reaped. Silence is lower-confidence: after 10 minutes by default it is
# recorded for auto-watch to surface, but no process is killed for silence.
# If the dispatcher disappears while its worker root is still alive, the
# abandoned worker tree is reaped before this observer exits.
#
# Args (named):
#   --state-dir <abs-path>   Directory created by the dispatcher
#   --parent-pid <PID>       PID of the dispatcher
#
# Env:
#   STALL_THRESHOLD_SECONDS      Default 600 (10 min)
#   STALL_POLL_INTERVAL_SECONDS  Default 30
#   IMPLEMENT_REVIEW_STREAM_RETRY_LIMIT
#                                Maximum automatic redispatches after stream
#                                death (default 1; 0 disables). The dispatcher
#                                records the effective value in the state dir.
# Retry attempts reuse the dispatch state dir; the dispatcher archives each
# failed attempt under <state-dir>/attempt-N before starting the next watcher.

set -u

# Release the deployed path before either session can refresh the shared
# scripts. Exec preserves the PID recorded by the dispatcher, so worker-tree
# capture continues to exclude the watcher itself by comparing against $$.
if [ "${IMPLEMENT_REVIEW_STALL_WATCH_REEXEC:-}" != "1" ]; then
    REEXEC_TMP_BASE="${TMPDIR:-/tmp}"
    REEXEC_TMP_BASE="${REEXEC_TMP_BASE%/}"
    REEXEC_DIR="${REEXEC_TMP_BASE}/implement-review-stall-watch-reexec-$$"
    REEXEC_COPY="${REEXEC_DIR}/stall-watch.sh"

    umask 077
    if ! mkdir "$REEXEC_DIR"; then
        echo "stall-watch: failed to create re-exec dir: $REEXEC_DIR" >&2
        exit 2
    fi
    if ! cp -- "$0" "$REEXEC_COPY"; then
        rmdir -- "$REEXEC_DIR" 2>/dev/null || true
        echo "stall-watch: failed to create re-exec copy: $REEXEC_COPY" >&2
        exit 2
    fi
    chmod u+x "$REEXEC_COPY" 2>/dev/null || true

    export IMPLEMENT_REVIEW_STALL_WATCH_REEXEC=1
    export IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR
    IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR=$(dirname -- "$0")

    "${BASH:-bash}" -c '
        watched_pid=$1
        reexec_copy=$2
        reexec_dir=$3
        while kill -0 "$watched_pid" 2>/dev/null; do sleep 1; done
        rm -f -- "$reexec_copy"
        rmdir -- "$reexec_dir" 2>/dev/null || true
    ' stall-watch-cleanup "$$" "$REEXEC_COPY" "$REEXEC_DIR" >/dev/null 2>&1 &

    exec "${BASH:-bash}" "$REEXEC_COPY" "$@"

    echo "stall-watch: failed to launch re-exec copy: $REEXEC_COPY" >&2
    rm -f -- "$REEXEC_COPY"
    rmdir -- "$REEXEC_DIR" 2>/dev/null || true
    exit 2
fi

SCRIPT_DIR="${IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR:-$(dirname -- "$0")}"
unset IMPLEMENT_REVIEW_STALL_WATCH_REEXEC \
    IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR

STATE_DIR=""
PARENT_PID=""

while [ $# -gt 0 ]; do
    case "$1" in
        --state-dir)
            [ $# -ge 2 ] || exit 0
            STATE_DIR="$2"; shift 2 ;;
        --parent-pid)
            [ $# -ge 2 ] || exit 0
            PARENT_PID="$2"; shift 2 ;;
        *) exit 0 ;;
    esac
done

[ -n "$STATE_DIR" ] || exit 0
case "$PARENT_PID" in ''|*[!0-9]*) exit 0 ;; esac
[ -d "$STATE_DIR" ] || exit 0

THRESHOLD="${STALL_THRESHOLD_SECONDS:-600}"
INTERVAL="${STALL_POLL_INTERVAL_SECONDS:-30}"
case "$THRESHOLD" in ''|*[!0-9]*|0) THRESHOLD=600 ;; esac
case "$INTERVAL" in ''|*[!0-9]*|0) INTERVAL=30 ;; esac

TAIL_FILE="$STATE_DIR/tail"
TAIL_STDERR_FILE="$STATE_DIR/tail.stderr-tmp"
WARN_FILE="$STATE_DIR/stall-warning"
STREAM_DEATH_FILE="$STATE_DIR/stream-death"
REAP_REASON_FILE="$STATE_DIR/reap-reason"
WORKER_ROOTS_FILE="$STATE_DIR/worker-roots"
REAP_TARGETS_FILE="$STATE_DIR/reap-targets"
STREAM_RETRY_LIMIT_FILE="$STATE_DIR/stream-retry-limit"
STREAM_RETRY_COUNT_FILE="$STATE_DIR/stream-retry-count"
STREAM_RETRY_REQUEST_FILE="$STATE_DIR/stream-retry-request"
STREAM_REAP_COMPLETE_FILE="$STATE_DIR/stream-reap-complete"

_process_start() {
    local process_id="$1"
    ps -o lstart= -p "$process_id" 2>/dev/null \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

_child_pids() {
    local parent_id="$1"
    if command -v pgrep >/dev/null 2>&1; then
        pgrep -P "$parent_id" 2>/dev/null || true
    else
        ps -eo pid=,ppid= 2>/dev/null \
            | awk -v parent="$parent_id" '$2 == parent { print $1 }'
    fi
}

PARENT_START="$(_process_start "$PARENT_PID")"
[ -n "$PARENT_START" ] || exit 0
capture_attempts=0

_same_process() {
    local expected_pid="$1"
    local expected_start="$2"
    local current_start
    [ -n "$expected_start" ] || return 1
    current_start="$(_process_start "$expected_pid")"
    [ -n "$current_start" ] && [ "$current_start" = "$expected_start" ]
}

_capture_worker_roots() {
    local found=0
    local candidate started
    [ -s "$WORKER_ROOTS_FILE" ] && return 0
    capture_attempts=$((capture_attempts + 1))
    for candidate in $(_child_pids "$PARENT_PID"); do
        case "$candidate" in ''|*[!0-9]*) continue ;; esac
        [ "$candidate" = "$$" ] && continue
        kill -0 "$candidate" 2>/dev/null || continue
        started="$(_process_start "$candidate")"
        [ -n "$started" ] || continue
        printf '%s\t%s\n' "$candidate" "$started" \
            >> "$WORKER_ROOTS_FILE" 2>/dev/null || continue
        found=1
    done
    [ "$found" -eq 1 ] || return 0
}

_collect_tree() {
    local target_pid="$1"
    local child_pid target_start
    for child_pid in $(_child_pids "$target_pid"); do
        [ "$child_pid" = "$$" ] || _collect_tree "$child_pid"
    done
    [ "$target_pid" = "$$" ] && return 0
    target_start="$(_process_start "$target_pid")"
    [ -n "$target_start" ] || return 0
    printf '%s\t%s\n' "$target_pid" "$target_start" >> "$REAP_TARGETS_FILE"
}

_reap_worker_roots() {
    local reason="$1"
    local victims=""
    local root_pid root_start target_pid target_start
    [ -s "$WORKER_ROOTS_FILE" ] || return 0
    while IFS="$(printf '\t')" read -r root_pid root_start; do
        case "$root_pid" in ''|*[!0-9]*) continue ;; esac
        if _same_process "$root_pid" "$root_start"; then
            victims="${victims}${victims:+ }${root_pid}"
        fi
    done < "$WORKER_ROOTS_FILE"
    [ -n "$victims" ] || return 0

    : > "$REAP_TARGETS_FILE" 2>/dev/null || return 0
    for root_pid in $victims; do
        _collect_tree "$root_pid"
    done
    printf '%s\n' "$reason" > "$REAP_REASON_FILE" 2>/dev/null || true
    while IFS="$(printf '\t')" read -r target_pid target_start; do
        case "$target_pid" in ''|*[!0-9]*) continue ;; esac
        _same_process "$target_pid" "$target_start" || continue
        kill -TERM "$target_pid" 2>/dev/null || true
    done < "$REAP_TARGETS_FILE"
    sleep 2
    while IFS="$(printf '\t')" read -r target_pid target_start; do
        case "$target_pid" in ''|*[!0-9]*) continue ;; esac
        _same_process "$target_pid" "$target_start" || continue
        kill -KILL "$target_pid" 2>/dev/null || true
    done < "$REAP_TARGETS_FILE"
}

_stream_died() {
    [ -f "$TAIL_FILE" ] || return 1
    tail -n 16 "$TAIL_FILE" 2>/dev/null \
        | tr -d '\r' \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
              -e '/^$/d' \
        | awk '
            { line[NR] = $0 }
            END {
                n = NR
                if (n < 3 || line[n - 1] != "tokens used" ||
                    line[n] !~ /^[0-9][0-9,]*$/) exit 1
                first = n - 4
                if (first < 1) first = 1
                for (i = first; i <= n - 2; i++) {
                    if (line[i] ~ /^ERROR: stream disconnected before completion: .*chatgpt[.]com\/backend-api\/codex\/responses/) exit 0
                }
                exit 1
            }
        '
}

_state_counter() {
    local path="$1" value
    [ -f "$path" ] || return 1
    value="$(head -n 1 "$path" 2>/dev/null | tr -d '[:space:]')"
    case "$value" in ''|*[!0-9]*) return 1 ;; esac
    printf '%s\n' "$value"
}

_request_stream_retry() {
    local iso="$1" limit count
    limit="$(_state_counter "$STREAM_RETRY_LIMIT_FILE")" || return 1
    count="$(_state_counter "$STREAM_RETRY_COUNT_FILE")" || return 1
    [ "$count" -lt "$limit" ] || return 1
    printf 'STREAM-RETRY-REQUEST %s attempt=%s/%s codex-response-stream-disconnected\n' \
        "$iso" "$((count + 2))" "$((limit + 1))" \
        > "$STREAM_RETRY_REQUEST_FILE" 2>/dev/null
}

# Both files count as progress. PowerShell dispatchers may split the streams;
# Bash dispatchers normally merge them, making the second probe a no-op.
last_size=-1
last_mtime=0
last_growth_time=$(date +%s 2>/dev/null || echo 0)
stalled_logged=0

while :; do
    if _same_process "$PARENT_PID" "$PARENT_START"; then
        parent_alive=1
        _capture_worker_roots
    else
        parent_alive=0
    fi

    current_size=0
    current_mtime=0
    any_exists=0
    for tf in "$TAIL_FILE" "$TAIL_STDERR_FILE"; do
        [ -f "$tf" ] || continue
        any_exists=1
        sz=$(wc -c < "$tf" 2>/dev/null | tr -d ' ')
        sz="${sz:-0}"
        case "$sz" in ''|*[!0-9]*) sz=0 ;; esac
        current_size=$((current_size + sz))
        if mt=$(stat -c %Y "$tf" 2>/dev/null); then
            :
        elif mt=$(stat -f %m "$tf" 2>/dev/null); then
            :
        else
            mt=0
        fi
        case "$mt" in ''|*[!0-9]*) mt=0 ;; esac
        [ "$mt" -le "$current_mtime" ] || current_mtime="$mt"
    done

    if [ "$any_exists" -eq 1 ]; then
        now=$(date +%s 2>/dev/null || echo 0)
        case "$current_size$last_size$current_mtime$last_mtime$now" in
            *[!0-9-]*) sleep "$INTERVAL"; continue ;;
        esac

        if [ "$current_size" -gt "$last_size" ] || [ "$current_mtime" -gt "$last_mtime" ]; then
            if [ ! -f "$STREAM_DEATH_FILE" ] && _stream_died; then
                iso=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo unknown)
                retry_requested=0
                if _request_stream_retry "$iso"; then
                    retry_requested=1
                fi
                if ! printf 'STREAM-DEATH %s codex-response-stream-disconnected\n' "$iso" \
                    > "$STREAM_DEATH_FILE" 2>/dev/null; then
                    [ "$retry_requested" -eq 0 ] || \
                        rm -f -- "$STREAM_RETRY_REQUEST_FILE"
                fi
                _reap_worker_roots stream-death
                printf 'STREAM-REAP-COMPLETE %s\n' "$iso" \
                    > "$STREAM_REAP_COMPLETE_FILE" 2>/dev/null || true
                exit 0
            fi
            last_size="$current_size"
            last_mtime="$current_mtime"
            last_growth_time="$now"
            stalled_logged=0
        else
            elapsed=$((now - last_growth_time))
            if [ "$elapsed" -ge "$THRESHOLD" ] && [ "$stalled_logged" -eq 0 ]; then
                iso=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo unknown)
                printf 'STALL %s tail-no-growth-for-%ds\n' "$iso" "$elapsed" \
                    >> "$WARN_FILE" 2>/dev/null || exit 0
                stalled_logged=1
            fi
        fi
    fi

    if [ "$parent_alive" -eq 0 ]; then
        _reap_worker_roots parent-exited
        exit 0
    fi

    if [ -s "$WORKER_ROOTS_FILE" ] || [ "$capture_attempts" -ge 5 ]; then
        sleep "$INTERVAL"
    else
        sleep 1
    fi
done
