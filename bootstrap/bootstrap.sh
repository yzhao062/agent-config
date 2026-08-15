# Line endings are handled by this repo's .gitattributes. Bootstrap intentionally
# avoids changing user-level Git configuration.

# Parse flags and positional args:
#   [UPSTREAM]          positional, user/repo form (overrides env and persisted)
#   --rule-packs PACK   dry helper: print agent-config.yaml snippet and exit
#   --no-cache          force rule-pack refetch on this run (opt-in path only)
#   --help | -h         show usage
_POS_UPSTREAM=""
RULE_PACKS_DRY=""
NO_CACHE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --rule-packs)
      if [ -z "${2:-}" ]; then
        echo "error: --rule-packs requires a pack name" >&2
        exit 1
      fi
      if [ -n "$RULE_PACKS_DRY" ]; then
        echo "warning: --rule-packs specified multiple times; last value wins" >&2
      fi
      RULE_PACKS_DRY="$2"
      shift 2
      ;;
    --rule-packs=*)
      _rp_val="${1#--rule-packs=}"
      if [ -z "$_rp_val" ]; then
        echo "error: --rule-packs requires a pack name" >&2
        exit 1
      fi
      if [ -n "$RULE_PACKS_DRY" ]; then
        echo "warning: --rule-packs specified multiple times; last value wins" >&2
      fi
      RULE_PACKS_DRY="$_rp_val"
      shift
      ;;
    --no-cache)
      NO_CACHE=1
      shift
      ;;
    --help|-h)
      cat <<'EOF'
Usage: bash bootstrap.sh [UPSTREAM] [--rule-packs PACK] [--no-cache]
  UPSTREAM        user/repo form; overrides AGENT_CONFIG_UPSTREAM env and persisted file
  --rule-packs P  print agent-config.yaml snippet for pack P and exit (dry helper)
  --no-cache      force refetch of rule-pack content on this run
  -h, --help      show this help
EOF
      exit 0
      ;;
    --*)
      echo "error: unknown flag: $1" >&2
      echo "supported: --rule-packs PACK, --no-cache, --help" >&2
      exit 1
      ;;
    *)
      if [ -z "$_POS_UPSTREAM" ]; then
        _POS_UPSTREAM="$1"
      fi
      shift
      ;;
  esac
done

# Dry helper: --rule-packs prints a YAML snippet and exits without running
# bootstrap. The flag wins when both --rule-packs and AGENT_CONFIG_RULE_PACKS
# are set simultaneously.
if [ -n "$RULE_PACKS_DRY" ]; then
  if [ -n "${AGENT_CONFIG_RULE_PACKS:-}" ]; then
    echo "notice: --rule-packs is a dry helper; AGENT_CONFIG_RULE_PACKS env var is ignored in this mode" >&2
  fi
  cat <<EOF
Add the following to agent-config.yaml at your project root, then run bootstrap again to apply:

  rule_packs:
    - name: $RULE_PACKS_DRY
      # Optional: pin to a specific ref (defaults to manifest's default-ref)
      # ref: v0.3.5

After committing agent-config.yaml, run:

  bash bootstrap.sh
EOF
  exit 0
fi


# Find a real Python interpreter, avoiding the Windows Store App Execution
# Alias shim under %LOCALAPPDATA%\Microsoft\WindowsApps\ (which prints
# "Python was not found; install from Store" and exits non-zero on call).
# Order: env override > deployed wrapper > sparse-clone wrapper > PATH lookup
# with shim skip. See https://github.com/yzhao062/anywhere-agents/issues/2.
# Exit status alone is not proof that Python ran. A command that ignores its
# arguments and exits 0, such as `true` or a .cmd containing only `exit /b 0`,
# passes an exit-status probe while executing nothing. Require the interpreter
# to echo a sentinel, so only something that actually evaluated the -c program
# is accepted.
_python_runs() {
  _probe_output="$("$1" -c 'import sys; sys.stdout.write("__ANYWHERE_AGENTS_PY3__" if sys.version_info[0] >= 3 else "")' 2>/dev/null)" || return 1
  [ "$_probe_output" = "__ANYWHERE_AGENTS_PY3__" ]
}

