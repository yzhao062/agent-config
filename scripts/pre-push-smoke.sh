#!/usr/bin/env bash
# pre-push-smoke.sh — real-agent smoke for the CURRENT checkout.
#
# Unlike scripts/remote-smoke.sh (which tests the published package from
# PyPI / npm), this script validates the exact commit being pushed:
#
#   1. Generator determinism: regenerate CLAUDE.md / agents/codex.md in a
#      temp dir from the committed AGENTS.md and diff against the
#      committed generated files. Catches stale generator output that
#      could silently ship.
#   2. Claude Code: if `claude` is on PATH, two single-turn probes from
#      the repo root. The config probe runs with every tool disabled and
#      asks which skill `/vet` aliases; only the committed CLAUDE.md says
#      `implement-review`, so the answer proves the file was loaded. The
#      roster probe asks for the directories under skills/ that hold a
#      SKILL.md and asserts every shipped skill is named. The rules file
#      carries no roster since the 2026-09 rewrite; the tree is the
#      source, and the probe shows the agent can reach it.
#   3. Codex: if `codex` is on PATH, the same two probes through
#      `codex exec`, the config probe worded to forbid tool use.
#
# Agent calls are SKIPPED (not failed) when the corresponding CLI is
# missing, so the script is useful on machines that have only one agent
# configured. The generator-determinism check always runs.
#
# Called by .githooks/pre-push. Can also be invoked manually:
#   bash scripts/pre-push-smoke.sh

set -uo pipefail

red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

pass()  { green "PASS: $*"; }
fail()  { red   "FAIL: $*"; exit 1; }
skip()  { yellow "SKIP: $*"; }

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

# Auto-detect shipped skills from the skills/ directory. Keeps this
# script in sync with whatever the repo actually ships without a
# hardcoded list that could drift.
EXPECTED_SKILLS=()
if [ -d skills ]; then
  for d in skills/*/; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    [ -f "$d/SKILL.md" ] || continue
    EXPECTED_SKILLS+=("$name")
  done
fi
if [ "${#EXPECTED_SKILLS[@]}" -eq 0 ]; then
  fail "no shipped skills found under skills/"
fi

# The config probe's answer is stated by the shared rules file ("`vet` is
# the alias for `implement-review`"), so a fork that drops that line skips
# the probe instead of failing it.
CONFIG_PROMPT="Without running any command or reading any file: according to your project instructions (CLAUDE.md or AGENTS.md), /vet is an alias of which skill? Reply with that skill's directory name only."
CONFIG_EXPECT="implement-review"
ROSTER_PROMPT="List the skills shipped in this repository, meaning the directories under skills/ that contain a SKILL.md. Reply with the directory names only, comma-separated, no other text."
if grep -q 'is the alias for `implement-review`' AGENTS.md; then
  CONFIG_PROBE=1
else
  CONFIG_PROBE=0
fi

echo "== pre-push-smoke in $(pwd) =="
echo "Expected skills: ${EXPECTED_SKILLS[*]}"
echo ""

# --- 1. Generator determinism --------------------------------------------
echo "[1/3] Generator output matches committed per-agent files"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

if [ ! -f scripts/generate_agent_configs.py ]; then
  skip "scripts/generate_agent_configs.py not found in this repo; skipping determinism check"
else
  cp AGENTS.md "$TMPDIR/AGENTS.md"
  # Prefer the shipped _python wrapper, which filters out Windows
  # Store python.exe shims that resolve ahead of real interpreters via
  # %LOCALAPPDATA%\Microsoft\WindowsApps\. Falls back to PATH discovery
  # on systems where the wrapper is missing or non-executable.
  if [ -x "scripts/_python" ]; then
    _py="scripts/_python"
  else
    _py=$(command -v python3 || command -v python || true)
  fi
  if [ -z "$_py" ]; then
    fail "python not on PATH; cannot run generator"
  fi
  "$_py" scripts/generate_agent_configs.py --root "$TMPDIR" --quiet

  for f in CLAUDE.md agents/codex.md; do
    if [ ! -f "$f" ]; then
      fail "$f is missing in the checkout (generator output is tracked)"
    fi
    if ! diff -q "$TMPDIR/$f" "$f" >/dev/null 2>&1; then
      red "FAIL: committed $f does not match generator output."
      red "      Run: python scripts/generate_agent_configs.py --root ."
      exit 1
    fi
    pass "$f matches generator output"
  done
fi

# --- 2. Claude Code -------------------------------------------------------
echo ""
echo "[2/3] Claude Code single-turn: config probe, then skill roster"
if command -v claude >/dev/null 2>&1; then
  if [ "$CONFIG_PROBE" = 1 ]; then
    # --tools "" leaves the model nothing but its loaded instructions. It
    # is variadic, so it comes after the prompt or it swallows it.
    resp=$(claude -p "$CONFIG_PROMPT" --tools "" </dev/null 2>&1 || true)
    printf 'config probe response:\n%s\n' "$resp"
    if ! grep -q "$CONFIG_EXPECT" <<<"$resp"; then
      fail "Claude did not answer $CONFIG_EXPECT from CLAUDE.md (is the file loaded?)"
    fi
    pass "Claude answered the config probe from CLAUDE.md"
  else
    skip "AGENTS.md does not state the vet alias; config probe skipped"
  fi
  resp=$(claude -p "$ROSTER_PROMPT" </dev/null 2>&1 || true)
  printf 'roster response:\n%s\n' "$resp"
  missing=()
  for s in "${EXPECTED_SKILLS[@]}"; do
    if ! grep -q "$s" <<<"$resp"; then
      missing+=("$s")
    fi
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    fail "Claude response missing skills: ${missing[*]}"
  fi
  pass "Claude mentioned all ${#EXPECTED_SKILLS[@]} shipped skills"
else
  skip "claude CLI not on PATH; skipping Claude agent test"
fi

# --- 3. Codex -------------------------------------------------------------
echo ""
echo "[3/3] Codex single-turn: config probe, then skill roster"
if command -v codex >/dev/null 2>&1; then
  if [ "$CONFIG_PROBE" = 1 ]; then
    resp=$(codex exec "$CONFIG_PROMPT" </dev/null 2>&1 || true)
    printf 'config probe response:\n%s\n' "$resp"
    if ! grep -q "$CONFIG_EXPECT" <<<"$resp"; then
      fail "Codex did not answer $CONFIG_EXPECT from AGENTS.md (is the file loaded?)"
    fi
    pass "Codex answered the config probe from AGENTS.md"
  else
    skip "AGENTS.md does not state the vet alias; config probe skipped"
  fi
  resp=$(codex exec "$ROSTER_PROMPT" </dev/null 2>&1 || true)
  printf 'roster response:\n%s\n' "$resp"
  missing=()
  for s in "${EXPECTED_SKILLS[@]}"; do
    if ! grep -q "$s" <<<"$resp"; then
      missing+=("$s")
    fi
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    fail "Codex response missing skills: ${missing[*]}"
  fi
  pass "Codex mentioned all ${#EXPECTED_SKILLS[@]} shipped skills"
else
  skip "codex CLI not on PATH; skipping Codex agent test"
fi

echo ""
green "== pre-push-smoke: ALL PASSED =="
