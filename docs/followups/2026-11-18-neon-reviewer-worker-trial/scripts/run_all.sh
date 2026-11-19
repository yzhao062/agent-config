#!/usr/bin/env bash
# Launch every arm of the Neon trial in parallel and wait for all of them.
# Each run records start/end epoch seconds, exit code, stdout, and stderr under agent-io/runs/<name>.*
set -u
N="$(cd "$(dirname "$0")" && pwd)"; IO="$N/agent-io"; R="$IO/runs"; mkdir -p "$R"
AC=/Users/yzhao062/PycharmProjects/agent-config
PY=/Users/yzhao062/miniforge3/envs/py312/bin/python
IRS=$AC/skills/implement-review/scripts; PRS=$AC/skills/prun/scripts

stamp() { date +%s > "$R/$1.start"; }
finish() { echo "$2" > "$R/$1.exit"; date +%s > "$R/$1.end"; }

review() { # review <name> <clone> <body> <model>
  local name=$1 clone=$2 body=$3 model=$4
  { cat "$IO/header.txt"; sed "s#__REPO__#$clone#g" "$IO/$body"; } > "$IO/$name-prompt.txt"
  stamp "$name"
  ( cd "$clone" && IMPLEMENT_REVIEW_ORCHESTRATOR=claude ANTIGRAVITY_DISPATCH_MODEL="$model" \
      "$PY" "$IRS/dispatch-gemini.py" --prompt-file "$IO/$name-prompt.txt" --round 1 \
      --expected-review-file Review-Antigravity.md ) > "$R/$name.out" 2> "$R/$name.err"
  finish "$name" $?
}

unit() { # unit <name> <prompt> <model> [clone]
  local name=$1 prompt=$2 model=$3 clone=${4:-}
  stamp "$name"
  if [ -n "$clone" ]; then
    PRUN_SCRATCH_CWD="$clone" PRUN_STALL_THRESHOLD=1200 ANTIGRAVITY_DISPATCH_MODEL="$model" \
      "$PY" "$PRS/dispatch-task-agy.py" --prompt-file "$IO/$prompt" --result-file "$IO/results/$name.md" \
      --unit-id "$name" --mode accept-edits > "$R/$name.out" 2> "$R/$name.err"
  else
    ANTIGRAVITY_DISPATCH_MODEL="$model" \
      "$PY" "$PRS/dispatch-task-agy.py" --prompt-file "$IO/$prompt" --result-file "$IO/results/$name.md" \
      --unit-id "$name" > "$R/$name.out" 2> "$R/$name.err"
  fi
  finish "$name" $?
}

swarm() { # one Agy process on Neon running /swarm headless, env scrubbed like worker_env()
  local name=swarm-neon clone="$N/swarm-neon"
  sed "s#__RESULT__#$IO/results/swarm-neon.md#g" "$IO/swarm.md" > "$IO/swarm-prompt.txt"
  stamp "$name"
  ( cd "$clone" && "$PY" - "$IO/swarm-prompt.txt" "$R/$name.agy.log" <<'PYEOF'
import os, re, subprocess, sys
prompt = open(sys.argv[1]).read()
drop = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|APIKEY|AUTH")
env = {k: v for k, v in os.environ.items()
       if k.startswith("ANTIGRAVITY_") or not (drop.search(k) or k.startswith("AWS_"))}
cmd = ["agy", "-p", prompt, "--model", "gemini-4-neon-high", "--effort", "high",
       "--mode", "accept-edits", "--dangerously-skip-permissions",
       "--output-format", "stream-json", "--print-timeout", "2700s", "--log-file", sys.argv[2]]
sys.exit(subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL).returncode)
PYEOF
  ) > "$R/$name.out" 2> "$R/$name.err"
  finish "$name" $?
}

mkdir -p "$IO/results"
review vseed-carbon "$N/vseed-carbon" seed-body.txt gemini-4-carbon-medium &
review vseed-neon   "$N/vseed-neon"   seed-body.txt gemini-4-neon-high &
review vclean-carbon "$N/vclean-carbon" clean-body.txt gemini-4-carbon-medium &
review vclean-neon   "$N/vclean-neon"   clean-body.txt gemini-4-neon-high &
unit u1-hydrogen u1.md gemini-4-hydrogen-high "$N/u1-hydrogen" &
unit u1-neon     u1.md gemini-4-neon-high     "$N/u1-neon" &
unit u2-hydrogen u2.md gemini-4-hydrogen-high &
unit u2-neon     u2.md gemini-4-neon-high &
unit u3-hydrogen u3.md gemini-4-hydrogen-high "$N/u3-hydrogen" &
unit u3-neon     u3.md gemini-4-neon-high     "$N/u3-neon" &
swarm &
wait
for f in "$R"/*.exit; do n=$(basename "$f" .exit); echo "$n exit=$(cat "$f") secs=$(( $(cat "$R/$n.end") - $(cat "$R/$n.start") ))"; done
