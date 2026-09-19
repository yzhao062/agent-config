"""The Milestone A acceptance measurement, as run on 2026-09-18.

Before: the eleven fire-ai-bench rollouts the audit sampled, under the old
contract. After: the four consumer rollouts that ran once the contract landed,
fire-ai-bench round 10 (root plus two sub-agents) and trading-doc round 3.

Both cohorts go through classify_reviewer_io.py with the scope lists below,
and then through a second pass that counts how much of each session's output
the reviewer had already been delivered. This recipe reproduces the two raw
tables in README.md and lists the flagged after events. It does not apply the
adjudication in README.md, which is a reading of those events by hand.

The rollouts live under ~/.codex/sessions and the audit sample under a session
scratchpad, so reproducing this exact pair means keeping those inputs. A new
pair needs new paths, session ids, a new date glob, and its own scopes. Here,
one PAPER_SCOPE stands in for every paper rollout instead of being taken from
each request separately.

Usage: python measure_acceptance.py [--events]
"""
from __future__ import annotations

import glob
import json
import os
import sys
import tempfile
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SP = Path(r"C:/Users/yuezh/AppData/Local/Temp/claude/C--Users-yuezh-PycharmProjects-agent-config/27c4fb45-bb69-43ab-9fbf-90ed9a022fd7/scratchpad")
OUT = Path(tempfile.mkdtemp(prefix="acceptance-"))

spec = importlib.util.spec_from_file_location("clf", HERE / "classify_reviewer_io.py")
clf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clf)

PAPER_SCOPE = [
    "sections", "figures", "main.tex", "main.bib", "refs.bib", "appendix",
    "models.py", "analysis", "probe_bedrock_caps.py", "run_tier1.ps1", "run_tier2.ps1",
    "pilot_tier1.ps1", "docs", "gw.py", "run_allocation.py", "run_mesogeos.py",
    "run_tooluse.py", "table_rows_new_models.py", "build_manifest.py", "tests",
    "README.md", "manifest-v1.json", "logs", "task-allocation", "task-tooluse",
    "task-aerial", "task-conservation", "scores.json",
]
TRADING_SCOPE = ["crypto"]

ROUNDS = {
    "after": [
        ("fire-ai-bench R10 root", "rollout-2026-09-18T19-22-49", PAPER_SCOPE),
        ("fire-ai-bench R10 sub-a", "rollout-2026-09-18T19-23-39", PAPER_SCOPE),
        ("fire-ai-bench R10 sub-b", "rollout-2026-09-18T19-27-37", PAPER_SCOPE),
        ("trading-doc R3", "rollout-2026-09-18T19-44-04", TRADING_SCOPE),
    ],
}

BEFORE_GLOB = str(SP / "prun-skills-audit/data/codex-rollouts/*.jsonl")

# A line counts as already delivered only when this many significant characters
# survive stripping a "NNN: " line-number prefix and the surrounding whitespace.
# Shorter lines (blank, a brace, a rule) match each other across unrelated files.
# A matching line contributes its own bytes including its terminator, so a corpus
# that mixes CRLF, LF, and unterminated final lines is counted as it stands.
MIN_SIG = 12


def round_json(scope, path):
    path.write_text(json.dumps({
        "backend": "codex",
        "supplied_instruction_files": ["AGENTS.md"],
        "review_scope": scope,
        "diff_transport": "command",
    }, indent=1), encoding="utf-8", newline="\n")
    return path


def line(label, t):
    tot = t["tool_output_total"]
    av = t["by_label"]["avoidable"]
    un = t["by_label"]["unresolved"]
    cs = t["by_class"].get("coordinator_skill", 0)
    ru = t["by_class"].get("rules", 0)
    pct = (av / tot * 100) if tot else 0
    return f"| {label} | {tot:,} | {av:,} ({pct:.1f}%) | {un:,} | {cs:,} | {ru:,} |"


# ------------------------------------------------------- the classifier pass

rows = []
for label, stem, scope in ROUNDS["after"]:
    hits = glob.glob(os.path.expanduser(f"~/.codex/sessions/2026/09/18/{stem}*.jsonl"))
    if not hits:
        print("missing:", stem)
        continue
    rj = round_json(scope, OUT / f"round-after-{stem[-8:]}.json")
    rep = clf.classify(hits[0], rj)
    rows.append((label, rep["totals"], rep, hits[0]))

before = []
for f in sorted(glob.glob(BEFORE_GLOB)):
    rj = round_json(PAPER_SCOPE, OUT / "round-before-paper.json")
    rep = clf.classify(f, rj)
    if rep["totals"]["tool_output_total"] == 0:
        continue  # the three probe rollouts
    before.append((os.path.basename(f)[8:24], rep["totals"], rep, f))

