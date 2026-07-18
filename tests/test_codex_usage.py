#!/usr/bin/env python3
"""Regression tests for Codex usage rendering in the user-level quota scripts.

Covers the schema change after OpenAI removed the fixed 5h window on
2026-07-12: the rollout `payload.rate_limits` now reports `primary` as the
weekly window (window_minutes 10080) with `secondary` null and a `credits`
block. Both scripts derive the window label from window_minutes and gate
credits null-safely; these tests pin that behavior against later drift.

Scope: `scripts/statusline.py` (Claude Code statusLine) and
`scripts/agent-quota.py` (standalone readout). ac-local test; check-parity
guarantees the anywhere-agents copies are byte-identical, so pinning the ac
copy pins both.
"""
import importlib.util
import json
import os
import pathlib
import tempfile
import time
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[1]


def _load(filename, modname):
    spec = importlib.util.spec_from_file_location(modname, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


statusline = _load("statusline.py", "cx_statusline")
agent_quota = _load("agent-quota.py", "cx_agent_quota")

# Both scripts define the same label helper (statusline: public name,
# agent-quota: underscore-prefixed).
LABEL_FNS = (statusline.codex_window_label, agent_quota._codex_window_label)


def _window(pct, minutes):
    return {"used_percent": float(pct), "window_minutes": minutes,
            "resets_at": time.time() + 600000}


def _render(rate_limits):
    """Run both renderers against a synthetic rollout in a throwaway home
    directory, returning (statusline_segment, agent_quota_row).

    Both scripts locate the rollout via os.path.expanduser("~"). Setting
    $HOME only redirects that on POSIX; Windows expanduser reads
    USERPROFILE. Patching os.path.expanduser is platform-independent, so
    the same test exercises the real glob/parse path on Linux, macOS, and
    the Windows CI lane alike."""
    with tempfile.TemporaryDirectory() as tmp:
        sess = pathlib.Path(tmp) / ".codex" / "sessions" / "s"
        sess.mkdir(parents=True, exist_ok=True)
        (sess / "rollout-1.jsonl").write_text(
            json.dumps({"payload": {"rate_limits": rate_limits}}) + "\n"
        )
        real = os.path.expanduser

        def fake(path):
            if path == "~":
                return tmp
            if path.startswith("~" + os.sep) or path.startswith("~/"):
                return os.path.join(tmp, path[2:])
            return real(path)

        with mock.patch("os.path.expanduser", fake):
            return statusline.codex_segment(), agent_quota.codex_row()


class TestWindowLabel(unittest.TestCase):
    def test_matrix(self):
        for fn in LABEL_FNS:
            self.assertEqual(fn({"window_minutes": 300}), "5h")
            self.assertEqual(fn({"window_minutes": 10080}), "7d")
            self.assertEqual(fn({"window_minutes": 1440}), "1d")
            self.assertEqual(fn({"window_minutes": 60}), "1h")
            self.assertEqual(fn({"window_minutes": 90}), "90m")
            self.assertEqual(fn({"window_minutes": 20160}), "14d")

    def test_missing_or_zero(self):
        for fn in LABEL_FNS:
            self.assertEqual(fn({}), "")
            self.assertEqual(fn({"window_minutes": 0}), "")
            self.assertEqual(fn({"window_minutes": None}), "")


class TestRender(unittest.TestCase):
    def test_weekly_only(self):
        # Current shape: primary is weekly, secondary null, zero credits.
        seg, row = _render({
            "primary": _window(13, 10080),
            "secondary": None,
            "credits": {"has_credits": False, "balance": "0"},
        })
        self.assertIn("7d 87%", seg)      # 100 - 13
        self.assertNotIn("5h", seg)       # not mislabeled
        self.assertNotIn("cr", seg)       # zero balance, credits off -> hidden
        self.assertIn("7d 87%", row)
        self.assertNotIn("5h", row)
        self.assertNotIn("credits", row)

    def test_dual_window_when_5h_restored(self):
        seg, row = _render({
            "primary": _window(50, 300),
            "secondary": _window(20, 10080),
            "credits": {"has_credits": False, "balance": "0"},
        })
        self.assertIn("5h 50%", seg)
        self.assertIn("7d 80%", seg)
        self.assertIn("5h 50%", row)
        self.assertIn("7d 80%", row)

    def test_credits_nonzero_shown(self):
        seg, row = _render({
            "primary": _window(0, 10080),
            "credits": {"has_credits": True, "balance": "42"},
        })
        self.assertIn("cr 42", seg)
        self.assertIn("credits 42", row)

    def test_has_credits_null_balance_is_null_safe(self):
        # The Medium finding: has_credits opens the branch, but balance may
        # be absent. Must render the tag alone, never "cr None"/"credits None".
        seg, row = _render({
            "primary": _window(0, 10080),
            "credits": {"has_credits": True, "balance": None},
        })
        self.assertNotIn("None", seg)
        self.assertNotIn("None", row)
        self.assertTrue(seg.rstrip().endswith("cr"), seg)
        self.assertIn("credits", row)

    def test_no_windows_no_credits(self):
        # rate_limits present but empty -> no broken row.
        seg, row = _render({"primary": None, "secondary": None,
                            "credits": {"has_credits": False, "balance": "0"}})
        self.assertIsNone(seg)
        self.assertIn("(no windows)", row)


if __name__ == "__main__":
    unittest.main()
