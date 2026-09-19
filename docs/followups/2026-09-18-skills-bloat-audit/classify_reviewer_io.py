#!/usr/bin/env python3
"""Classify what a dispatched reviewer read during one review round.

Input is one Codex rollout (JSONL, the file under ~/.codex/sessions that a
dispatched `codex exec` wrote) or one Antigravity `tail` (the JSON event stream
dispatch-gemini.py captured), plus a small round.json that says what the
reviewer was given. Output is one row per tool event with a class, a label, and
the bytes the model received, then totals by class and by label.

Byte convention. Tool output is the decoded output the model received, counted
once per event, without JSON serialization wrappers: for Codex the UTF-8 length
of `aggregated_output`; for Antigravity the payload size M from the `N lines,
M bytes` summary a `view_file` call reports, or the UTF-8 length of `output`
for other tools; an event with no usable output counts 0 and is marked so.
Prompt and injected bytes are reported separately and never added to the
tool-output totals. A Codex shell event is the script the wrapper ran (the
payload after `-Command` or `-lc`), never the wrapper's own argv; operands a
command executes (`python x.py`) are not reads. A shell event that reads
several files is one event with one output, so it is classed by its most
consequential read (coordinator skill, then rules, then review sink, then
source); when such an event mixes an in-scope read with a read that would be
avoidable on its own, it is unresolved, because the bytes cannot be split.

Labels, in this order:
  1. diff: with command transport the first obtain is required and later ones
     avoidable; with embedded transport every obtain is avoidable;
  2. an exact repeat (the same file, the same range, or the same command) is
     avoidable whatever the scope says; a full read after targeted reads of
     the same file is unresolved;
  3. a first read of a path inside review_scope is required (this includes
     the coordinator skill and rule files when they are under review);
  4. an event with an entry in verification_reasons is required;
  5. rules: the first read of an instruction file NOT in
     supplied_instruction_files is required; a read of a supplied one is
     avoidable;
  6. coordinator_skill outside the scope with no reason: a full-file read or
     an example-reviews read is avoidable, a targeted range read is
     unresolved;
  7. source, review_sink, tests_builds, other: a first read or run is
     required.
Unresolved events are listed separately for adjudication by hand; the totals
never fold them into required or avoidable.

round.json fields: backend ("codex" | "antigravity"; detected from the input
when absent), supplied_instruction_files (repo-relative paths whose contents
were injected or pasted), review_scope (paths or prefixes under review),
diff_transport ("command" | "embedded"), coordinator_skill_roots,
rule_files, verification_reasons ({event_id: reason}).

Usage:
  python classify_reviewer_io.py --input <rollout.jsonl|tail> --round <round.json>
                                 [--json <out.json>] [--prompt-relay <path>]
Exit 0 on success, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_COORDINATOR_ROOTS = [
    "skills/implement-review",
    ".claude/skills/implement-review",
    ".agent-config/repo/skills/implement-review",
]
DEFAULT_RULE_FILES = ["AGENTS.md", "AGENTS.local.md", "CLAUDE.md", "CLAUDE.local.md",
                      "agents/codex.md", "agents/codex.local.md"]
RULE_BASENAMES = {"agents.md", "agents.local.md", "claude.md", "claude.local.md",
                  "codex.md", "codex.local.md"}

_VIEW_FILE_RE = re.compile(r"^(\d+)\s+lines?,\s+(\d+)\s+bytes?$")
_GIT_DIFF_RE = re.compile(r"\bgit\b[^|;&]*\bdiff\b")
_READ_CMD_RE = re.compile(
    r"\b(Get-Content|gc|cat|sed|head|tail|type|more|less|bat|nl)\b", re.IGNORECASE
)
_TEST_BUILD_RE = re.compile(
    r"\b(pytest|unittest|npm\s+(run\s+)?test|cargo\s+(test|build)|make|latexmk|pdflatex|"
    r"bibtex|biber|python(3)?(\.exe)?\s+(-m\s+\w+|[^\s]+\.py)|pwsh(\.exe)?\s+[^\s]+\.ps1|"
    r"bash\s+[^\s]+\.sh|pip\s+install|mamba|conda|check-parity)\b",
    re.IGNORECASE,
)
# A path-looking token: absolute, dot-relative, or bare with a slash or a known
# extension. Quoted forms first so a space inside quotes survives.
_QUOTED_PATH_RE = re.compile(r"""["']([^"'\n]+?)["']""")
_BARE_PATH_RE = re.compile(
    r"""(?:(?<=\s)|^)((?:[A-Za-z]:[\\/]|\.{1,2}[\\/]|[\\/])[^\s"'|;&<>]+"""
    r"""|[\w.-]+(?:[\\/][\w.-]+)+"""
    r"""|[\w.-]+\.(?:md|txt|py|sh|ps1|tex|json|jsonl|yaml|yml|bib|rst|csv|toml|cfg|ini))"""
)
_EXT_RE = re.compile(r"\.(md|txt|py|sh|ps1|tex|json|jsonl|yaml|yml|bib|rst|csv|toml|cfg|ini|html|js|ts)$", re.IGNORECASE)


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip().lower()


def _under(path: str, prefixes: List[str]) -> bool:
    """True when the normalized path is, or lies below, any prefix.

    Absolute paths are matched at a directory boundary anywhere in the path,
    so `C:/repo/skills/implement-review/SKILL.md` lies under
    `skills/implement-review` without knowing where the repository is.
    """
    p = _norm(path)
    for raw in prefixes:
        pre = _norm(raw).rstrip("/")
        if not pre:
            continue
        if p == pre or p.startswith(pre + "/") or ("/" + pre + "/") in ("/" + p):
            return True
        if p.endswith("/" + pre):
            return True
    return False


def _is_rule_file(path: str, rule_files: List[str]) -> bool:
    p = _norm(path)
    base = os.path.basename(p)
    if base in RULE_BASENAMES:
        return True
    if "/.claude/commands/" in ("/" + p) and base.endswith(".md"):
        return True
    for raw in rule_files:
        rf = _norm(raw)
        if p == rf or p.endswith("/" + rf):
            return True
    return False


def _is_review_sink(path: str) -> bool:
    base = os.path.basename(_norm(path))
    return base.startswith("review-") and base.endswith(".md")


_HERESTRING_RE = re.compile(r"@(['\"])\r?\n(.*?)\r?\n\1@", re.DOTALL)
_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)(\w+)\1(?P<rest>[^\n]*)\r?\n(?P<body>.*?)\r?\n\2(?=\r?\n|$)", re.DOTALL)
# What follows a here-string decides whether its body runs: a pipe into an
# interpreter reading stdin executes it; Set-Content, Out-File, or a file
# redirection stores it as data.
_EXECUTED_HERESTRING_TAIL_RE = re.compile(
    r"^\s*\|\s*&?\s*['\"]?[\w./\\:-]*(python(3)?(\.exe)?|pwsh(\.exe)?|powershell(\.exe)?|bash|sh|node)['\"]?"
    r"(\s+-\w*)*\s*(-|-c\b|-Command\b|$)",
    re.IGNORECASE,
)
_EXECUTED_HEREDOC_HEAD_RE = re.compile(
    r"(python(3)?(\.exe)?|pwsh(\.exe)?|powershell(\.exe)?|bash|sh|node)['\"]?\s+(-\s+|-c\s+-\s+|-Command\s+-\s+)?<<",
    re.IGNORECASE,
)


