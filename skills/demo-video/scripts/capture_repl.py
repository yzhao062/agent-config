"""Run each scene's lines in a real Python REPL and record what it prints, for the terminal scenes of a demo video.

    python capture_repl.py SCENES.json SITE/data.js [--width 120]

SCENES.json maps a scene name to the lines typed at the prompt, in order; an empty string ends an indented block, as
at a real prompt. All scenes share one REPL, so a later scene can use names an earlier one defined. Each typed line
becomes colored code tokens and each output becomes colored segments, wrapped at the terminal width the way a
terminal would wrap them. Nothing on screen is written by hand: run this with the released package installed.

rich prints colors to a redirected stdout only when told the stream is a color terminal, so this script sets
FORCE_COLOR, COLORTERM, TERM and COLUMNS and clears NO_COLOR before anything imports rich (an agent's shell often has
TERM=dumb, which makes rich drop colors and wrap at 80 columns, or NO_COLOR=1, which drops colors).
"""
import argparse
import code
import contextlib
import io
import json
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("scenes")
ap.add_argument("out")
ap.add_argument("--width", type=int, default=120)
args = ap.parse_args()
os.environ.pop("NO_COLOR", None)
os.environ.update(FORCE_COLOR="1", COLORTERM="truecolor", TERM="xterm-256color", COLUMNS=str(args.width))

from pygments.lexers import PythonLexer  # noqa: E402
from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String  # noqa: E402
from rich.color import ColorType  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.terminal_theme import TerminalTheme  # noqa: E402
from rich.text import Text  # noqa: E402

WIDTH = args.width
# ANSI colors for a dark terminal; tune them to the project's palette.
THEME = TerminalTheme(
    (14, 35, 38), (228, 236, 238),
    [(29, 42, 46), (237, 141, 90), (125, 196, 168), (233, 185, 73), (108, 180, 201), (217, 139, 176), (159, 214, 198), (210, 220, 223)],
    [(127, 146, 150), (245, 168, 128), (159, 222, 196), (242, 206, 128), (143, 208, 224), (232, 168, 200), (191, 232, 220), (255, 255, 255)],
)
CODE_COLORS = [(Keyword, "#F5A880"), (Name.Builtin, "#9FD6C6"), (String, "#F2CE80"), (Number, "#F2CE80"),
               (Comment, "#7F9296"), (Operator, "#C9D6DA"), (Punctuation, "#C9D6DA"), (Name.Function, "#8FD0E0")]
DEFAULT_CODE = "#E4ECEE"
ATTRIBUTE = "#8FD0E0"
_console = Console(color_system="truecolor")


def code_tokens(line):
    tokens = []
    for kind, value in PythonLexer().get_tokens(line):
        value = value.replace("\n", "")
        if not value:
            continue
        color = next((c for k, c in CODE_COLORS if kind in k), DEFAULT_CODE)
        if kind in Name and tokens and tokens[-1][0] == ".":
            color = ATTRIBUTE
        tokens.append([value, color])
    return tokens


def css(style):
    if style is None:
        return ""
    rules = []
    if style.color is not None and style.color.type != ColorType.DEFAULT:
        rules.append("color:" + style.color.get_truecolor(THEME).hex)
    if style.bgcolor is not None and style.bgcolor.type != ColorType.DEFAULT:
        rules.append("background:" + style.bgcolor.get_truecolor(THEME, foreground=False).hex)
    if style.bold:
        rules.append("font-weight:700")
    if style.dim:
        rules.append("opacity:.62")
    if style.italic:
        rules.append("font-style:italic")
    if style.underline:
        rules.append("text-decoration:underline")
    return ";".join(rules)


def runs(text):
    """(start, end, style) runs that cover every character of a Text once."""
    n = len(text.plain)
    cuts = sorted({0, n, *(s.start for s in text.spans), *(s.end for s in text.spans)})
    for a, b in zip(cuts, cuts[1:]):
        if a < b:
            yield a, b, (text.get_style_at_offset(_console, a) if text.spans else None)


def out_lines(ansi):
    """ANSI output to display lines of [text, css] segments, wrapped at WIDTH."""
    lines = []
    for text in Text.from_ansi(ansi).split("\n", allow_blank=True):     # parse once, so a color spans lines
        line, col = [], 0
        for a, b, style in runs(text):
            chunk = text.plain[a:b]
            while chunk:
                part, chunk = chunk[: WIDTH - col], chunk[WIDTH - col:]
                line.append([part, css(style)])
                col += len(part)
                if col >= WIDTH and chunk:
                    lines.append(line)
                    line, col = [], 0
        lines.append([s for s in line if s[0]])
    while lines and not any(s[0].strip() for s in lines[-1]):
        lines.pop()
    return lines


def main():
    with open(args.scenes, encoding="utf-8") as f:
        scenes_in = json.load(f)
    repl = code.InteractiveConsole({"__name__": "__console__"})
    scenes, more = {}, False
    for name, lines in scenes_in.items():
        entries = []
        for line in lines:
            prompt = "... " if more else ">>> "
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                more = repl.push(line)
            entries.append({"prompt": prompt, "code": code_tokens(line), "out": out_lines(buf.getvalue())})
            print(prompt + line, file=sys.stderr)
            if buf.getvalue():
                print(buf.getvalue().rstrip()[:600], file=sys.stderr)
        if more:
            sys.exit(f"scene {name!r} ends inside an open block; add an empty line")
        scenes[name] = entries
        print(f"-- {name}: {sum(1 + len(e['out']) for e in entries)} display lines", file=sys.stderr)
    meta = {"python": sys.version.split()[0], "width": WIDTH}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.CAPTURE = " + json.dumps({"meta": meta, "scenes": scenes}) + ";\n")
    print("wrote", args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
