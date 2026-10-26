"""Copy the round-2 Sonnet prompts for a few tasks into units for another harness.

Usage: python build_cc.py <round-2 ledger.json> [label prefix task ...]. With no label, it builds the
Claude Code Workflow set (sonnet-cc, w01-w09); the Codex set is `codex x triage-paper ...`. The prompt
text is the Agy prompt verbatim, under a new unit id, plus one line that keeps the agent out of the
repository it starts in.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IO = ROOT / "agent-io"
if len(sys.argv) > 2:
    LABEL, PREFIX, TASKS_CC = sys.argv[2], sys.argv[3], tuple(sys.argv[4:])
else:
    LABEL, PREFIX, TASKS_CC = "sonnet-cc", "w", ("triage-paper", "exp-leak", "open-config")
NOTE = ("Work from this prompt alone; do not read repository files or skills. If you create files to "
        "test code, create them only under {work}.\n\n")

source = json.loads(Path(sys.argv[1]).read_text())
picked = sorted((u for u in source if u["model"] == "sonnet" and u["task"] in TASKS_CC and u["rep"] == 1),
                key=lambda u: u["uid"])
(IO / "prompts").mkdir(parents=True, exist_ok=True)
(IO / "results").mkdir(parents=True, exist_ok=True)
ledger = []
for i, u in enumerate(picked, 1):
    uid = f"{PREFIX}{i:02d}"
    work = IO / "work" / uid
    work.mkdir(parents=True, exist_ok=True)
    text = Path(u["prompt"]).read_text().replace(f"# {u['uid']} result", f"# {uid} result")
    prompt = IO / "prompts" / f"{uid}.txt"
    prompt.write_text(NOTE.format(work=work) + text)
    ledger.append({"uid": uid, "round": 2, "rep": 1, "task": u["task"], "condition": u["condition"],
                   "model": LABEL, "agy_twin": u["uid"], "prompt": str(prompt),
                   "result": str(IO / "results" / f"{uid}.md")})
(IO / "ledger.json").write_text(json.dumps(ledger, indent=1))
print(len(ledger), "units:", [(u["uid"], u["task"], u["condition"]) for u in ledger])
