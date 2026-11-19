#!/usr/bin/env bash
# Round 2: build pinned throwaway clones of agent-config under <workdir>, one per diff and arm,
# each checked out at <commit>^ with the commit's diff staged. No remote. Then run seed.py.
# Usage: setup.sh <workdir>
set -eu
work="$1"; ac=/Users/yzhao062/PycharmProjects/agent-config
mkdir -p "$work"
replay() { # replay <dir> <commit>
  git clone -q --local "$ac" "$work/$1"
  git -C "$work/$1" checkout -q --detach "$2^"
  git -C "$work/$1" remote remove origin
  git -C "$ac" diff --binary "$2^" "$2" | git -C "$work/$1" apply --index
}
for arm in carbon neon; do
  replay "d1-$arm" 15e383d   # agent_models.py map: panel gaps
  replay "d2-$arm" 37b9b26   # Agy rows to Hydrogen; xhigh slug sets the effort
  replay "d3-$arm" 932bd74   # GROK_HOME ~ expansion; Grok executor reference corrected
  replay "d4-$arm" d3aac68   # absent Claude quota window left out
  replay "c1-$arm" 5ed589b   # Grok fast model in every role (clean)
  replay "c2-$arm" ee57b98   # /vet reviewer set in checklist step 3 (clean)
done