_find_python() {
  if [ -n "${ANYWHERE_AGENTS_PYTHON:-}" ]; then
    if [ -x "$ANYWHERE_AGENTS_PYTHON" ] && _python_runs "$ANYWHERE_AGENTS_PYTHON"; then
      echo "$ANYWHERE_AGENTS_PYTHON"; return 0
    fi
    printf '%s\n' "[anywhere-agents] ANYWHERE_AGENTS_PYTHON did not execute Python 3 successfully: $ANYWHERE_AGENTS_PYTHON; trying automatic discovery." >&2
  fi
  if [ -x "$HOME/.claude/hooks/_python" ] && _python_runs "$HOME/.claude/hooks/_python"; then
    echo "$HOME/.claude/hooks/_python"; return 0
  fi
  if [ -x ".agent-config/repo/scripts/_python" ] && _python_runs ".agent-config/repo/scripts/_python"; then
    echo ".agent-config/repo/scripts/_python"; return 0
  fi
  for cmd in python3 python; do
    while IFS= read -r candidate; do
      [ -n "$candidate" ] || continue
      resolved="$candidate"
      if command -v readlink >/dev/null 2>&1; then
        maybe=$(readlink -f "$candidate" 2>/dev/null || true)
        [ -n "$maybe" ] && resolved="$maybe"
      fi
      case "$resolved" in
        *WindowsApps*|*windowsapps*) continue ;;
      esac
      if _python_runs "$candidate"; then
        echo "$candidate"; return 0
      fi
    done < <(type -a -p "$cmd" 2>/dev/null || true)
  done
  return 1
}

# Best-effort bootstrap ledger. This script runs without set -e, so every
# helper must finish successfully rather than relying on error propagation.
_ledger_esc() {
  local LC_ALL=C
  local _ledger_input=$1
  local _ledger_output=""
  local _ledger_char _ledger_code _ledger_encoded
  local _ledger_index=0
  while [ "$_ledger_index" -lt "${#_ledger_input}" ]; do
    _ledger_char=${_ledger_input:$_ledger_index:1}
    case "$_ledger_char" in
      $'\b') _ledger_output="${_ledger_output}\\b" ;;
      $'\t') _ledger_output="${_ledger_output}\\t" ;;
      $'\n') _ledger_output="${_ledger_output}\\n" ;;
      $'\f') _ledger_output="${_ledger_output}\\f" ;;
      $'\r') _ledger_output="${_ledger_output}\\r" ;;
      '"') _ledger_output="${_ledger_output}\\\"" ;;
      '\') _ledger_output="${_ledger_output}\\\\" ;;
      *)
        if ! printf -v _ledger_code '%d' "'$_ledger_char" 2>/dev/null; then
          _ledger_output=""
          break
        fi
        if [ "$_ledger_code" -lt 32 ]; then
          if ! printf -v _ledger_encoded '\\u%04x' "$_ledger_code" 2>/dev/null; then
            _ledger_output=""
            break
          fi
          _ledger_output="${_ledger_output}${_ledger_encoded}"
        else
          _ledger_output="${_ledger_output}${_ledger_char}"
        fi
        ;;
    esac
    _ledger_index=$((_ledger_index + 1))
  done
  printf '%s' "$_ledger_output" 2>/dev/null || true
  return 0
}