# The storage-only grammar: after the bodies are masked, every statement of
# the event must be one of these, or the bodies are kept as executable. Only
# a literal body (single-quoted here-string, quoted heredoc delimiter) can be
# inert; an expandable body is masked with a different marker that this
# grammar does not accept, because `$(...)` inside it runs during expansion
# whatever happens to the result.
_STORAGE_STATEMENT_RE = re.compile(
    r"^\s*(?:\$\w+\s*=\s*@'<script>'@"
    r"|@'<script>'@\s*(?:\|\s*(?:Set-Content|Out-File|Add-Content)\b[^;|\n]*|>>?\s*[^\s;|&]+))\s*$"
    r"|^\s*(?:cat|tee)?\s*<<'<script>'\s*(?:>>?\s*[^\s;|&]+|\|\s*tee\b[^;|\n]*)\s*$",
    re.IGNORECASE,
)


def _storage_only(masked: str) -> bool:
    """True only when every statement of the masked event stores a literal body.

    Positive recognition, deliberately small: a single-quoted here-string
    assigned to a variable, or piped into Set-Content, Out-File, or
    Add-Content, or redirected into a file; a quoted heredoc redirected into a
    file or piped into tee; and nothing else in the event. Any other statement
    (a script run afterwards, `Invoke-Expression`, an unknown pipeline
    consumer, a bare here-string, a bare `cat <<'EOF'`) fails the test and the
    bodies are kept.
    """
    statements = [st for st in re.split(r"[;\n]+", masked) if st.strip()]
    if not statements:
        return False
    return all(_STORAGE_STATEMENT_RE.match(st) for st in statements)


