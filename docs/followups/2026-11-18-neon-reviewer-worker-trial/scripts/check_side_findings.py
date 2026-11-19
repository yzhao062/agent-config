"""Re-run the side findings of the 2026-11-18 Neon trial against ac 0878a02.

Usage: python check_side_findings.py [path-to-agent-config]

Loads health-check.py and dispatch-gemini.py as of 0878a02^ (old) and 0878a02
(shipped) through `git show`, then prints, for each input, whether a failure
marker survives code-span stripping (health-check) or whether the review
structure is found (dispatch-gemini). Prints results only; asserts nothing.
"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
MARKER = "connection refused"
TICK = "`"


def load(rev: str, rel: str, tmp: Path):
    src = subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{rel}"],
                         check=True, capture_output=True, text=True).stdout
    path = tmp / (rev.replace("^", "_parent") + "_" + Path(rel).name.replace("-", "_"))
    path.write_text(src)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    sys.path.insert(0, str(REPO / "scripts"))  # dispatch-gemini imports agent_models
    revs = ("0878a02^", "0878a02")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        hc = {r: load(r, "skills/implement-review/scripts/health-check.py", tmp) for r in revs}
        dg = {r: load(r, "skills/implement-review/scripts/dispatch-gemini.py", tmp) for r in revs}

    dbl = TICK * 2
    # 1. LaTeX quotes on one JSON tail line: the shipped scanner pairs the two
    #    opening `` runs and hides the marker between them.
    latex = ('{"text":"wrote ' + dbl + "first'' then " + MARKER
             + " while saving " + dbl + "second'' to main.tex\"}\n")
    # 2. tests/test_health_check.py "double-backtick span holding a backtick":
    #    the shipped input hides the marker on both versions; the alternative
    #    (marker before the inner backtick) tells them apart.
    shipped_dbl = f"Quoted {dbl}a {TICK} {MARKER}{dbl} here.\n"
    alt_dbl = f"Quoted {dbl}{MARKER} {TICK} a{dbl} here.\n"
    for name, text in (("latex-json-tail", latex), ("hc-shipped-input", shipped_dbl),
                       ("hc-alternative", alt_dbl)):
        row = ", ".join(f"{r}: marker {'visible' if MARKER in hc[r].strip_code_spans(text) else 'hidden'}"
                        for r in revs)
        print(f"{name:22} {row}")

    # 3. tests/test_dispatch_gemini.py nested-fence assertion (expects False).
    status, verdict = "Verification status: VERIFIED", "Commit verdict: PASS"
    whole = f"<!-- Round 6 -->\n\n## Notes\n\n{status}\n\n## New\n\nNone.\n\n{verdict}\n"
    fence, long_fence = TICK * 3, TICK * 4
    head = f"<!-- Round 6 -->\n\nStill reading.\n\n{long_fence}markdown\n"
    shipped_fence = head + f"{fence}text\nexample\n{fence}\n{whole}{long_fence}\n"
    alt_fence = head + f"{fence}markdown\n{whole}{fence}\n{long_fence}\n"
    for name, text in (("dg-shipped-input", shipped_fence), ("dg-alternative", alt_fence)):
        row = ", ".join(f"{r}: {dg[r].has_review_structure(text, 6)}" for r in revs)
        print(f"{name:22} {row}")


if __name__ == "__main__":
    main()
