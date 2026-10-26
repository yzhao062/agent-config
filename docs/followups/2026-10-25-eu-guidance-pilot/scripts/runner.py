"""Dispatch every ledger unit to Agy through prun's dispatcher, at most N at a time."""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "agent-io" / "ledger.json"
DISPATCH = "/Users/yzhao062/PycharmProjects/agent-config/skills/prun/scripts/dispatch-task-agy.py"
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None

ledger = json.loads(LEDGER.read_text())


def run(unit):
    if only and unit["uid"] not in only:
        return unit
    env = dict(os.environ, ANTIGRAVITY_DISPATCH_MODEL=unit["model_slug"])
    start = time.time()
    proc = subprocess.run(
        [sys.executable, DISPATCH, "--prompt-file", unit["prompt"],
         "--result-file", unit["result"], "--unit-id", unit["uid"]],
        env=env, capture_output=True, text=True)
    state = next((line.split(" ", 1)[1] for line in proc.stdout.splitlines()
                  if line.startswith("STATE-DIR ")), None)
    ran = Path(state, "model").read_text().strip() if state and Path(state, "model").exists() else None
    unit.update(exit=proc.returncode, state_dir=state, model_ran=ran,
                seconds=round(time.time() - start), stderr_tail=proc.stderr[-400:])
    print(f"{unit['uid']} exit={proc.returncode} model={ran} {unit['seconds']}s", flush=True)
    return unit


with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    done = list(pool.map(run, ledger))
LEDGER.write_text(json.dumps(done, indent=1))
print("ALL-DONE", sum(1 for u in done if u.get("exit") == 0), "of", len(done), "exit 0")