_INLINE_CODE_RE = re.compile(
    r"(?:^|[\s;|&(])['\"]?[\w./\\:-]*"
    r"(?:python(?:3)?(?:\.exe)?|pwsh(?:\.exe)?|powershell(?:\.exe)?|bash|sh|node)['\"]?"
    r"(?:\s+-\w+)*\s+(?:-c|-Command)\s+(?P<code>.+)",
    re.IGNORECASE | re.DOTALL,
)


def _inline_code(command: str) -> List[str]:
    """Source passed to an interpreter with -c or -Command, as a body.

    `python -c "print(open('AGENTS.md').read())"` reads a file just as a
    here-string piped into `python -` does, and the quoted-path matcher
    cannot see the inner path through the outer quotes. The whole argument
    after the flag is taken as one body; the sensitive-read rule then decides,
    and inline code that names nothing sensitive stays an ordinary build step.
    """
    out: List[str] = []
    for m in _INLINE_CODE_RE.finditer(command):
        code = m.group("code").strip()
        # The argument usually arrives wrapped in one quote pair; without
        # stripping it the inner quoted paths are invisible to the matcher.
        if len(code) >= 2 and code[0] == code[-1] and code[0] in "'\"":
            code = code[1:-1]
        if code:
            out.append(code)
    return out


def _split_embedded_scripts(command: str) -> Tuple[str, List[str]]:
    """The command with inert script bodies removed, plus every body that may run.

    A body is inert only when it is literal (a single-quoted here-string or a
    quoted heredoc delimiter) and the whole event is recognized as
    storage-only (`_storage_only`); then the words `git diff` or a path inside
    it are data on their way to disk and are dropped before matching. An
    expandable body (`@"..."@`, or a heredoc with a bare delimiter, since
    both bash quote styles suppress expansion) is always kept, because
    `$(...)` inside it runs during expansion even when the result is stored.
    Every other event keeps its bodies aside, so the classifier can refuse to
    label the event automatically when a body names a sensitive read.
    Source passed inline with `-c` or `-Command` is a body as well.
    Conservative by design: no shell is interpreted, and an unknown use counts
    as executable.
    """
    bodies: List[str] = []
    expandable = False

    def here(m: "re.Match[str]") -> str:
        nonlocal expandable
        bodies.append(m.group(2))
        if m.group(1) == '"':
            expandable = True
            return '@"<script>"@'
        return "@'<script>'@"

    text = _HERESTRING_RE.sub(here, command)

    def heredoc(m: "re.Match[str]") -> str:
        nonlocal expandable
        bodies.append(m.group("body"))
        rest = m.group("rest")
        if m.group(1) == "":
            expandable = True
            return "<<<script>" + rest
        return "<<'<script>'" + rest

    text = _HEREDOC_RE.sub(heredoc, text)
    inline = _inline_code(text)
    if not bodies:
        return text, inline
    if not expandable and _storage_only(text) and not inline:
        return text, []
    return text, bodies + inline


def _strip_embedded_scripts(command: str) -> str:
    return _split_embedded_scripts(command)[0]


def _paths_in_command(command: str) -> List[str]:
    """Every path-looking token of a shell command, quoted forms first."""
    found: List[str] = []
    for m in _QUOTED_PATH_RE.finditer(command):
        token = m.group(1)
        if ("/" in token or "\\" in token or _EXT_RE.search(token)) and " " not in token.strip():
            found.append(token)
    for m in _BARE_PATH_RE.finditer(command):
        token = m.group(1).rstrip(".,;:)")
        if token and token not in found and not token.lower().startswith(("http:", "https:")):
            found.append(token)
    return found


def _range_in_command(command: str) -> Optional[Tuple[int, int]]:
    """A line range when the command reads part of a file, else None."""
    m = re.search(r"sed\s+-n\s+['\"]?(\d+),(\d+)p", command)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"sed\s+-n\s+['\"]?(\d+)p", command)
    if m:
        return int(m.group(1)), int(m.group(1))
    m = re.search(r"Select-Object\s+-Skip\s+(\d+)\s+-First\s+(\d+)", command, re.IGNORECASE)
    if m:
        skip, first = int(m.group(1)), int(m.group(2))
        return skip + 1, skip + first
    m = re.search(r"Select-Object\s+-First\s+(\d+)", command, re.IGNORECASE)
    if m:
        return 1, int(m.group(1))
    m = re.search(r"-TotalCount\s+(\d+)", command, re.IGNORECASE)
    if m:
        return 1, int(m.group(1))
    m = re.search(r"\bhead\s+(?:-n\s*|-)(\d+)", command)
    if m:
        return 1, int(m.group(1))
    m = re.search(r"\btail\s+(?:-n\s*|-)(\d+)", command)
    if m:
        return -int(m.group(1)), -1
    m = re.search(r"\$\w+\s+-ge\s+(\d+)\s+-and\s+\$\w+\s+-le\s+(\d+)", command)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


