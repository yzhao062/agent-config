"""Score every unit against the labels and write agent-io/scores.json; report.py prints the tables."""
import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from tasks import LABELS

ROOT = Path(__file__).resolve().parent.parent
IO = ROOT / "agent-io"
HIDDEN = ROOT / "hidden"
CODE = IO / "code"
JUDGE = IO / "judge.json"

ledger = json.loads((IO / "ledger.json").read_text())
judge = json.loads(JUDGE.read_text()) if JUDGE.exists() else {}

# task: (file under test, the unit's own test file, hidden test)
CODE_FILES = {
    "code-merge": ("merge.py", "test_merge.py", "test_merge_hidden.py"),
    "code-hook": ("hook.py", "test_hook.py", "test_hook_hidden.py"),
    "open-config": ("config.py", "test_config.py", "test_config_hidden.py"),
    "open-count": ("count_lines.py", "test_count_lines.py", "test_count_hidden.py"),
}

KEYWORDS = {
    "Q1": r"generali[sz]", "Q3": r"further work", "Q5": r"confound",
    "Q2": r"iForest", "Q4": r"natural",
    "R1": r"may fail|may vary", "R3": r"guarantee|tried our best", "R5": r"back up|backup",
    "R2": r"3\.10", "R4": r"libomp",
}


def last_block(text, lang):
    blocks = re.findall(r"```" + lang + r"\s*\n(.*?)```", text, re.S)
    return blocks[-1] if blocks else None


def text_blocks(text):
    """Every ```text block, whole: a unit may add a separate Limitations block or nest ```sh blocks inside one."""
    blocks, cur, depth = [], None, 0
    for line in text.splitlines():
        fence = line.strip()
        if cur is None:
            if fence == "```text":
                cur = []
        elif fence == "```" and depth == 0:
            blocks.append("\n".join(cur))
            cur = None
        else:
            if fence.startswith("```"):
                depth += 1 if fence != "```" else -1
            cur.append(line)
    return blocks


def score_decisions(unit, text):
    lab = LABELS[unit["task"]]
    pos_key, neg_key = ("fix", "decline") if "fix" in lab else ("run", "skip")
    raw = last_block(text, "json")
    try:
        got = {k.strip(): str(v).strip().lower() for k, v in json.loads(raw).items()}
    except Exception:
        return {"parse_error": True}
    over = [i for i in lab[neg_key] if got.get(i) == pos_key]
    under = [i for i in lab[pos_key] if got.get(i) == neg_key]
    missing = [i for i in lab[pos_key] + lab[neg_key] if got.get(i) not in (pos_key, neg_key)]
    trap_wrong = [i for i in lab["trap"] if i in under or i in over]
    return {"over": over, "under": under, "missing": missing, "trap_wrong": trap_wrong,
            "errors": len(over) + len(under) + len(missing)}


def code_metrics(src):
    tree = ast.parse(src)
    nodes = list(ast.walk(tree))
    lines = [ln for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return {"try": sum(isinstance(n, ast.Try) for n in nodes),
            "raise": sum(isinstance(n, ast.Raise) for n in nodes),
            "isinstance": sum(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "isinstance" for n in nodes),
            "if": sum(isinstance(n, ast.If) for n in nodes),
            "funcs": sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in nodes),
            "loc": len(lines)}


def score_code(unit, text):
    main, test, hidden = CODE_FILES[unit["task"]]
    files = dict(re.findall(r"FILE:\s*`?([\w.]+)`?\s*\n```\w*\s*\n(.*?)```", text, re.S))
    if main not in files:
        return {"parse_error": True}
    d = CODE / unit["uid"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for name, body in files.items():
        (d / name).write_text(body)
    shutil.copy(HIDDEN / hidden, d / hidden)
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", hidden],
                          cwd=d, capture_output=True, text=True, timeout=120)
    passed = re.search(r"(\d+) passed", proc.stdout)
    failed = re.search(r"(\d+) failed", proc.stdout)
    out = {"hidden_ok": proc.returncode == 0,
           "hidden_passed": int(passed.group(1)) if passed else 0,
           "hidden_failed": int(failed.group(1)) if failed else 0}
    try:
        out.update(code_metrics(files[main]))
    except SyntaxError:
        out["syntax_error"] = True
    t = files.get(test, "")
    out["test_loc"] = len([ln for ln in t.splitlines() if ln.strip()])
    out["test_count"] = len(re.findall(r"^\s*def test_", t, re.M))
    out["mocks"] = len(re.findall(r"unittest\.mock|monkeypatch|MagicMock|mock\.patch|patch\(", t))
    if "ideal" in LABELS[unit["task"]]:
        out["excess_try"] = max(0, out.get("try", 0) - LABELS[unit["task"]]["ideal"]["try"])
    return out


def score_writing(unit, text):
    blocks = text_blocks(text)
    if not blocks:
        return {"parse_error": True}
    block = "\n\n".join(blocks)
    lab = LABELS[unit["task"]]
    j = judge.get(unit["uid"])
    if "must_mention" in lab:
        res = {"words": len(re.findall(r"\w+", block)),
               "sentences": len(re.findall(r"[.!?](?:\s|$)", block.strip())),
               "mentions": bool(re.search(lab["must_mention"], block, re.I))}
        if j:
            res["judge"] = j
        return res
    kw = {q: bool(re.search(KEYWORDS[q], block, re.I)) for q in list(lab["keep"]) + list(lab["cut"])}
    res = {"kw_present": kw, "words": len(re.findall(r"\w+", block))}
    res["kw_errors"] = sum(not kw[q] for q in lab["keep"]) + sum(kw[q] for q in lab["cut"])
    if j:
        res["judge"] = j
        res["errors"] = (sum(j["items"].get(q) != "kept" for q in lab["keep"])
                         + sum(j["items"].get(q) == "kept" for q in lab["cut"]))
        res["facts_lost"] = j.get("facts_lost", 0)
    return res


def main():
    rows = []
    for u in ledger:
        path = Path(u["result"])
        text = path.read_text() if path.exists() else ""
        row = {k: u.get(k) for k in ("uid", "round", "rep", "task", "condition", "model", "model_ran", "exit", "seconds")}
        lab = LABELS[u["task"]]
        if not text or text.lstrip().startswith("FALLBACK") or "# FALLBACK" in text[:200]:
            row["failed"] = True
        elif "fix" in lab or "run" in lab:
            row.update(score_decisions(u, text))
        elif u["task"] in CODE_FILES:
            row.update(score_code(u, text))
        else:
            row.update(score_writing(u, text))
        rows.append(row)
    (IO / "scores.json").write_text(json.dumps(rows, indent=1))
    bad = [r["uid"] for r in rows if r.get("failed") or r.get("parse_error")]
    print(len(rows), "units scored; failed or unparsed:", bad or "none")


if __name__ == "__main__":
    main()
