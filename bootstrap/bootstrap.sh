# Let .gitattributes handle line endings; silence CRLF warnings on Windows

# Upstream cascade: argv > env var > persisted file > hardcoded default.
# Forkers can persist a different default in their fork; consumers can pass
# upstream via `bash .agent-config/bootstrap.sh <user>/<repo>` or the
# $AGENT_CONFIG_UPSTREAM environment variable.
UPSTREAM=""
if [ -n "${1:-}" ]; then
  UPSTREAM="$1"
elif [ -n "${AGENT_CONFIG_UPSTREAM:-}" ]; then
  UPSTREAM="$AGENT_CONFIG_UPSTREAM"
elif [ -f .agent-config/upstream ]; then
  UPSTREAM="$(tr -d '\r\n' < .agent-config/upstream)"
fi
UPSTREAM="${UPSTREAM:-yzhao062/agent-config}"
mkdir -p .agent-config
printf '%s' "$UPSTREAM" > .agent-config/upstream

git config --global core.autocrlf false

mkdir -p .agent-config .claude/commands
curl -sfL "https://raw.githubusercontent.com/$UPSTREAM/main/AGENTS.md" -o .agent-config/AGENTS.md
cp -f .agent-config/AGENTS.md AGENTS.md
REPO_URL="https://github.com/$UPSTREAM.git"
if [ -d .agent-config/repo/.git ]; then
  git -C .agent-config/repo remote set-url origin "$REPO_URL"
  git -C .agent-config/repo pull --ff-only
else
  git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" .agent-config/repo
fi
git -C .agent-config/repo sparse-checkout set skills .claude scripts user bootstrap
# Generate per-agent config files (CLAUDE.md, agents/codex.md) from AGENTS.md.
# Generator preserves hand-authored files (no GENERATED header) and warns loudly.
if [ -f .agent-config/repo/scripts/generate_agent_configs.py ]; then
  _py=$(command -v python3 || command -v python)
  if [ -n "$_py" ]; then
    "$_py" .agent-config/repo/scripts/generate_agent_configs.py --root . --quiet || true
  fi
fi
if [ -d .agent-config/repo/.claude/commands ]; then
  cp -f .agent-config/repo/.claude/commands/*.md .claude/commands/
fi
if [ -f .agent-config/repo/.claude/settings.json ]; then
  if [ -f .claude/settings.json ]; then
    _py=$(command -v python3 || command -v python)
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
fi
# --- User-level setup: hooks and settings ---
# This section modifies ~/.claude/ (user-level, not project-level).
# It deploys a PreToolUse hook guard and merges shared permission settings.
# Remove this section if you do not want bootstrap to modify user-level config.
if [ -f .agent-config/repo/scripts/guard.py ]; then
  mkdir -p "$HOME/.claude/hooks"
  cp -f .agent-config/repo/scripts/guard.py "$HOME/.claude/hooks/guard.py"
fi
if [ -f .agent-config/repo/scripts/session_bootstrap.py ]; then
  mkdir -p "$HOME/.claude/hooks"
  cp -f .agent-config/repo/scripts/session_bootstrap.py "$HOME/.claude/hooks/session_bootstrap.py"
fi
if [ -f .agent-config/repo/user/settings.json ]; then
  mkdir -p "$HOME/.claude"
  if [ -f "$HOME/.claude/settings.json" ]; then
    _py=$(command -v python3 || command -v python)
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
fi
# Heal legacy autoUpdates: false in ~/.claude.json. See bootstrap.ps1 comment
# for the why. To genuinely disable auto-updates, set DISABLE_AUTOUPDATER=1
# via the env block in ~/.claude/settings.json.
if [ -f "$HOME/.claude.json" ]; then
  _py=$(command -v python3 || command -v python)
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
fi

if [ ! -f .gitignore ] || ! grep -qE '^\/?\.agent-config/' .gitignore; then
  echo '.agent-config/' >> .gitignore
fi
# Self-update: copy the latest bootstrap script from the sparse clone over this
# one. Without this, a consumer that initially fetched an older bootstrap.sh
# stays on that version forever; future bootstrap improvements added upstream
# would never reach them automatically.
if [ -f .agent-config/repo/bootstrap/bootstrap.sh ]; then
  cp -f .agent-config/repo/bootstrap/bootstrap.sh .agent-config/bootstrap.sh || \
    printf '%s\n' 'warning: could not self-update .agent-config/bootstrap.sh' >&2
fi
