import json
import pathlib
import subprocess
import sys

HOOK = pathlib.Path(__file__).with_name("hook.py")


def run(stdin):
    p = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=20)
    return p.returncode, p.stdout.strip()


def decision(out):
    return json.loads(out.splitlines()[-1])["decision"]


def test_deny():
    rc, out = run(json.dumps({"tool": "Bash", "command": "sudo rm -rf / --no-preserve-root"}))
    assert rc == 0 and decision(out) == "deny"


def test_allow():
    rc, out = run(json.dumps({"tool": "Bash", "command": "ls -la"}))
    assert rc == 0 and decision(out) == "allow"


def test_empty_payload_allows():
    rc, out = run("")
    assert rc == 0 and decision(out) == "allow"


def test_truncated_payload_allows():
    rc, out = run('{"tool": "Bash", "comm')
    assert rc == 0 and decision(out) == "allow"