print("| round | tool output | avoidable | unresolved | coordinator_skill | rules |")
print("|---|---:|---:|---:|---:|---:|")
print("| **BEFORE (old contract, same paper, rounds 7-9)** | | | | | |")
for label, t, _, _ in before:
    print(line(label, t))


def totals(group):
    return {
        "tool_output_total": sum(t["tool_output_total"] for _, t, _, _ in group),
        "by_label": {
            "avoidable": sum(t["by_label"]["avoidable"] for _, t, _, _ in group),
            "unresolved": sum(t["by_label"]["unresolved"] for _, t, _, _ in group),
        },
        "by_class": {
            "coordinator_skill": sum(t["by_class"].get("coordinator_skill", 0)
                                     for _, t, _, _ in group),
            "rules": sum(t["by_class"].get("rules", 0) for _, t, _, _ in group),
        },
    }


print(line(f"**before total ({len(before)})**", totals(before)))
print("| **AFTER (new contract)** | | | | | |")
for label, t, _, _ in rows:
    print(line(label, t))
print(line(f"**after total ({len(rows)})**", totals(rows)))

print()
print("AFTER: every avoidable and unresolved event, for hand adjudication")
for label, t, rep, _ in rows:
    for r in rep["events"]:
        if r["label"] in ("avoidable", "unresolved"):
            print(f"  [{label}] {r['event_id']} {r['label']:10} {r['class']:18} {r['output_bytes']:>8} "
                  f"{(r['path'] or r['target'])[:90]} | {r['reason'][:70]}")


# ------------------------------------------------- the already-delivered pass

def command_events(path):
    """The CommandExecution items of one rollout, in order, as the classifier reads them."""
    out = []
    n = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "event_msg":
                continue
            item = (rec.get("payload") or {}).get("item")
            if isinstance(item, dict) and item.get("type") == "CommandExecution":
                out.append((f"c{n}", item))
                n += 1
    return out


def significant(text: str) -> str:
    s = text.rstrip()
    i = s.find(": ")
    if 0 < i <= 6 and s[:i].strip().isdigit():
        s = s[i + 2:]
    return s.strip()


def redelivered(path, label, show=False):
    """Raw bytes, delivered bytes, and bytes an earlier event already delivered.

    Repetition is measured against formatted_output, which is what the model
    received after Codex truncated a long response. Recovering content that a
    truncation dropped is therefore not counted as a repeat.
    """
    seen = set()
    raw_total = delivered_total = repeat = 0
    hits = []
    for eid, item in command_events(path):
        agg = str(item.get("aggregated_output") or "")
        fmt = str(item.get("formatted_output") or "")
        raw_total += len(agg.encode("utf-8"))
        delivered_total += len(fmt.encode("utf-8"))
        dup = 0
        for ln in agg.splitlines(keepends=True):
            t = significant(ln)
            if len(t) >= MIN_SIG and t in seen:
                dup += len(ln.encode("utf-8"))
        repeat += dup
        if dup:
            cmd = item.get("command")
            hits.append((eid, dup, len(agg.encode("utf-8")),
                         " ".join(cmd) if isinstance(cmd, list) else str(cmd)))
        for ln in fmt.splitlines():
            t = significant(ln)
            if len(t) >= MIN_SIG:
                seen.add(t)
    pct = repeat / raw_total * 100 if raw_total else 0
    print(f"| {label} | {raw_total:,} | {delivered_total:,} | {repeat:,} | {pct:.1f}% |")
    if show:
        for eid, dup, tot, cmd in sorted(hits, key=lambda r: -r[1])[:10]:
            print(f"      {eid:>4} already delivered {dup:>7,} of {tot:>7,}  {cmd[:100]}")
    return raw_total, delivered_total, repeat


print()
print("Content the reviewer had already been delivered")
print("| round | raw bytes | delivered bytes | already delivered | share of raw |")
print("|---|---:|---:|---:|---:|")
show_events = "--events" in sys.argv
for name, group in (("BEFORE (old contract)", before), ("AFTER (new contract)", rows)):
    print(f"| **{name}** | | | | |")
    gr = gd = gp = 0
    for label, _, _, path in group:
        a, d, p = redelivered(path, label, show_events)
        gr += a
        gd += d
        gp += p
    print(f"| **{name.split()[0].lower()} total ({len(group)})** | {gr:,} | {gd:,} | {gp:,} | "
          f"{gp / gr * 100 if gr else 0:.1f}% |")
