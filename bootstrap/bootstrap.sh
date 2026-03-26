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
git -C .agent-config/repo sparse-checkout set skills .claude
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
  elif k in b and isinstance(b[k],list) and isinstance(v,list):b[k]=list(dict.fromkeys(b[k]+v))
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
if [ ! -f .gitignore ] || ! grep -qx '\.agent-config/' .gitignore; then
  echo '.agent-config/' >> .gitignore
fi
