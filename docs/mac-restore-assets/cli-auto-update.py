#!/usr/bin/env python3
"""Update the user-installed development CLIs without an interactive shell."""

import fcntl
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile


HOME = Path.home()
BASE = HOME / ".local/share/cli-auto-update"
BIN = HOME / ".local/bin"
ENV = os.environ.copy()
ENV["PATH"] = os.pathsep.join(
    (str(BIN), str(HOME / "miniforge3/bin"), "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin")
)
ENV["CI"] = "1"


def run(name, argv, timeout=900, cwd=None, env=None):
    logging.info("Updating %s", name)
    try:
        result = subprocess.run(
            argv, env=env or ENV, cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logging.error("%s: %s", name, exc)
        return False
    for line in result.stdout.splitlines():
        logging.info("%s: %s", name, line)
    if result.returncode:
        logging.error("%s failed with exit %s", name, result.returncode)
        return False
    logging.info("%s completed", name)
    return True


def output(argv, timeout=30):
    return subprocess.check_output(argv, env=ENV, text=True, timeout=timeout).strip()


def version_tuple(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("unexpected version: " + value)
    return tuple(int(part) for part in match.groups())


def update_codex():
    with tempfile.TemporaryDirectory(prefix="codex-update-", dir=str(BASE)) as temp:
        installer = Path(temp) / "install.sh"
        if not run(
            "Codex installer download",
            ["/usr/bin/curl", "-fsSL", "https://chatgpt.com/codex/install.sh", "-o", str(installer)],
            timeout=60,
        ):
            return False
        env = dict(ENV, CODEX_NON_INTERACTIVE="1")
        return run("Codex installer", ["/bin/sh", str(installer)], env=env)


def update_gh():
    try:
        installed = re.search(r"\b\d+\.\d+\.\d+\b", output([str(BIN / "gh"), "--version"]).splitlines()[0]).group()
        tag = output([str(BIN / "gh"), "api", "repos/cli/cli/releases/latest", "--jq", ".tag_name"])
        if version_tuple(tag) <= version_tuple(installed):
            logging.info("gh is current: %s", installed)
            return True
        version = tag.removeprefix("v") if hasattr(str, "removeprefix") else tag.lstrip("v")
        archive = "gh_{}_macOS_arm64.zip".format(version)
        checksums = "gh_{}_checksums.txt".format(version)
        with tempfile.TemporaryDirectory(prefix="gh-update-", dir=str(BASE)) as temp:
            subprocess.run(
                [str(BIN / "gh"), "release", "download", tag, "-R", "cli/cli", "-p", archive,
                 "-p", checksums, "-D", temp], env=ENV, timeout=300, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            archive_path = Path(temp) / archive
            lines = (Path(temp) / checksums).read_text().splitlines()
            expected = None
            for line in lines:
                parts = line.split()
                if len(parts) == 2 and parts[1].lstrip("*") == archive:
                    expected = parts[0]
                    break
            if not expected or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
                raise ValueError("gh release checksum missing")
            actual = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            if actual.lower() != expected.lower():
                raise ValueError("gh release checksum mismatch")
            member = "gh_{}_macOS_arm64/bin/gh".format(version)
            with zipfile.ZipFile(archive_path) as package:
                executable = package.read(member)
            staged = BIN / (".gh-update-{}".format(os.getpid()))
            try:
                staged.write_bytes(executable)
                staged.chmod(0o755)
                os.replace(staged, BIN / "gh")
            finally:
                staged.unlink(missing_ok=True)
        actual_version = output([str(BIN / "gh"), "--version"]).splitlines()[0]
        logging.info("gh updated: %s", actual_version)
        return version in actual_version
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        logging.error("gh update failed: %s", exc)
        return False


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(BASE / "update.log", maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    with (BASE / "update.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logging.info("Another update run is active")
            return 0
        checks = [
            update_codex(),
            run("Claude Code", [str(BIN / "claude"), "update"]),
            run("Agy", [str(BIN / "agy"), "update"]),
            run("AWS CLI", [str(BIN / "aws"), "update"]),
            run("Google Cloud CLI", [str(BIN / "gcloud"), "components", "update", "--quiet"]),
            run("anywhere-agents", [str(HOME / "miniforge3/bin/pipx"), "upgrade", "anywhere-agents"]),
            run("VibeSignal", [str(HOME / "miniforge3/bin/pipx"), "upgrade", "vibesignal"]),
            run("Twine", [str(HOME / "miniforge3/bin/pipx"), "upgrade", "twine"]),
            run("Azure CLI", [str(HOME / "miniforge3/bin/pipx"), "upgrade", "azure-cli"]),
            update_gh(),
        ]
        ok = all(checks)
        logging.info("Update run %s", "completed" if ok else "failed")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
