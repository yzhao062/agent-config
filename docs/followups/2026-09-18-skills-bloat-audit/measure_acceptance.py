"""The Milestone A acceptance measurement, as run on 2026-09-18.

Before: the eleven fire-ai-bench rollouts the audit sampled, under the old
contract. After: the four consumer rollouts that ran once the contract landed,
fire-ai-bench round 10 (root plus two sub-agents) and trading-doc round 3.

Both cohorts go through classify_reviewer_io.py with the scope lists below,
and then through a second pass that counts how much of each session's output
the reviewer had already been delivered. This recipe reproduces the two raw
tables in README.md and lists the flagged after events. It does not apply the
adjudication in README.md, which is a reading of those events by hand.

corpus-manifest.json beside this file states the cohort: every input by session
stem and SHA-256, and which of them the published table counts. Both cohorts
are resolved by stem under one corpus root, so neither depends on a session
scratchpad and neither can absorb an unrelated rollout that happens to share a
date. A missing, ambiguous, or hash-mismatched input ends the run with a
nonzero exit rather than a table that is quietly short.

The default root is ~/.codex/sessions, which is per-machine application storage
that can be archived or pruned. Point the measurement at a frozen copy with
--corpus-dir <path> or ACCEPTANCE_CORPUS_DIR. A new pair needs new session ids,
its own scopes, and its own manifest. Here, one PAPER_SCOPE stands in for every
paper rollout instead of being taken from each request separately.

Usage: python measure_acceptance.py [--events] [--corpus-dir <path>] [--manifest <path>]

`--manifest` exists so the resolver's refusals can be tested against a small
synthetic cohort. Without it a negative test can only withhold files from the
real manifest, and the run then fails on the seventeen inputs it did not supply
rather than on the one condition under test.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = Path(tempfile.mkdtemp(prefix="acceptance-"))

def option(name: str) -> str | None:
    """The value of `--name <value>`, refusing the flag with nothing after it.

    `sys.argv[index + 1]` raises IndexError when the flag is the last argument,
    which reports a missing path as a traceback rather than as the usage error
    it is.
    """
    if name not in sys.argv:
        return None
    index = sys.argv.index(name) + 1
    if index >= len(sys.argv) or sys.argv[index].startswith("--"):
        print(f"{name} needs a path", file=sys.stderr)
        raise SystemExit(2)
    return sys.argv[index]


MANIFEST_PATH = Path(option("--manifest") or (HERE / "corpus-manifest.json")).expanduser()
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def corpus_root() -> Path:
    """Where the rollouts are read from, most explicit wins."""
    explicit = option("--corpus-dir")
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("ACCEPTANCE_CORPUS_DIR")
    if env:
        return Path(env).expanduser()
    return Path(os.path.expanduser(MANIFEST["corpus_root_default"]))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_corpus(root: Path):
    """Map every manifest entry to a verified file, or report every problem.

    Collects rather than failing on the first entry, because a corpus that has
    moved usually fails for many entries at once and one name at a time turns
    that into a long guessing loop. The earlier version of this script resolved
    the before cohort with a directory glob and the after cohort by taking the
    first timestamp-prefix match, then printed `missing:` and carried on. A run
    with absent inputs produced an empty table and exit 0, which is the failure
    mode that makes a published measurement untrustworthy.
    """
    resolved, problems = {}, []
    for cohort in ("before", "after"):
        for entry in MANIFEST[cohort]:
            stem = entry["stem"]
            hits = sorted(root.rglob(f"{stem}*.jsonl"))
            if not hits:
                problems.append(f"{cohort}/{stem}: no file under {root}")
                continue
            if len(hits) > 1:
                names = ", ".join(str(h.relative_to(root)) for h in hits[:4])
                problems.append(f"{cohort}/{stem}: {len(hits)} matches ({names})")
                continue
            actual = sha256(hits[0])
            if actual != entry["sha256"]:
                problems.append(
                    f"{cohort}/{stem}: sha256 {actual[:16]} does not match the "
                    f"recorded {entry['sha256'][:16]}")
                continue
            resolved[(cohort, stem)] = hits[0]
    if problems:
        print(f"corpus resolution failed against {root}", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print(f"\n{MANIFEST['acquisition']}", file=sys.stderr)
        raise SystemExit(2)
    return resolved

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

SCOPES = {"paper": PAPER_SCOPE, "trading": TRADING_SCOPE}

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

CORPUS = resolve_corpus(corpus_root())
drift = []


def classify_cohort(cohort):
    """Classify one cohort, recording any entry whose output contradicts the manifest.

    The manifest states membership; this only checks that the reason it states
    still holds. An excluded round is excluded for producing no reviewer output,
    so a classifier change that gives one output has moved the cohort and the
    published table no longer describes this corpus.

    Both cohorts go through here. An earlier version checked only the before
    cohort, so an after round that fell silent kept `included: true`, printed a
    row of zeros, and exited 0, which is the opposite of what the README
    promises for that state.
    """
    out = []
    for entry in MANIFEST[cohort]:
        path = CORPUS[(cohort, entry["stem"])]
        rj = round_json(SCOPES[entry["scope"]],
                        OUT / f"round-{cohort}-{entry['stem'][-8:]}.json")
        rep = clf.classify(str(path), rj)
        total = rep["totals"]["tool_output_total"]
        if entry["included"] != (total > 0):
            drift.append(
                f"{cohort}/{entry['stem']}: manifest says "
                f"included={entry['included']}, classifier reports "
                f"tool_output_total={total:,}")
        if not entry["included"]:
            continue
        out.append((entry.get("label") or entry["stem"][8:24],
                    rep["totals"], rep, str(path)))
    return out


rows = classify_cohort("after")
before = classify_cohort("before")

if drift:
    print("corpus membership no longer matches the manifest", file=sys.stderr)
    for d in drift:
        print(f"  {d}", file=sys.stderr)
    raise SystemExit(3)

# The historical headings describe one specific pair of cohorts. With
# --manifest they would sit above someone else's numbers and read as the
# published record, which is the one way this script can produce a misleading
# artifact rather than merely a wrong one. Say whose cohort it is instead.
PUBLISHED = MANIFEST_PATH.resolve() == (HERE / "corpus-manifest.json").resolve()
BEFORE_HEADING = ("BEFORE (old contract, same paper, rounds 7-9)" if PUBLISHED
                  else "BEFORE (custom cohort)")
AFTER_HEADING = "AFTER (new contract)" if PUBLISHED else "AFTER (custom cohort)"

if not PUBLISHED:
    print(f"Custom cohort from {MANIFEST_PATH}: "
          f"{MANIFEST.get('record', 'no record field')}.")
    print("These totals are not the published Milestone A measurement.")
    print()

print("| round | tool output | avoidable | unresolved | coordinator_skill | rules |")
print("|---|---:|---:|---:|---:|---:|")
print(f"| **{BEFORE_HEADING}** | | | | | |")
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
print(f"| **{AFTER_HEADING}** | | | | | |")
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
for name, group in ((BEFORE_HEADING, before), (AFTER_HEADING, rows)):
    print(f"| **{name}** | | | | |")
    gr = gd = gp = 0
    for label, _, _, path in group:
        a, d, p = redelivered(path, label, show_events)
        gr += a
        gd += d
        gp += p
    print(f"| **{name.split()[0].lower()} total ({len(group)})** | {gr:,} | {gd:,} | {gp:,} | "
          f"{gp / gr * 100 if gr else 0:.1f}% |")