_ledger_write() {
  _ledger_last_phase=$1
  _ledger_completed=$2
  mkdir -p .agent-config 2>/dev/null || return 0
  _ledger_upstream=$(_ledger_esc "${_LEDGER_UPSTREAM:-}")
  _ledger_run_id=$(_ledger_esc "${_LEDGER_RUN_ID:-}")
  _ledger_started=$(_ledger_esc "${_LEDGER_STARTED:-}")
  _ledger_phase=$(_ledger_esc "$_ledger_last_phase")
  printf '{"schema":1,"emitted_by":"bootstrap.sh","run_id":"%s","started_at":"%s","upstream":"%s","completed":%s,"last_phase":"%s","steps":[%s]}\n' \
    "$_ledger_run_id" "$_ledger_started" "$_ledger_upstream" "$_ledger_completed" \
    "$_ledger_phase" "${_LEDGER_STEPS:-}" > .agent-config/last-run.json.tmp 2>/dev/null &&
    mv -f .agent-config/last-run.json.tmp .agent-config/last-run.json 2>/dev/null || true
}

_ledger_init() {
  _LEDGER_RUN_ID="$$-$(date -u +%s 2>/dev/null || echo 0)"
  _LEDGER_STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"
  _LEDGER_UPSTREAM="${_POS_UPSTREAM:-${AGENT_CONFIG_UPSTREAM:-}}"
  _LEDGER_STEPS=""
  _LEDGER_TARGETS=""
  _ledger_write start false
  return 0
}

_ledger_target() {
  _ledger_target_value=$(_ledger_esc "$1")
  if [ -n "${_LEDGER_TARGETS:-}" ]; then
    _LEDGER_TARGETS="${_LEDGER_TARGETS},"
  fi
  _LEDGER_TARGETS="${_LEDGER_TARGETS}\"${_ledger_target_value}\""
  return 0
}

_ledger_step() {
  _ledger_step_phase=$1
  _ledger_step_scope=$2
  _ledger_step_status=$3
  _ledger_step_rc=${4:-null}
  _ledger_step_phase_json=$(_ledger_esc "$_ledger_step_phase")
  _ledger_step_scope_json=$(_ledger_esc "$_ledger_step_scope")
  _ledger_step_status_json=$(_ledger_esc "$_ledger_step_status")
  _ledger_step_value="{\"phase\":\"${_ledger_step_phase_json}\",\"scope\":\"${_ledger_step_scope_json}\",\"status\":\"${_ledger_step_status_json}\",\"rc\":${_ledger_step_rc},\"targets\":[${_LEDGER_TARGETS:-}]}"
  if [ -n "${_LEDGER_STEPS:-}" ]; then
    _LEDGER_STEPS="${_LEDGER_STEPS},"
  fi
  _LEDGER_STEPS="${_LEDGER_STEPS}${_ledger_step_value}"
  _LEDGER_TARGETS=""
  _ledger_write "$_ledger_step_phase" false
  return 0
}

_generator_status=skipped
_generator_rc=null

_run_generator() {
  _generator_python=$1
  [ -n "$_generator_python" ] || return 0
  [ -f .agent-config/repo/scripts/generate_agent_configs.py ] || return 0
  "$_generator_python" .agent-config/repo/scripts/generate_agent_configs.py --root . --quiet
  _generator_rc=$?
  if [ "$_generator_rc" -eq 0 ]; then
    _generator_status=ok
  else
    _generator_status=failed
  fi
  return 0
}

_record_generator_step() {
  case "$_generator_status" in
    ok)
      _ledger_target CLAUDE.md
      _ledger_target agents/codex.md
      _ledger_step generate repo ok
      ;;
    failed)
      _ledger_step generate repo failed "$_generator_rc"
      ;;
    *)
      _ledger_step generate repo skipped
      ;;
  esac
  return 0
}

