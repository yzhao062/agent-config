"""Write one prompt per unit under opaque unit ids, plus the ledger.

Round 1 (`python build.py`) is one run per (task, condition, model). Round 2 (`python build.py 2`)
adds Sonnet, runs the round-1 tasks once more, and runs each new task twice.
"""
import json
import random
import sys
from pathlib import Path

from tasks import BASE_RULES, CONDITIONS, MODELS, MODELS2, ROUND1_TASKS, ROUND2_NEW, TASKS

ROOT = Path(__file__).resolve().parent.parent
IO = ROOT / "agent-io"
ROUND = int(sys.argv[1]) if len(sys.argv) > 1 else 1

TEMPLATE = """\
You are working on a software and research project. The project rules below apply.

## Project rules

{rules}

## Task

{body}

## Reply format

{reply}

Begin your final reply with these five lines, then the content:
# {uid} result
Conclusion: <one line>
Files: none (read-only)
Open items: <blockers, or "none">
Verification: <what you ran or checked, or "none">
"""

if ROUND == 1:
    models, prefix, seed = MODELS, "u{:02d}", 20261025
    cells = [(t, c, m, 1) for t in ROUND1_TASKS for c in CONDITIONS for m in models]
else:
    models, prefix, seed = MODELS2, "v{:03d}", 20261026
    cells = ([(t, c, m, 1) for t in ROUND1_TASKS for c in CONDITIONS for m in models]
             + [(t, c, m, r) for t in ROUND2_NEW for c in CONDITIONS for m in models for r in (1, 2)])
random.Random(seed).shuffle(cells)
(IO / "prompts").mkdir(parents=True, exist_ok=True)
(IO / "results").mkdir(parents=True, exist_ok=True)
ledger = []
for i, (task, cond, model, rep) in enumerate(cells, 1):
    uid = prefix.format(i)
    rules = BASE_RULES + ("\n" + CONDITIONS[cond] if CONDITIONS[cond] else "")
    text = TEMPLATE.format(rules=rules, body=TASKS[task]["body"], reply=TASKS[task]["reply"], uid=uid)
    prompt = IO / "prompts" / f"{uid}.txt"
    prompt.write_text(text)
    ledger.append({"uid": uid, "round": ROUND, "rep": rep, "task": task, "condition": cond, "model": model,
                   "model_slug": models[model], "prompt": str(prompt),
                   "result": str(IO / "results" / f"{uid}.md")})
(IO / "ledger.json").write_text(json.dumps(ledger, indent=1))
print(len(ledger), "units")
