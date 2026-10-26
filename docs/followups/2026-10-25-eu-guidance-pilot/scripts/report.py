"""Print the pilot tables from one or more scores.json files; round 1 and round 2 rows pool."""
import json
import sys
from collections import defaultdict
from math import comb
from statistics import mean

from tasks import LABELS

CONDS = ("none", "rules", "eu")
# The independent key marked E2 contested and five of the six round-1 units skipped it.
EXCLUDED = {"E2"}
rows = [r for path in sys.argv[1:] for r in json.loads(open(path).read())]
for r in rows:
    for k in ("over", "under", "missing", "trap_wrong"):
        if k in r:
            r[k] = [i for i in r[k] if i not in EXCLUDED]
models = sorted({r["model"] for r in rows})


def family(r):
    return LABELS[r["task"]].get("family", "round1")


def error(r):
    """A labelled error: a failed unit, a wrong decision, a failed hidden test, or a lost point or fact."""
    if r.get("failed") or r.get("parse_error") or r.get("syntax_error"):
        return True
    if "over" in r:
        return bool(r["over"] or r["under"] or r["missing"])
    if "hidden_passed" in r:
        return not r.get("hidden_ok", r["hidden_failed"] == 0 and r["hidden_passed"] > 0)
    if "mentions" in r:
        j = r.get("judge", {})
        return not j.get("drop_stated", r["mentions"]) or j.get("accuracy_errors", 0) > 0
    return r.get("errors", r.get("kw_errors", 0)) > 0 or r.get("facts_lost", 0) > 0


def fisher(a, b, c, d):
    """Two-sided Fisher exact p for the table [[a, b], [c, d]]."""
    n1, n2, k = a + b, c + d, a + c

    def p(x):
        return comb(n1, x) * comb(n2, k - x) / comb(n1 + n2, k)

    obs = p(a)
    return sum(p(x) for x in range(max(0, k - n2), min(k, n1) + 1) if p(x) <= obs * (1 + 1e-9))


def cells(select):
    out = defaultdict(list)
    for r in rows:
        if select(r):
            out[(r["condition"], r["model"])].append(r)
    return out


print("Units with a labelled error (errors/units)")
print(f"{'family':8} {'cond':6} " + " ".join(f"{m:>8}" for m in models) + "      all")
for fam in ("round1", "eu-trap", "open"):
    c = cells(lambda r: family(r) == fam)
    for cond in CONDS:
        per = [c[(cond, m)] for m in models]
        flat = [r for rs in per for r in rs]
        if flat:
            print(f"{fam:8} {cond:6} " + " ".join(f"{sum(map(error, rs)):>3}/{len(rs):<4}" for rs in per)
                  + f"  {sum(map(error, flat)):>3}/{len(flat)}")
tot = {cond: [r for r in rows if r["condition"] == cond] for cond in CONDS}
err = {cond: sum(map(error, rs)) for cond, rs in tot.items()}
for other in ("rules", "none"):
    a, b = err["eu"], len(tot["eu"]) - err["eu"]
    c_, d = err[other], len(tot[other]) - err[other]
    print(f"eu {a}/{a + b} vs {other} {c_}/{c_ + d}: Fisher p = {fisher(a, b, c_, d):.3g}")
# Repeated runs of one prompt on one model are correlated, so also count (task, model) pairs with any error.
pairs = defaultdict(lambda: defaultdict(bool))
for r in rows:
    pairs[r["condition"]][(r["task"], r["model"])] |= error(r)
for other in ("rules", "none"):
    a, n = sum(pairs["eu"].values()), len(pairs["eu"])
    c_, m = sum(pairs[other].values()), len(pairs[other])
    print(f"pairs: eu {a}/{n} vs {other} {c_}/{m}: Fisher p = {fisher(a, n - a, c_, m - c_):.3g}")

print("\nDecision tasks: over (acted on a negative item) / under (skipped a positive) / trap items wrong")
for fam in ("round1", "eu-trap"):
    c = cells(lambda r: family(r) == fam and "over" in r)
    for cond in CONDS:
        cellstr = []
        for m in models:
            rs = c[(cond, m)]
            cellstr.append(f"{sum(len(r['over']) for r in rs)}/{sum(len(r['under']) for r in rs)}"
                           f"/{sum(len(r['trap_wrong']) for r in rs)}")
        print(f"{fam:8} {cond:6} " + " ".join(f"{s:>8}" for s in cellstr))

print("\nOpen coding tasks, mean per unit: try, raise, isinstance, if, lines, tests, mocks")
c = cells(lambda r: r["task"] in ("open-config", "open-count") and "hidden_passed" in r)
for cond in CONDS:
    for m in models:
        rs = c[(cond, m)]
        if rs:
            vals = [mean(r.get(k, 0) for r in rs) for k in ("try", "raise", "isinstance", "if", "loc", "test_count", "mocks")]
            print(f"{cond:6} {m:7} n={len(rs)} " + " ".join(f"{v:5.1f}" for v in vals))

print("\nOpen summary: drop stated, accuracy errors, filler caveats, words, not three sentences")
c = cells(lambda r: "mentions" in r)
for cond in CONDS:
    for m in models:
        rs = c[(cond, m)]
        if rs:
            js = [r.get("judge", {}) for r in rs]
            print(f"{cond:6} {m:7} n={len(rs)} "
                  f"{sum(j.get('drop_stated', r['mentions']) for j, r in zip(js, rs))}/{len(rs)} "
                  f"{sum(j.get('accuracy_errors', 0) for j in js)} {sum(j.get('filler_caveats', 0) for j in js)} "
                  f"{mean(r['words'] for r in rs):.0f} {sum(r['sentences'] != 3 for r in rs)}")

bad = [r["uid"] for r in rows if r.get("failed") or r.get("parse_error")]
print("\nfailed or unparsed:", bad or "none")