_SEARCH_RE = re.compile(
    r"(?:^|[\s;|&(])(?:rg|grep|egrep|Select-String|findstr)\b", re.IGNORECASE
)


def _search_identity(command: str) -> Optional[str]:
    """The identity of a search command, or None when the command is not one.

    A search over a file returns matching lines, so the pattern and every
    output-affecting option (context, case, multiline) decide what the
    reviewer saw, and whitespace inside a quoted pattern is part of it. The
    literal command is the identity: an identical command is a repeat,
    anything else is a different read; a repeat that differs only by shell
    spacing is missed on purpose rather than merging two different reads.
    """
    if not _SEARCH_RE.search(command):
        return None
    return command


class Event:
    def __init__(self, event_id: str, tool: str, target: str, paths: List[str],
                 line_range: Optional[Tuple[int, int]], output_bytes: int,
                 command: str = "", output_known: bool = True,
                 executed_bodies: Optional[List[str]] = None) -> None:
        self.search = _search_identity(command) if tool in ("shell", "run_command") else None
        self.executed_bodies = executed_bodies or []
        self.event_id = event_id
        self.tool = tool
        self.target = target
        self.paths = paths
        self.line_range = line_range
        self.output_bytes = output_bytes
        self.command = command
        self.output_known = output_known
        self.cls = ""
        self.label = ""
        self.reason = ""
        self.path = ""  # the path the class was decided on


# ------------------------------------------------------------------ parsers

_SHELL_WRAPPER_RE = re.compile(r"(pwsh|powershell|bash|sh|zsh|cmd)(\.exe)?$", re.IGNORECASE)


def _shell_payload(command) -> str:
    """The script a shell wrapper runs, without the wrapper's own argv.

    Codex records `["C:/.../pwsh.exe", "-Command", "<script>"]` or
    `["bash", "-lc", "<script>"]`; joining that argv put `C:/Program` in the
    path list. The payload is the last element after a `-Command`, `-c`, or
    `-lc` flag; any other list is joined with spaces.
    """
    if isinstance(command, str):
        return command
    if not isinstance(command, list) or not command:
        return ""
    argv = [str(c) for c in command]
    if len(argv) >= 3 and _SHELL_WRAPPER_RE.search(argv[0].replace("\\", "/").rsplit("/", 1)[-1]):
        flags = {a.lower() for a in argv[1:-1]}
        if flags & {"-command", "-c", "-lc", "-noprofile", "-nologo", "-noninteractive", "/c"}:
            return argv[-1]
    return " ".join(argv)


def _parse_codex(input_path: Path) -> Tuple[List[Event], int, int]:
    """Events, injected bytes, prompt bytes from a Codex rollout."""
    events: List[Event] = []
    injected = 0
    prompt = 0
    n = 0
    with open(input_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rtype = rec.get("type")
            payload = rec.get("payload") or {}
            if rtype == "response_item" and payload.get("role") == "user":
                for item in payload.get("content") or []:
                    if isinstance(item, dict) and item.get("type") == "input_text":
                        text = item.get("text") or ""
                        if text.startswith("# AGENTS.md instructions for"):
                            injected += len(text.encode("utf-8"))
                        else:
                            prompt += len(text.encode("utf-8"))
            elif rtype == "event_msg":
                item = payload.get("item")
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "UserMessage" and prompt == 0:
                    content = item.get("content")
                    if isinstance(content, str):
                        prompt += len(content.encode("utf-8"))
                    elif isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict):
                                prompt += len((c.get("text") or "").encode("utf-8"))
                elif item.get("type") == "CommandExecution":
                    cmd, bodies = _split_embedded_scripts(_shell_payload(item.get("command")))
                    out = item.get("aggregated_output")
                    known = out is not None
                    out_bytes = len(str(out or "").encode("utf-8"))
                    events.append(Event(
                        f"c{n}", "shell", cmd.strip()[:200], _paths_in_command(cmd),
                        _range_in_command(cmd), out_bytes, cmd, known, bodies))
                    n += 1
    return events, injected, prompt


