"""Run every ledger unit through `codex exec` in its scratch work folder, at most N at a time."""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "agent-io" / "ledger.json"
MODEL = "gpt-6-astra"  # the maintainer's configured Codex default, at its configured effort
EFFORT = "medium"
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4

ledger = json.loads(LEDGER.read_text())


def run(unit):
    work = ROOT / "agent-io" / "work" / unit["uid"]
    work.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with open(unit["prompt"]) as prompt:
        proc = subprocess.run(
            ["codex", "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
             "-m", MODEL, "-c", f'model_reasoning_effort="{EFFORT}"', "-s", "workspace-write",
             "-C", str(work), "-o", unit["result"], "-"],
            stdin=prompt, capture_output=True, text=True)
    unit.update(exit=proc.returncode, model_ran=MODEL, seconds=round(time.time() - start),
                stderr_tail=proc.stderr[-400:])
    print(f"{unit['uid']} exit={proc.returncode} {unit['seconds']}s", flush=True)
    return unit


with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    done = list(pool.map(run, ledger))
LEDGER.write_text(json.dumps(done, indent=1))
print("ALL-DONE", sum(1 for u in done if u.get("exit") == 0), "of", len(done), "exit 0")
