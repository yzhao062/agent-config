"""Round 2: plant one defect in each seeded clone (d1 to d4) and stage it.

Usage: python seed.py <workdir>

Each replacement must match exactly once. The c1 and c2 clones stay as committed.
"""
import subprocess
import sys
from pathlib import Path

WORK = Path(sys.argv[1])
AC = "/Users/yzhao062/PycharmProjects/agent-config"


def show(rev: str, path: str) -> str:
    return subprocess.run(["git", "-C", AC, "show", f"{rev}:{path}"],
                          check=True, capture_output=True, text=True).stdout


def method(text: str, name: str) -> str:
    start = text.index(f"    def {name}(")
    end = text.index("\n    def ", start + 1)
    return text[start:end]


def plant(clone: str, path: str, old: str, new: str) -> None:
    target = WORK / clone / path
    text = target.read_text()
    assert text.count(old) == 1, (clone, path, text.count(old))
    target.write_text(text.replace(old, new))
    subprocess.run(["git", "-C", str(WORK / clone), "add", path], check=True)


for arm in ("carbon", "neon"):
    # D1, logic: worker and prun-worker rows count toward the "two or more reviewer rows" panel test.
    plant(f"d1-{arm}", "scripts/agent_models.py",
          'if role == "reviewer" and family != "*"',
          'if role in ("reviewer", "worker", "prun-worker") and family != "*"')

    # D2, one copy of two: the prun dispatcher keeps the old tier list, and its xhigh test input goes too.
    plant(f"d2-{arm}", "skills/prun/scripts/dispatch-task-agy.py",
          '("low", "medium", "high", "xhigh", "max")', '("low", "medium", "high", "max")')
    test = "tests/test_dispatch_task_agy.py"
    name = "test_effort_follows_a_resolved_tier_other_than_high"
    plant(f"d2-{arm}", test, method((WORK / f"d2-{arm}" / test).read_text(), name),
          method(show("37b9b26^", test), name))

    # D3, document against code: the dispatcher waives a missing registry row only when both overrides are set.
    plant(f"d3-{arm}", "skills/prun/references/grok-executor.md",
          "unless both `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` are set, which waives it",
          "unless `GROK_DISPATCH_MODEL` is set, which waives it")

    # D4, a test that does not test its claim: the zero-usage case no longer uses zero.
    usage = "tests/test_codex_usage.py"
    plant(f"d4-{arm}", usage,
          'rate_limits = {"five_hour": {"used_percentage": 0},\n                       "seven_day": {"used_percentage": 0}}',
          'rate_limits = {"five_hour": {"used_percentage": 1},\n                       "seven_day": {"used_percentage": 1}}')
    plant(f"d4-{arm}", usage, 'self.assertEqual(compact, "cc 5h100% 7d100%")',
          'self.assertEqual(compact, "cc 5h99% 7d99%")')
    plant(f"d4-{arm}", usage, 'self.assertEqual(full, "\U0001f916 Opus 5.5 · 5h 100% · 7d 100%")',
          'self.assertEqual(full, "\U0001f916 Opus 5.5 · 5h 99% · 7d 99%")')
    plant(f"d4-{arm}", usage,
          'self.assertIn("5h 100% left", row)\n        self.assertIn("7d 100% left", row)',
          'self.assertIn("5h 99% left", row)\n        self.assertIn("7d 99% left", row)')

print("seeded")
