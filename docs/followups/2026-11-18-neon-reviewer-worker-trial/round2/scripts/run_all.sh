#!/usr/bin/env bash
# Round 2: launch all twelve reviews (six diffs, two arms) at once and wait for them.
# Each run records start and end epoch seconds, exit code, stdout, and stderr under <workdir>/agent-io/runs/<name>.*
# Usage: run_all.sh <workdir>
set -u
W="$1"; IO="$W/agent-io"; R="$IO/runs"; mkdir -p "$R"
HERE="$(cd "$(dirname "$0")/.." && pwd)"           # round2/
HEADER="$HERE/../prompts/header.txt"                # the round-1 header, unchanged
AC=/Users/yzhao062/PycharmProjects/agent-config
PY=/Users/yzhao062/miniforge3/envs/py312/bin/python
IRS=$AC/skills/implement-review/scripts

review() { # review <diff> <arm> <slug>
  local name="$1-$2" clone="$W/$1-$2"
  { cat "$HEADER"; sed "s#__REPO__#$clone#g" "$HERE/prompts/$1-body.txt"; } > "$IO/$name-prompt.txt"
  date +%s > "$R/$name.start"
  ( cd "$clone" && IMPLEMENT_REVIEW_ORCHESTRATOR=claude ANTIGRAVITY_DISPATCH_MODEL="$3" \
      "$PY" "$IRS/dispatch-gemini.py" --prompt-file "$IO/$name-prompt.txt" --round 1 \
      --expected-review-file Review-Antigravity.md ) > "$R/$name.out" 2> "$R/$name.err"
  echo $? > "$R/$name.exit"; date +%s > "$R/$name.end"
}

for d in d1 d2 d3 d4 c1 c2; do
  review "$d" carbon gemini-4-carbon-medium &
  review "$d" neon gemini-4-neon-high &
done
wait
for f in "$R"/*.exit; do
  n=$(basename "$f" .exit)
  conv=$(grep -o '"conversation_id":"[^"]*"' "$R/$n.err" | head -1 | cut -d'"' -f4)
  echo "$n exit=$(cat "$f") wall_s=$(( $(cat "$R/$n.end") - $(cat "$R/$n.start") )) conversation=$conv"
done | tee "$R/summary.txt"