def _parse_agy(input_path: Path, relay: Optional[Path]) -> Tuple[List[Event], Dict[str, int]]:
    """Events and prompt-relay byte split from an Antigravity tail."""
    split = {"preamble_bytes": 0, "request_bytes": 0, "diff_bytes_prompt": 0}
    if relay and relay.exists():
        text = relay.read_text(encoding="utf-8", errors="replace")
        marker = "--- ORIGINAL REVIEW REQUEST ---"
        idx = text.find(marker)
        if idx >= 0:
            split["preamble_bytes"] = len(text[:idx].encode("utf-8"))
            rest = text[idx + len(marker):]
            cut = len(rest)
            for dm in ("--- STAGED DIFF PROVIDED BY DISPATCHER ---", "--- STAGED DIFF ---"):
                j = rest.find(dm)
                if 0 <= j < cut:
                    cut = j
            split["request_bytes"] = len(rest[:cut].encode("utf-8"))
            split["diff_bytes_prompt"] = len(rest[cut:].encode("utf-8"))
        else:
            split["preamble_bytes"] = len(text.encode("utf-8"))

    events: List[Event] = []
    n = 0
    with open(input_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event") != "step_update":
                continue
            su = rec.get("step_update") or {}
            if su.get("step_type") != "tool" or su.get("state") != "DONE":
                continue
            tool = su.get("tool_name") or ""
            info = su.get("tool_info") or {}
            params = info.get("parameters") or {}
            output = info.get("output")
            known = output is not None
            output = output or ""
            if tool == "view_file":
                path = params.get("AbsolutePath") or ""
                start, end = params.get("StartLine"), params.get("EndLine")
                rng = (int(start), int(end)) if start is not None and end is not None else None
                m = _VIEW_FILE_RE.match(output.strip())
                out_bytes = int(m.group(2)) if m else 0
                known = bool(m)
                events.append(Event(f"a{n}", tool, path, [path], rng, out_bytes, "", known))
            elif tool == "run_command":
                cmd, bodies = _split_embedded_scripts(params.get("CommandLine") or "")
                events.append(Event(
                    f"a{n}", tool, cmd.strip()[:200], _paths_in_command(cmd),
                    _range_in_command(cmd), len(output.encode("utf-8")), cmd, known, bodies))
            elif tool in ("grep_search", "find_by_name", "search_web", "read_url_content"):
                query = params.get("Query") or params.get("Pattern") or params.get("Url") or ""
                where = params.get("SearchPath") or params.get("SearchDirectory") or ""
                target = f"{tool}:{query}@{where}"
                events.append(Event(f"a{n}", tool, target, [], None,
                                    len(output.encode("utf-8")), target, known))
            elif tool == "list_dir":
                path = params.get("DirectoryPath") or ""
                events.append(Event(f"a{n}", tool, path, [], None,
                                    len(output.encode("utf-8")), f"list_dir {path}", known))
            else:
                target = params.get("TargetFile") or params.get("AbsolutePath") or tool
                events.append(Event(f"a{n}", tool, str(target), [], None,
                                    len(output.encode("utf-8")), f"{tool} {target}", known))
            n += 1
    return events, split


def detect_backend(input_path: Path) -> str:
    with open(input_path, encoding="utf-8", errors="replace") as fh:
        first = fh.readline().strip()
    try:
        rec = json.loads(first)
    except json.JSONDecodeError:
        return "antigravity"
    if isinstance(rec, dict) and "event" in rec:
        return "antigravity"
    return "codex"


# ----------------------------------------------------------- classification

class _State:
    def __init__(self) -> None:
        self.diffs = 0
        self.sources: Dict[str, Dict[str, object]] = {}
        self.others: Dict[str, int] = {}


_TOKEN_RE = re.compile(r"'[^']*'|\"[^\"]*\"|\S+")
_INTERPRETER_RE = re.compile(
    r"^(python(3)?(\.exe)?|pwsh(\.exe)?|powershell(\.exe)?|bash|sh|zsh|node|npm|pytest)$",
    re.IGNORECASE,
)
_SEPARATORS = {";", "|", "&&", "||", "&"}


def _executed_paths(command: str) -> List[str]:
    """Paths a command executes (interpreter operands), as opposed to reads.

    The interpreter may be quoted (`& 'C:/.../python.exe' x.py`), the script
    may follow `-File`, and `-m module` or `-c code` names no path.
    """
    tokens = [t.strip("'\"") for t in _TOKEN_RE.findall(command)]
    out: List[str] = []
    i = 0
    while i < len(tokens):
        base = tokens[i].replace("\\", "/").rsplit("/", 1)[-1]
        if _INTERPRETER_RE.match(base):
            j = i + 1
            while j < len(tokens):
                nxt = tokens[j]
                low = nxt.lower()
                if low in _SEPARATORS:
                    break
                if low in ("-file", "-f"):
                    j += 1
                    continue
                if low in ("-m", "-c", "-command"):
                    j += 2
                    continue
                if nxt.startswith("-"):
                    j += 1
                    continue
                out.append(nxt.rstrip(";|&"))
                break
            i = j
        i += 1
    return out


def _executes_something(command: str) -> bool:
    tokens = [t.strip("'\"") for t in _TOKEN_RE.findall(command)]
    return any(_INTERPRETER_RE.match(t.replace("\\", "/").rsplit("/", 1)[-1]) for t in tokens)


def _read_paths(ev: Event) -> List[str]:
    """The event's path operands that are read rather than executed."""
    if ev.tool == "view_file":
        return list(ev.paths)
    cmd = ev.command or ev.target
    excluded = {_norm(p) for p in _executed_paths(cmd)}
    # A redirection target is written, not read.
    excluded |= {_norm(p.strip("'\"")) for p in re.findall(r">>?\s*([^\s;|&]+)", cmd)}
    return [p for p in ev.paths if _norm(p) not in excluded]


def _decide_class(ev: Event, coord_roots: List[str], rule_files: List[str]) -> Tuple[str, str]:
    """(class, deciding path) for one event.

    Operands a command executes (`python x.py`, `pwsh x.ps1`) are not reads:
    running the coordinator's health-check script is a build step, not a
    skill read. Only read operands decide the document classes.
    """
    cmd = ev.command or ev.target
    if ev.tool in ("shell", "run_command") and _GIT_DIFF_RE.search(cmd):
        return "diff", ""
    reads = _read_paths(ev)
    coord = [p for p in reads if _under(p, coord_roots)]
    if coord:
        return "coordinator_skill", coord[0]
    rules = [p for p in reads if _is_rule_file(p, rule_files)]
    if rules:
        return "rules", rules[0]
    sinks = [p for p in reads if _is_review_sink(p)]
    if sinks:
        return "review_sink", sinks[0]
    if ev.tool in ("shell", "run_command") and (
            _TEST_BUILD_RE.search(cmd) or (_executes_something(cmd) and not _READ_CMD_RE.search(cmd))):
        return "tests_builds", ""
    if ev.tool == "view_file" and reads:
        return "source", reads[0]
    if ev.tool in ("shell", "run_command") and reads and (
            _READ_CMD_RE.search(cmd) or ev.search is not None):
        return "source", reads[0]
    return "other", ""


def _in_scope(ev: Event, scope: List[str]) -> bool:
    if not scope:
        return False
    return any(_under(p, scope) for p in _read_paths(ev))


def _mixed_reads(ev: Event, scope: List[str], supplied: List[str],
                 coord_roots: List[str], rule_files: List[str]) -> bool:
    """True when one output covers an in-scope read and an out-of-scope read
    that would be avoidable on its own (a supplied rule file or a coordinator
    skill file). The bytes cannot be apportioned, so the event is unresolved
    rather than required."""
    reads = _read_paths(ev)
    if len(reads) < 2 or not scope:
        return False
    inside = [p for p in reads if _under(p, scope)]
    if not inside or len(inside) == len(reads):
        return False
    for p in reads:
        if _under(p, scope):
            continue
        if _under(p, coord_roots):
            return True
        if _is_rule_file(p, rule_files) and any(
                _under(p, [sup]) or os.path.basename(_norm(p)) == os.path.basename(_norm(sup))
                for sup in supplied):
            return True
    return False


def _decide_label(ev: Event, cls: str, supplied: List[str], scope: List[str],
                  transport: str, reasons: Dict[str, str], st: _State,
                  coord_roots: Optional[List[str]] = None,
                  rule_files: Optional[List[str]] = None) -> Tuple[str, str]:
    coord_roots = coord_roots or DEFAULT_COORDINATOR_ROOTS
    rule_files = rule_files or DEFAULT_RULE_FILES
    key = _norm(ev.path)
    # A script body that runs on stdin may read anything; when it names a rule
    # file, a coordinator file, a review sink, or a diff, the event cannot be
    # labeled automatically.
    for body in ev.executed_bodies:
        names = _paths_in_command(body)
        sensitive = [p for p in names if _under(p, coord_roots) or _is_rule_file(p, rule_files) or _is_review_sink(p)]
        if sensitive or _GIT_DIFF_RE.search(body) or re.search(r"\bdiff\b", body):
            return "unresolved", "an executed script body names " + (", ".join(sensitive[:3]) if sensitive else "a diff") + "; adjudicate by hand"
    # The diff is governed by its transport, not by the paths it names.
    if cls == "diff":
        st.diffs += 1
        if transport == "embedded":
            return "avoidable", "diff obtained although the request embeds it"
        if st.diffs == 1:
            return "required", "first diff obtain (command transport)"
        return "avoidable", f"diff obtained again (#{st.diffs})"
    # A mixed event is judged as a whole first: an identical whole command seen
    # before is an exact repeat; otherwise its bytes cannot be split between an
    # in-scope read and a read that would be avoidable alone, so it is unresolved.
    whole = _norm(ev.command or ev.target)
    if _mixed_reads(ev, scope, supplied, coord_roots, rule_files):
        seen_whole = st.others.get(whole, 0)
        st.others[whole] = seen_whole + 1
        if seen_whole:
            return "avoidable", f"exact repeat of the same mixed command (#{seen_whole + 1})"
        return "unresolved", "one output covers an in-scope read and an out-of-scope read; adjudicate by hand"
    # An exact repeat is avoidable whatever the scope says: being under review
    # makes a read eligible, it does not excuse reading the same content twice.
    # Every file class keys on (path, range), so two ranges of one instruction
    # file are two reads.
    if cls in ("rules", "review_sink", "source", "coordinator_skill"):
        rec = st.sources.setdefault(key, {"full": 0, "ranges": {}})
        ranges: Dict[object, int] = rec["ranges"]  # type: ignore[assignment]
        if ev.search is not None:
            skey = ("search", ev.search)
            seen = ranges.get(skey, 0)
            ranges[skey] = seen + 1
            if seen:
                return "avoidable", f"same search of the same file again (#{seen + 1})"
        elif ev.line_range is None:
            full = int(rec["full"])  # type: ignore[arg-type]
            rec["full"] = full + 1
            if full:
                return "avoidable", f"full read of the same file again (#{full + 1})"
            if ranges:
                return "unresolved", "full read after targeted reads of the same file"
        else:
            seen = ranges.get(ev.line_range, 0)
            ranges[ev.line_range] = seen + 1
            if seen:
                return "avoidable", f"same range read again (#{seen + 1})"
    elif cls == "other":
        other_key = _norm(ev.command or ev.target)
        seen = st.others.get(other_key, 0)
        st.others[other_key] = seen + 1
        if seen:
            return "avoidable", f"exact repeat of the same command (#{seen + 1})"
    # First reads: scope and a recorded reason make any read required.
    if _in_scope(ev, scope):
        return "required", "path is in review_scope"
    if ev.event_id in reasons:
        return "required", "verification reason: " + str(reasons[ev.event_id])
    if cls == "rules":
        if any(_under(ev.path, [s]) or os.path.basename(key) == os.path.basename(_norm(s))
               for s in supplied):
            return "avoidable", "re-read of a supplied instruction file"
        return "required", "first read of an instruction file that was not supplied"
    if cls == "coordinator_skill":
        if "example-reviews" in key:
            return "avoidable", "example-reviews read outside the review scope"
        if ev.line_range is None and ev.search is None:
            return "avoidable", "full read of the coordinator skill outside the review scope"
        return "unresolved", "targeted read of the coordinator skill outside the scope, no reason recorded"
    if cls == "source":
        if ev.search is not None:
            return "required", f"first search of the file for {ev.search!r}"
        if ev.line_range is None:
            return "required", "first read of the file"
        return "required", f"first read of lines {ev.line_range[0]}-{ev.line_range[1]}"
    if cls == "review_sink":
        return "required", "first read of the reviewer's own review file"
    if cls == "tests_builds":
        return "required", "test or build run"
    return "required", "first occurrence"


def classify(input_path, round_path, prompt_relay=None) -> dict:
    """Classify one round. Returns the machine report as a dict."""
    input_path = Path(input_path)
    round_path = Path(round_path)
    cfg = json.loads(round_path.read_text(encoding="utf-8"))
    backend = cfg.get("backend") or detect_backend(input_path)
    if backend not in ("codex", "antigravity"):
        backend = detect_backend(input_path)
    supplied = list(cfg.get("supplied_instruction_files") or [])
    scope = list(cfg.get("review_scope") or [])
    transport = cfg.get("diff_transport") or "command"
    coord_roots = list(cfg.get("coordinator_skill_roots") or DEFAULT_COORDINATOR_ROOTS)
    rule_files = list(cfg.get("rule_files") or DEFAULT_RULE_FILES)
    reasons = dict(cfg.get("verification_reasons") or {})

    report: dict = {"backend": backend, "input": str(input_path), "round": str(round_path)}
    if backend == "codex":
        events, injected, prompt = _parse_codex(input_path)
        report["injected_bytes"] = injected
        report["prompt_bytes"] = prompt
    else:
        relay = Path(prompt_relay) if prompt_relay else input_path.parent / "prompt-relay"
        events, split = _parse_agy(input_path, relay if relay.exists() else None)
        report.update(split)

    st = _State()
    rows = []
    by_class: Dict[str, int] = {}
    by_label: Dict[str, int] = {"required": 0, "avoidable": 0, "unresolved": 0}
    unresolved = []
    unknown = 0
    for ev in events:
        ev.cls, ev.path = _decide_class(ev, coord_roots, rule_files)
        ev.label, ev.reason = _decide_label(ev, ev.cls, supplied, scope, transport, reasons, st,
                                            coord_roots, rule_files)
        if not ev.output_known:
            unknown += 1
        row = {
            "event_id": ev.event_id, "tool": ev.tool, "target": ev.target,
            "path": ev.path, "line_range": list(ev.line_range) if ev.line_range else None,
            "output_bytes": ev.output_bytes, "output_known": ev.output_known,
            "class": ev.cls, "label": ev.label, "reason": ev.reason,
        }
        rows.append(row)
        by_class[ev.cls] = by_class.get(ev.cls, 0) + ev.output_bytes
        by_label[ev.label] = by_label.get(ev.label, 0) + ev.output_bytes
        if ev.label == "unresolved":
            unresolved.append(row)
    report["events"] = rows
    report["totals"] = {
        "by_class": by_class,
        "by_label": by_label,
        "tool_output_total": sum(r["output_bytes"] for r in rows),
        "events": len(rows),
        "events_without_usable_output": unknown,
    }
    report["unresolved_events"] = unresolved
    return report


# --------------------------------------------------------------------- CLI

def print_table(report: dict, out=None) -> None:
    out = out or sys.stdout
    print(f"{'id':<6} {'tool':<13} {'bytes':>9} {'class':<18} {'label':<11} target | reason", file=out)
    for r in report["events"]:
        mark = "" if r["output_known"] else " (no usable output)"
        rng = f" [{r['line_range'][0]}-{r['line_range'][1]}]" if r["line_range"] else ""
        print(f"{r['event_id']:<6} {r['tool']:<13} {r['output_bytes']:>9} {r['class']:<18} "
              f"{r['label']:<11} {r['target'][:70]}{rng} | {r['reason']}{mark}", file=out)
    t = report["totals"]
    print("\nTotals by class (tool-output bytes):", file=out)
    for cls, b in sorted(t["by_class"].items()):
        print(f"  {cls:<18} {b:>10}", file=out)
    print("Totals by label (tool-output bytes):", file=out)
    for lbl in ("required", "avoidable", "unresolved"):
        print(f"  {lbl:<18} {t['by_label'].get(lbl, 0):>10}", file=out)
    print(f"  {'tool_output_total':<18} {t['tool_output_total']:>10}  "
          f"({t['events']} events, {t['events_without_usable_output']} without usable output)", file=out)
    print("Prompt and injected bytes (reported separately, never in the tool-output totals):", file=out)
    for key in ("injected_bytes", "prompt_bytes", "preamble_bytes", "request_bytes", "diff_bytes_prompt"):
        if key in report:
            print(f"  {key:<18} {report[key]:>10}", file=out)
    if report["unresolved_events"]:
        print("Unresolved events (adjudicate by hand before any zero-avoidable claim):", file=out)
        for r in report["unresolved_events"]:
            print(f"  {r['event_id']}: {r['target'][:90]} | {r['reason']}", file=out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="classify_reviewer_io.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Codex rollout .jsonl or Antigravity tail")
    parser.add_argument("--round", required=True, dest="round_json", help="round.json")
    parser.add_argument("--json", dest="json_out", default=None, help="write the machine report here")
    parser.add_argument("--prompt-relay", default=None,
                        help="Antigravity prompt-relay (default: the file beside the tail)")
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    round_path = Path(args.round_json)
    if not input_path.is_file():
        print(f"error: input not found: {input_path}", file=sys.stderr)
        return 2
    if not round_path.is_file():
        print(f"error: round.json not found: {round_path}", file=sys.stderr)
        return 2
    report = classify(input_path, round_path, args.prompt_relay)
    print_table(report)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
