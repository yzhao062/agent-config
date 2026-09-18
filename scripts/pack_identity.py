#!/usr/bin/env python3
"""Read-only pack identity for the session banner (Session check item 7).

The renderer (``render_banner.py``) asks two questions of a consumer
repository: how many user-level packs are not deployed in this project, and
how many deployed packs have a newer upstream head recorded in the lock. This
module answers both from files on disk. It performs no network resolution and
no healing; ``anywhere-agents pack verify --fix`` owns those. It is vendored
beside the renderer in both delivery paths (the bootstrap sparse clone and
the wheel) and imports nothing from either, so the banner calculation is one
function wherever it runs.

Inputs and the rules they follow:

- ``user_packs``: the user-level ``config.yaml`` (``%APPDATA%\\anywhere-agents``
  on Windows, ``$XDG_CONFIG_HOME/anywhere-agents`` or
  ``~/.config/anywhere-agents`` elsewhere). An absent file is an empty list.
  A row that names a bundled default (``agent-style``, ``aa-core-skills``)
  without a ``source`` is ``(name, "bundled:aa", "bundled")``.
  ``AGENT_CONFIG_PACKS`` is never read.
- ``project_packs``: seeded with the bundled defaults for the host
  (``AGENT_CONFIG_HOST``; ``claude-code`` unless ``codex``), then
  ``agent-config.yaml`` and ``agent-config.local.yaml`` in that order. Each
  layer replaces earlier entries of the same name; an explicit empty or null
  ``packs:`` clears everything accumulated so far, and a later layer can add
  entries again. A seeded default, or a project row naming a bundled default
  without a ``source``, takes the identity the lock records for it
  (``source_url``, ``requested_ref``); when the lock has no entry, the sparse
  clone's ``bootstrap/packs.yaml`` supplies ``source.repo`` and
  ``source.ref``. A lock entry whose ``source_url`` is ``bundled:aa`` and a
  manifest entry without a ``source`` are ``(name, "bundled:aa", "bundled")``.
- ``gap_count``: user rows with no project row of the same name, or whose
  normalized ``(name, url, ref)`` differs from the project row's.
- ``update_count``: lock entries whose ``latest_known_head`` and
  ``resolved_commit`` are both non-empty and differ.

Absence and unavailability are kept apart. An absent user config is an empty
user list; absent project layers leave the seeds in place; a missing lock
means no update count and no lock identity. Missing identity evidence for a
seeded default, malformed YAML or JSON, and a PyYAML that cannot be imported
all report ``unavailable`` (a ``None`` count with a reason) rather than a
zero, because a zero would read as a clean check.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Optional

BUNDLED_URL = "bundled:aa"
BUNDLED_REF = "bundled"
DEFAULT_SELECTIONS = ("agent-style", "aa-core-skills")
CLAUDE_ONLY_DEFAULTS = frozenset({"aa-core-skills"})
KNOWN_HOSTS = ("claude-code", "codex")

_GITHUB_HTTPS_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)
_GITHUB_SSH_SCP_RE = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$"
)
_GITHUB_SSH_URL_RE = re.compile(
    r"^ssh://git@github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


class Unavailable(Exception):
    """A check cannot be computed; ``str(exc)`` names why."""


def normalize_pack_source_url(url: str) -> str:
    """Canonical form of ``url`` for identity comparison.

    Mirrors ``scripts/packs/source_fetch.py`` in anywhere-agents: a
    github.com URL collapses to ``https://github.com/<owner>/<repo>`` with a
    lowercased owner and repo, no trailing ``.git`` and no trailing slash;
    another host keeps its path case and loses only a trailing slash and
    ``.git``; anything unparseable is returned unchanged.
    """
    if not isinstance(url, str) or not url:
        return url
    candidate = re.sub(r"github\.com", "github.com", url, flags=re.IGNORECASE)
    if "github.com" in candidate:
        for pattern in (_GITHUB_HTTPS_RE, _GITHUB_SSH_SCP_RE, _GITHUB_SSH_URL_RE):
            match = pattern.match(candidate)
            if match:
                return "https://github.com/%s/%s" % (
                    match.group("owner").lower(),
                    match.group("repo").lower(),
                )
    from urllib.parse import urlsplit, urlunsplit

    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    if not parts.scheme or not parts.netloc:
        return url
    path = parts.path
    if path.endswith("/"):
        path = path[:-1]
    if path.endswith(".git"):
        path = path[:-4]
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, parts.fragment))


def user_config_path(environ: Optional[dict] = None, platform: Optional[str] = None) -> Optional[str]:
    """The user-level config path, or ``None`` when no home resolves."""
    env = os.environ if environ is None else environ
    plat = sys.platform if platform is None else platform
    if plat == "win32":
        appdata = env.get("APPDATA")
        if not appdata:
            return None
        return os.path.join(appdata, "anywhere-agents", "config.yaml")
    xdg = env.get("XDG_CONFIG_HOME")
    if xdg:
        return os.path.join(xdg, "anywhere-agents", "config.yaml")
    home = env.get("HOME")
    if home:
        return os.path.join(home, ".config", "anywhere-agents", "config.yaml")
    return None


def active_host(environ: Optional[dict] = None) -> str:
    env = os.environ if environ is None else environ
    value = env.get("AGENT_CONFIG_HOST", "").strip()
    return value if value in KNOWN_HOSTS else "claude-code"


def default_seed(host: str) -> tuple:
    if host == "claude-code":
        return DEFAULT_SELECTIONS
    return tuple(name for name in DEFAULT_SELECTIONS if name not in CLAUDE_ONLY_DEFAULTS)


def read_yaml(path: str) -> Optional[dict]:
    """``None`` when absent, ``{}`` when empty, the mapping otherwise.

    Raises ``Unavailable`` when PyYAML is missing, the text is not YAML, or
    the top level is not a mapping.
    """
    if not os.path.exists(path):
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        raise Unavailable("PyYAML is not installed")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise Unavailable("%s is unreadable: %s" % (path, exc))
    if not text.strip():
        return {}
    try:
        data = yaml.safe_load(text)
    except Exception as exc:  # yaml.YAMLError and friends
        raise Unavailable("%s is not valid YAML: %s" % (path, exc))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise Unavailable("%s: top level must be a mapping" % path)
    return data


def _packs_signal(data: Optional[dict], path: str):
    """The pack list of one config layer: ``None`` for no signal, ``[]`` for
    an explicit clear, the raw list otherwise."""
    if data is None:
        return None
    key = None
    if "packs" in data:
        key = "packs"
    elif "rule_packs" in data:
        key = "rule_packs"
    if key is None:
        return None
    raw = data[key]
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise Unavailable("%s: %r must be a list" % (path, key))
    return raw


def _normalize_row(entry: Any, path: str) -> dict:
    """A config row as a mapping with a non-empty string ``name``.

    A bare string is a name. Anything else that is not a mapping with a
    name, or whose ``source`` is neither absent, a mapping, nor a string,
    is unavailable rather than skipped: a selection that cannot be read is
    not an empty selection, and skipping the row would report the project
    as clean.
    """
    if isinstance(entry, str) and entry:
        return {"name": entry}
    if not isinstance(entry, dict):
        raise Unavailable("%s: pack entry %r is neither a name nor a mapping" % (path, entry))
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        raise Unavailable("%s: pack entry without a name: %r" % (path, entry))
    source = entry.get("source")
    if source is not None and not isinstance(source, (dict, str)):
        raise Unavailable("%s: pack %r has a source that is neither a mapping nor a string" % (path, name))
    if isinstance(source, dict):
        for key in ("url", "repo", "ref"):
            value = source.get(key)
            if value is not None and not isinstance(value, str):
                raise Unavailable("%s: pack %r source.%s is not a string" % (path, name, key))
    ref = entry.get("ref")
    if ref is not None and not isinstance(ref, str):
        raise Unavailable("%s: pack %r ref is not a string" % (path, name))
    return entry


def _entry_source(entry: dict) -> tuple:
    """``(url, ref)`` from a config row, ``("", "")`` when it has no source."""
    source = entry.get("source")
    if isinstance(source, dict):
        url = source.get("url") or source.get("repo") or ""
        ref = source.get("ref") or entry.get("ref") or ("main" if url else "")
        return str(url), str(ref)
    if isinstance(source, str) and source:
        return source, str(entry.get("ref") or "main")
    return "", str(entry.get("ref") or "")


def _identity(name: str, url: str, ref: str) -> tuple:
    return (name, normalize_pack_source_url(url), ref)


def user_packs(path: Optional[str]) -> list:
    """Identity tuples from the user-level config; empty when absent."""
    if path is None:
        return []
    data = read_yaml(path)
    raw = _packs_signal(data, path)
    if not raw:
        return []
    seen = set()
    out = []
    for raw_entry in raw:
        entry = _normalize_row(raw_entry, path)
        name = entry["name"]
        if name in seen:
            continue  # pack add once wrote duplicates; the first row wins
        seen.add(name)
        url, ref = _entry_source(entry)
        if not url and name in DEFAULT_SELECTIONS:
            out.append((name, BUNDLED_URL, BUNDLED_REF))
        else:
            out.append(_identity(name, url, ref))
    return out


def read_lock(project_root: str) -> Optional[dict]:
    """The ``packs`` mapping of ``.agent-config/pack-lock.json``, ``None``
    when the lock is absent. Both the flat shape and ``data.packs`` are read."""
    path = os.path.join(project_root, ".agent-config", "pack-lock.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise Unavailable("%s is malformed: %s" % (path, exc))
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    if not isinstance(data, dict):
        raise Unavailable("%s: top level must be an object" % path)
    packs = data.get("packs")
    if packs is None:
        return {}
    if not isinstance(packs, dict):
        raise Unavailable("%s: packs must be an object" % path)
    for name, body in packs.items():
        if not isinstance(body, dict):
            raise Unavailable("%s: lock entry %r is not an object" % (path, name))
        for key in ("source_url", "requested_ref", "resolved_commit", "latest_known_head"):
            value = body.get(key)
            if value is not None and not isinstance(value, str):
                raise Unavailable("%s: lock entry %r field %s is not a string" % (path, name, key))
    return packs


def _manifest_identity(project_root: str, name: str) -> Optional[tuple]:
    """Identity of a bundled default from the sparse clone's manifest, or
    ``None`` when the manifest or the entry is absent."""
    path = os.path.join(project_root, ".agent-config", "repo", "bootstrap", "packs.yaml")
    data = read_yaml(path)
    if not data:
        return None
    packs = data.get("packs")
    if not isinstance(packs, list):
        return None
    for pack in packs:
        if not isinstance(pack, dict) or pack.get("name") != name:
            continue
        source = pack.get("source")
        if isinstance(source, dict):
            url = source.get("repo") or source.get("url") or ""
            ref = source.get("ref") or pack.get("default-ref") or ""
            if url:
                return _identity(name, str(url), str(ref))
        if isinstance(source, str) and source:
            return _identity(name, source, str(pack.get("default-ref") or ""))
        return (name, BUNDLED_URL, BUNDLED_REF)
    return None


def _default_identity(project_root: str, name: str, lock: Optional[dict]) -> tuple:
    """Identity of a seeded default or a sourceless project row naming one."""
    body = lock.get(name) if isinstance(lock, dict) else None
    if isinstance(body, dict):
        url = body.get("source_url") or ""
        ref = body.get("requested_ref") or ""
        if url == BUNDLED_URL:
            return (name, BUNDLED_URL, BUNDLED_REF)
        if url or ref:
            return _identity(name, str(url), str(ref))
    ident = _manifest_identity(project_root, name)
    if ident is None:
        raise Unavailable("no identity recorded for bundled default %r" % name)
    return ident


def project_packs(project_root: str, environ: Optional[dict] = None, lock: Optional[dict] = None) -> list:
    """Identity tuples for the project after seeding and both config layers."""
    merged = {}
    for name in default_seed(active_host(environ)):
        merged[name] = {"name": name}
    for filename in ("agent-config.yaml", "agent-config.local.yaml"):
        path = os.path.join(project_root, filename)
        raw = _packs_signal(read_yaml(path), path)
        if raw is None:
            continue
        if raw == []:
            merged.clear()
            continue
        for raw_entry in raw:
            entry = _normalize_row(raw_entry, path)
            merged[entry["name"]] = entry
    out = []
    for name, entry in merged.items():
        url, ref = _entry_source(entry)
        if not url and name in DEFAULT_SELECTIONS:
            out.append(_default_identity(project_root, name, lock))
        else:
            out.append(_identity(name, url, ref))
    return out


def gap_count(user: list, project: list) -> int:
    by_name = {}
    for ident in project:
        by_name.setdefault(ident[0], ident)
    gaps = 0
    for ident in user:
        match = by_name.get(ident[0])
        if match is None or match != ident:
            gaps += 1
    return gaps


def update_count(lock: dict) -> int:
    """Lock entries whose recorded upstream head differs from the resolved
    commit. The caller decides what an absent lock means; an existing empty
    lock is a valid zero."""
    updates = 0
    for body in lock.values():
        if not isinstance(body, dict):
            continue
        head = body.get("latest_known_head")
        resolved = body.get("resolved_commit")
        if head and resolved and head != resolved:
            updates += 1
    return updates


def pack_checks(project_root: str, environ: Optional[dict] = None, platform: Optional[str] = None) -> dict:
    """Both counts for the banner, or the reason they are unavailable.

    Returns ``{"gap_count": int | None, "update_count": int | None,
    "unavailable": str | None}``. The two counts are computed independently
    so a malformed user config does not hide an available update; each
    ``None`` carries its reason in ``unavailable``.
    """
    result: dict[str, Any] = {"gap_count": None, "update_count": None, "unavailable": None}
    reasons = []
    lock = None
    lock_ok = True
    try:
        lock = read_lock(project_root)
    except Unavailable as exc:
        lock_ok = False
        reasons.append(str(exc))
    if lock_ok and lock is None:
        # The manifest can still supply the seeded defaults' identity for the
        # gap count, but nothing else records upstream heads.
        reasons.append("no update evidence (.agent-config/pack-lock.json is absent)")
    elif lock_ok:
        result["update_count"] = update_count(lock)
    try:
        user = user_packs(user_config_path(environ, platform))
        project = project_packs(project_root, environ, lock if lock_ok else None)
        result["gap_count"] = gap_count(user, project)
    except Unavailable as exc:
        reasons.append(str(exc))
    if reasons:
        result["unavailable"] = "; ".join(reasons)
    return result


def main(argv: Optional[list] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = args[0] if args else os.getcwd()
    print(json.dumps(pack_checks(os.path.abspath(root)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