# Detect git binary and reject pre-2.25 versions before any git invocation
# below. Sparse clone uses `git clone --filter=blob:none --sparse`; `--sparse`
# is the Git 2.25 floor (2020-01-13), while `--filter=blob:none` is the older
# partial-clone option (Git 2.19+). macOS shipped pre-2.25 system git as late
# as Big Sur, and a real consumer hit `unknown option 'sparse'` on 2026-05-18.
# On parse failure default-pass with a stderr warning so unexpected version
# strings (alpha builds, distro suffixes like `2.30.1.windows.1` or
# `(Apple Git-141)`) do not block already-modern systems.
_git_install_hint() {
  case "$(uname -s 2>/dev/null)" in
    Darwin) printf 'install: brew install git' ;;
    Linux)  printf 'install: sudo apt update && sudo apt install -y git (or your distro package manager)' ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT) printf 'install: https://git-scm.com/download/win' ;;
    *)      printf 'install: see https://git-scm.com/downloads' ;;
  esac
}

check_git_preflight() {
  if [ -n "${AGENT_CONFIG_SKIP_GIT_PREFLIGHT:-}" ]; then
    return 0
  fi
  if ! command -v git >/dev/null 2>&1; then
    printf '[anywhere-agents] git is not installed or not on PATH; bootstrap needs git >= 2.25 for sparse clone.\n' >&2
    printf '[anywhere-agents] %s\n' "$(_git_install_hint)" >&2
    exit 1
  fi
  _ver_line=$(git --version 2>/dev/null || true)
  _ver_str=${_ver_line#git version }
  _major=""
  _minor=""
  if [ -n "$_ver_str" ] && [ "$_ver_str" != "$_ver_line" ]; then
    _major=$(printf '%s' "$_ver_str" | sed -n 's/^\([0-9][0-9]*\)\..*/\1/p')
    _minor=$(printf '%s' "$_ver_str" | sed -n 's/^[0-9][0-9]*\.\([0-9][0-9]*\).*/\1/p')
  fi
  if [ -z "$_major" ] || [ -z "$_minor" ]; then
    printf '[anywhere-agents] could not parse git version from %s; assuming OK.\n' "${_ver_line:-<empty>}" >&2
    return 0
  fi
  if [ "$_major" -lt 2 ] || { [ "$_major" -eq 2 ] && [ "$_minor" -lt 25 ]; }; then
    printf '[anywhere-agents] git %s.%s is too old; bootstrap needs git >= 2.25 for sparse clone.\n' "$_major" "$_minor" >&2
    printf '[anywhere-agents] %s\n' "$(_git_install_hint)" >&2
    exit 1
  fi
  return 0
}

_ledger_init
check_git_preflight
[ -n "${AGENT_CONFIG_PREFLIGHT_TEST:-}" ] && exit 0

_codex_auto_update_disabled() {
  _v=$(printf '%s' "${ANYWHERE_AGENTS_CODEX_AUTO_UPDATE:-}" | tr '[:upper:]' '[:lower:]')
  case "$_v" in
    off|0|disabled|false|no) return 0 ;;
    *) return 1 ;;
  esac
}

