#!/usr/bin/env bash
# Build pinned throwaway clones of agent-config for the Neon trial. No remote.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"; ac=/Users/yzhao062/PycharmProjects/agent-config
mk() { # mk <dir> <rev>
  git clone -q --local "$ac" "$here/$1"; git -C "$here/$1" checkout -q --detach "$2"; git -C "$here/$1" remote remove origin
}
replay() { # replay <dir> <commit>: check out the parent, stage the commit's diff
  mk "$1" "$2^"; git -C "$ac" diff --binary "$2^" "$2" | git -C "$here/$1" apply --index
}
replay vseed-carbon 0878a02; replay vseed-neon 0878a02
replay vclean-carbon 011410a; replay vclean-neon 011410a
for d in u1-hydrogen u1-neon u3-hydrogen u3-neon swarm-neon; do mk "$d" 53f9c17; done
ls "$here"
