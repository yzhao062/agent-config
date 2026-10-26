"""Merge Workflow judge results into agent-io/judge.json, keyed by unit id, for score.py.

Usage: python merge_judge.py <judge result.json> [...]. Each file holds the workflow's return value, or
part of it: a writing judge {"outputs": [...]}, or a dict with "judge" and "summary" entries.
"""
import json
import sys
from pathlib import Path

IO = Path(__file__).resolve().parent.parent / "agent-io"
merged = {}
for path in sys.argv[1:]:
    data = json.loads(Path(path).read_text())
    data = data.get("result", data)
    parts = [data] if "outputs" in data else [data.get("judge"), data.get("summary")]
    for part in filter(None, parts):
        for o in part["outputs"]:
            if "items" in o:
                merged[o["id"]] = {"items": {i["item"]: i["status"] for i in o["items"]},
                                   "facts_lost": len(o["facts_lost"]), "facts_lost_list": o["facts_lost"],
                                   "new_hedges": o["new_hedges"], "notes": o["notes"]}
            else:
                merged[o["id"]] = {"drop_stated": o["drop_stated"], "accuracy_errors": len(o["accuracy_errors"]),
                                   "filler_caveats": len(o["filler_caveats"]), "filler_list": o["filler_caveats"],
                                   "sentences": o["sentences"], "notes": o["notes"]}
(IO / "judge.json").write_text(json.dumps(merged, indent=1))
print(len(merged), "units judged")