maybe_update_codex_cli() {
  _codex_auto_update_disabled && return 0
  command -v npm >/dev/null 2>&1 || return 0
  _prefix=$(npm prefix -g 2>/dev/null || true)
  [ -n "$_prefix" ] || return 0
  [ -f "$_prefix/node_modules/@openai/codex/package.json" ] || return 0
  _outdated=$(npm outdated -g @openai/codex --json 2>/dev/null || true)
  [ -n "$_outdated" ] && [ "$_outdated" != "{}" ] || return 0
  _current=$(printf '%s' "$_outdated" | sed -n 's/.*"current"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
  _latest=$(printf '%s' "$_outdated" | sed -n 's/.*"latest"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
  [ -n "$_latest" ] && [ "$_latest" != "$_current" ] || return 0
  printf '[anywhere-agents] updating Codex CLI @openai/codex %s -> %s\n' "${_current:-?}" "$_latest" >&2
  if ! npm install -g @openai/codex@latest --silent; then
    printf '%s\n' '[anywhere-agents] Codex CLI auto-update failed; run `npm install -g @openai/codex@latest`' >&2
  fi
}

# Legacy AC -> AA migration for direct shell-bootstrap runs. If the
# persisted upstream or cached repo origin still points at agent-config
# and the caller did not pass an explicit upstream, delete the old cache
# so the normal clone path below re-clones anywhere-agents.
_legacy_ac=0
if [ -z "$_POS_UPSTREAM" ] && [ -z "${AGENT_CONFIG_UPSTREAM:-}" ]; then
  if [ -f .agent-config/upstream ] && [ "$(tr -d '\r\n\t ' < .agent-config/upstream)" = "yzhao062/agent-config" ]; then
    _legacy_ac=1
  elif [ -f .agent-config/repo/.git/config ] && git -C .agent-config/repo remote get-url origin 2>/dev/null | grep -Eiq '(^|[:/])yzhao062/agent-config(\.git)?/?$'; then
    _legacy_ac=1
  fi
fi
if [ "$_legacy_ac" = "1" ]; then
  printf '%s\n' '[anywhere-agents] Migrating from agent-config bootstrap to anywhere-agents...' >&2
  rm -rf .agent-config/repo .agent-config/upstream .agent-config/bootstrap.sh .agent-config/bootstrap.ps1
fi

# Upstream cascade: argv > env var > persisted file > hardcoded default.
# Forkers can persist a different default in their fork; consumers can pass
# upstream via `bash .agent-config/bootstrap.sh <user>/<repo>` or the
# $AGENT_CONFIG_UPSTREAM environment variable.
UPSTREAM=""
if [ -n "$_POS_UPSTREAM" ]; then
  UPSTREAM="$_POS_UPSTREAM"
elif [ -n "${AGENT_CONFIG_UPSTREAM:-}" ]; then
  UPSTREAM="$AGENT_CONFIG_UPSTREAM"
elif [ -f .agent-config/upstream ]; then
  UPSTREAM="$(tr -d '\r\n' < .agent-config/upstream)"
fi
UPSTREAM="${UPSTREAM:-yzhao062/anywhere-agents}"
mkdir -p .agent-config
printf '%s' "$UPSTREAM" > .agent-config/upstream
_LEDGER_UPSTREAM="$UPSTREAM"
_ledger_target .agent-config/upstream
_ledger_step preflight repo ok

mkdir -p .agent-config .claude/commands
curl -sfL "https://raw.githubusercontent.com/$UPSTREAM/main/AGENTS.md" -o .agent-config/AGENTS.md

# Sparse clone moved up (before composing the root AGENTS.md): the rule-pack
# manifest and composer helper live inside .agent-config/repo/ and must be
# present before we branch on opt-in.
REPO_URL="https://github.com/$UPSTREAM.git"
if [ -d .agent-config/repo/.git ]; then
  git -C .agent-config/repo remote set-url origin "$REPO_URL"
  git -C .agent-config/repo pull --ff-only
else
  git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" .agent-config/repo
fi
git -C .agent-config/repo sparse-checkout set skills .claude scripts user bootstrap
_ledger_target .agent-config/AGENTS.md
_ledger_target .agent-config/repo
_ledger_step fetch repo ok

# Compose root AGENTS.md. Default-on: every aa consumer gets the agent-style
# writing rule pack unless they explicitly opt out via `rule_packs: []` in
# agent-config.yaml. Composition requires Python 3 + PyYAML; when PyYAML is
# missing we attempt a best-effort `pip install --user pyyaml`. If Python or
# PyYAML still aren't available, we fall back to the verbatim upstream
# AGENTS.md and print a one-line tip unless the consumer has explicitly
# referenced rule_packs themselves.
_py=$(_find_python || true)
# Candidate discovery is stable after the sparse clone, so reuse this probed
# result for every later Python-backed phase in the same bootstrap run.
_compose_ok=false
if [ -n "$_py" ]; then
  if ! "$_py" -c "import yaml" >/dev/null 2>&1; then
    printf 'installing PyYAML (enables agent-style rule-pack composition)...\n' >&2
    "$_py" -m pip install --user --quiet pyyaml || true
  fi
  if "$_py" -c "import yaml" >/dev/null 2>&1; then
    _compose_ok=true
  fi
fi

if $_compose_ok && [ ! -f .agent-config/repo/scripts/compose_packs.py ] && [ ! -f .agent-config/repo/scripts/compose_rule_packs.py ]; then
  # Upstream sparse clone has no composer script (e.g. the ac source repo
  # itself, which intentionally ships only generate_agent_configs.py and
  # not the v0.4.0 unified composer). Fall through to the verbatim-AGENTS.md
  # path instead of crashing on a non-existent Python file.
  printf '%s\n' '[anywhere-agents] no composer script in .agent-config/repo/scripts/; falling back to verbatim AGENTS.md' >&2
  _compose_ok=false
fi

if $_compose_ok; then
  _NO_CACHE_FLAG=""
  [ -n "$NO_CACHE" ] && _NO_CACHE_FLAG="--no-cache"
  # Prefer the v0.4.0 unified composer. Fall back to the v0.3.x rule-pack
  # composer on pre-v0.4.0 sparse clones that predate compose_packs.py.
  if [ -f .agent-config/repo/scripts/compose_packs.py ]; then
    _composer=.agent-config/repo/scripts/compose_packs.py
  else
    _composer=.agent-config/repo/scripts/compose_rule_packs.py
  fi
  # shellcheck disable=SC2086
  # v0.5.8: capture composer rc and always run generator so CLAUDE.md stays
  # coherent even when composition aborts (e.g. DriftAbort, OSError).
  "$_py" "$_composer" --root . $_NO_CACHE_FLAG
  _composer_rc=$?
  _run_generator "$_py"
  if [ "$_composer_rc" -ne 0 ]; then
    printf '%s\n' "[anywhere-agents] pack composition did not complete (rc=${_composer_rc}); generated files (CLAUDE.md, agents/codex.md) refreshed from current AGENTS.md. Re-run \`anywhere-agents\` after addressing the failure." >&2
    _ledger_target AGENTS.md
    _ledger_step compose repo failed "$_composer_rc"
    _record_generator_step
    exit "$_composer_rc"
  fi
  _ledger_target AGENTS.md
  _ledger_step compose repo ok
else
  cp -f .agent-config/AGENTS.md AGENTS.md
  _rp_aware=false
  if [ -f agent-config.yaml ] && grep -qE '^rule_packs:' agent-config.yaml 2>/dev/null; then
    _rp_aware=true
  elif [ -f agent-config.local.yaml ] && grep -qE '^rule_packs:' agent-config.local.yaml 2>/dev/null; then
    _rp_aware=true
  elif [ -n "${AGENT_CONFIG_RULE_PACKS:-}" ]; then
    _rp_aware=true
  fi
  if ! $_rp_aware; then
    printf '\n' >&2
    printf 'tip: anywhere-agents ships with agent-style writing rules enabled by default,\n' >&2
    printf '     but this run skipped them (Python 3 with PyYAML unavailable).\n' >&2
    printf "     install Python + PyYAML to enable, or silence with 'rule_packs: []' in agent-config.yaml.\n" >&2
  fi
  _ledger_target AGENTS.md
  _ledger_step compose repo skipped
fi
# Generate per-agent config files (CLAUDE.md, agents/codex.md) from AGENTS.md.
# Generator preserves hand-authored files (no GENERATED header) and warns loudly.
# v0.5.8: in the compose-ok path the generator already ran inside the if block
# above. Only run here for the fallback path (Python/PyYAML unavailable) where
# $_compose_ok is false.
if ! $_compose_ok; then
  _run_generator "$_py"
fi
_record_generator_step
if [ -d .agent-config/repo/.claude/commands ]; then
  cp -f .agent-config/repo/.claude/commands/*.md .claude/commands/
  _ledger_target .claude/commands
fi
if [ -f .agent-config/repo/.claude/settings.json ]; then
  if [ -f .claude/settings.json ]; then
    if [ -n "$_py" ]; then
      "$_py" -c "
import json, pathlib as P
def dm(b,o):
 for k,v in o.items():
  if k in b and isinstance(b[k],dict) and isinstance(v,dict):dm(b[k],v)
  elif k in b and isinstance(b[k],list) and isinstance(v,list):b[k]=v if (v and isinstance(v[0],dict)) else list(dict.fromkeys(b[k]+v))
  else:b[k]=v
s=json.loads(P.Path('.agent-config/repo/.claude/settings.json').read_text())
p=json.loads(P.Path('.claude/settings.json').read_text())
dm(p,s)
P.Path('.claude/settings.json').write_text(json.dumps(p,indent=2)+'\n')
"
    fi
  else
    cp -f .agent-config/repo/.claude/settings.json .claude/settings.json
  fi
  _ledger_target .claude/settings.json
fi
_ledger_step project_files repo ok
# --- User-level setup: hooks and settings ---
# This section modifies ~/.claude/ (user-level, not project-level).
# It deploys a PreToolUse hook guard and merges shared permission settings.
# Remove this section if you do not want bootstrap to modify user-level config.
if [ -f .agent-config/repo/scripts/_python ]; then
  mkdir -p "$HOME/.claude/hooks"
  cp -f .agent-config/repo/scripts/_python "$HOME/.claude/hooks/_python"
  chmod +x "$HOME/.claude/hooks/_python" 2>/dev/null || true
  _ledger_target '~/.claude/hooks/_python'
fi
if [ -f .agent-config/repo/scripts/guard.py ]; then
  mkdir -p "$HOME/.claude/hooks"
  cp -f .agent-config/repo/scripts/guard.py "$HOME/.claude/hooks/guard.py"
  _ledger_target '~/.claude/hooks/guard.py'
fi
if [ -f .agent-config/repo/scripts/session_bootstrap.py ]; then
  mkdir -p "$HOME/.claude/hooks"
  cp -f .agent-config/repo/scripts/session_bootstrap.py "$HOME/.claude/hooks/session_bootstrap.py"
  _ledger_target '~/.claude/hooks/session_bootstrap.py'
fi
if [ -f .agent-config/repo/scripts/statusline.py ]; then
  mkdir -p "$HOME/.claude"
  cp -f .agent-config/repo/scripts/statusline.py "$HOME/.claude/statusline.py"
  _ledger_target '~/.claude/statusline.py'
fi
if [ -f .agent-config/repo/scripts/agent-quota.py ]; then
  mkdir -p "$HOME/.claude"
  cp -f .agent-config/repo/scripts/agent-quota.py "$HOME/.claude/agent-quota.py"
  _ledger_target '~/.claude/agent-quota.py'
fi
if [ -f .agent-config/repo/user/settings.json ]; then
  mkdir -p "$HOME/.claude"
  if [ -f "$HOME/.claude/settings.json" ]; then
    if [ -n "$_py" ]; then
      "$_py" -c "
import json, pathlib as P
def dm(b,o):
 for k,v in o.items():
  if k in b and isinstance(b[k],dict) and isinstance(v,dict):dm(b[k],v)
  elif k in b and isinstance(b[k],list) and isinstance(v,list):b[k]=v if (v and isinstance(v[0],dict)) else list(dict.fromkeys(b[k]+v))
  else:b[k]=v
s=json.loads(P.Path('.agent-config/repo/user/settings.json').read_text())
u=json.loads(P.Path(P.Path.home()/'.claude'/'settings.json').read_text())
dm(u,s)
P.Path(P.Path.home()/'.claude'/'settings.json').write_text(json.dumps(u,indent=2)+'\n')
"
    fi
  else
    cp -f .agent-config/repo/user/settings.json "$HOME/.claude/settings.json"
  fi
  _ledger_target '~/.claude/settings.json'
fi
# Heal legacy autoUpdates: false in ~/.claude.json. See bootstrap.ps1 comment
# for the why. To genuinely disable auto-updates, set DISABLE_AUTOUPDATER=1
# via the env block in ~/.claude/settings.json.
if [ -f "$HOME/.claude.json" ]; then
  if [ -n "$_py" ]; then
    "$_py" -c "
import json, os, pathlib as P, tempfile
p = P.Path.home() / '.claude.json'
try:
    d = json.loads(p.read_text())
    if d.get('autoUpdates') is False:
        d['autoUpdates'] = True
        # Best-effort heal. Atomic replace (tempfile.mkstemp + os.replace)
        # prevents a truncated config on interrupt but is NOT a cross-process
        # lock: a concurrent Claude Code write landing between our read and
        # replace will be clobbered by our older snapshot. Healed flag
        # reappears on the next session if that happens.
        fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix='.claude.json.', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(json.dumps(d, indent=2) + '\n')
            os.replace(tmp, str(p))
        except Exception:
            try:
                os.remove(tmp)
            except Exception:
                pass
            raise
except Exception:
    pass
"
  fi
  _ledger_target '~/.claude.json'
fi
_ledger_step user_files user ok

# Codex CLI has no native updater like Claude Code. If Codex is installed as
# the global npm package that this config recommends, keep it current during
# bootstrap. Set ANYWHERE_AGENTS_CODEX_AUTO_UPDATE=off to disable.
maybe_update_codex_cli
# No target here: maybe_update_codex_cli no-ops when Codex is not the global
# npm install or when ANYWHERE_AGENTS_CODEX_AUTO_UPDATE=off, so naming the
# package would imply an update that may not have happened.
_ledger_step external external ok

if [ ! -f .gitignore ] || ! grep -qE '^\/?\.agent-config/' .gitignore; then
  echo '.agent-config/' >> .gitignore
fi
# Rule-pack opt-in writes agent-config.local.yaml as a machine-local override
# that must not be committed. Auto-ignore it idempotently alongside .agent-config/.
if [ ! -f .gitignore ] || ! grep -qE '^\/?agent-config\.local\.yaml$' .gitignore; then
  echo 'agent-config.local.yaml' >> .gitignore
fi
# Self-update: copy the latest bootstrap script from the sparse clone over this
# one. Without this, a consumer that initially fetched an older bootstrap.sh
# stays on that version forever; future bootstrap improvements added upstream
# would never reach them automatically.
#
# v0.5.2 cross-OS fix: copy BOTH bootstrap.sh AND bootstrap.ps1. Previously
# the .sh entry only refreshed itself, so a Windows user running this bash
# entry on Git Bash / WSL would never land bootstrap.ps1 at all. Symmetric
# in bootstrap.ps1 (copies both). Cheap and covers cross-OS dev workflows.
if [ -f .agent-config/repo/bootstrap/bootstrap.sh ]; then
  cp -f .agent-config/repo/bootstrap/bootstrap.sh .agent-config/bootstrap.sh || \
    printf '%s\n' 'warning: could not self-update .agent-config/bootstrap.sh' >&2
fi
if [ -f .agent-config/repo/bootstrap/bootstrap.ps1 ]; then
  cp -f .agent-config/repo/bootstrap/bootstrap.ps1 .agent-config/bootstrap.ps1 || \
    printf '%s\n' 'warning: could not copy .agent-config/bootstrap.ps1' >&2
fi
_ledger_target .gitignore
_ledger_target .agent-config/bootstrap.sh
_ledger_target .agent-config/bootstrap.ps1
_ledger_step finalize repo ok
_ledger_write finalize true
