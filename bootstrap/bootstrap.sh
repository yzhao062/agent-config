# Let .gitattributes handle line endings; silence CRLF warnings on Windows
git config --global core.autocrlf false

mkdir -p .agent-config .claude/commands
curl -sfL https://raw.githubusercontent.com/yzhao062/agent-config/main/AGENTS.md -o .agent-config/AGENTS.md
cp -f .agent-config/AGENTS.md AGENTS.md
if [ -d .agent-config/repo/.git ]; then
  git -C .agent-config/repo pull --ff-only
else
  git clone --depth 1 --filter=blob:none --sparse https://github.com/yzhao062/agent-config.git .agent-config/repo
fi
git -C .agent-config/repo sparse-checkout set skills .claude scripts user
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
if [ ! -f .gitignore ] || ! grep -qx '\.agent-config/' .gitignore; then
  echo '.agent-config/' >> .gitignore
fi
