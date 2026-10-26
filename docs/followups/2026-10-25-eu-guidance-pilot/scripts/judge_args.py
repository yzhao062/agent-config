"""Build the Workflow args: blinded writing outputs per task, plus the task set for the label audit.

`python judge_args.py 2` adds the open release summary and audits the four round-2 decision tasks.
"""
import json
import sys
from pathlib import Path

from score import text_blocks
from tasks import LABELS, TASKS

ROOT = Path(__file__).resolve().parent.parent
IO = ROOT / "agent-io"
ROUND = int(sys.argv[1]) if len(sys.argv) > 1 else 1
ledger = json.loads((IO / "ledger.json").read_text())


def outputs(task):
    outs = []
    for u in sorted((u for u in ledger if u["task"] == task), key=lambda u: u["uid"]):
        p = Path(u["result"])
        text = p.read_text() if p.exists() else ""
        blocks = text_blocks(text)
        if blocks:
            outs.append({"id": u["uid"], "text": "\n\n".join(b.strip() for b in blocks)})
    return outs


writing = []
for task in ("writing-results", "writing-readme"):
    lab = LABELS[task]
    items = {**lab["keep"], **lab["cut"]}
    writing.append({"task": task, "original": TASKS[task]["body"], "items": items,
                    "facts": lab["facts"], "outputs": outputs(task)})

if ROUND == 1:
    audit_tasks = ("triage-code", "triage-paper", "exp-ml", "exp-agent", "writing-results", "writing-readme")
    args = {"writing": writing}
else:
    audit_tasks = ("check-paper", "check-commit", "migration", "exp-leak")
    args = {"writing": writing,
            "summary": {"task": TASKS["open-summary"]["body"], "outputs": outputs("open-summary")}}
args["audit"] = [{"task": t, "body": TASKS[t]["body"]} for t in audit_tasks]
(IO / "judge-args.json").write_text(json.dumps(args, indent=1))
print({w["task"]: len(w["outputs"]) for w in writing},
      "summary:", len(args["summary"]["outputs"]) if "summary" in args else 0, "audit tasks:", len(args["audit"]))
