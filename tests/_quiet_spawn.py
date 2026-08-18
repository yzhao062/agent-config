"""Stop the suite from flashing console windows on Windows.

Importing this module installs the default. It is a no-op elsewhere.

A suite started as a background task runs in a process with no console. Each
shell it spawns is a console application, so Windows gives that shell a console
of its own and shows it. The suite spawns shells continuously, so a window
appears and vanishes about once a second across whatever else is on screen,
taking focus each time.

`CREATE_NO_WINDOW` removes that window. Measured from a console-less parent,
three runs of a shell each way: three windows without the flag, zero with it,
under both Windows PowerShell 5.1 and PowerShell 7.

It only reaches the process it is applied to, and that limit is worth stating
because it cost several wrong conclusions. A shell started with this flag has
no console at all, so if that shell then runs something that needs one, the
grandchild allocates its own and *that* window is shown. The suite's fixtures
used to put `git.cmd` and `python.cmd` on `PATH`; PowerShell runs a batch
target through `cmd.exe`, and `cmd.exe` then owned a visible window per
interpreter probe. Nothing on the Python side reached it: `CREATE_NO_WINDOW`,
`STARTF_USESHOWWINDOW` with `SW_HIDE`, the two combined, `CREATE_NEW_CONSOLE`
with `SW_HIDE`, and a runner process holding its own hidden console were all
measured against the real fixture, and every one of them left four windows
owned by `cmd.exe`. The fixtures now use `.ps1` stubs, which PowerShell runs
in-process, so there is no grandchild to suppress. See anywhere-agents#38.

So this module and the `.ps1` stubs are one fix in two halves: the flag
silences the shell, and the stubs remove the layer the flag cannot reach.

Patching the module rather than adding a wrapper at every call site is
deliberate. A wrapper covers only the sites that remember to use it, and the
next helper someone writes flashes again. Nineteen of this suite's twenty-two
test modules spawn processes.
"""
from __future__ import annotations

import subprocess
import sys

CREATE_NO_WINDOW = 0x08000000
_INSTALLED_FLAG = "_agent_config_quiet_spawn_installed"


def _with_flag(kwargs: dict) -> dict:
    kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
    return kwargs


def install() -> bool:
    """Patch `subprocess.run` and `subprocess.Popen`. Idempotent."""
    if not sys.platform.startswith("win"):
        return False
    if getattr(subprocess, _INSTALLED_FLAG, False):
        return False

    real_run = subprocess.run
    real_popen = subprocess.Popen

    def run(*args, **kwargs):
        return real_run(*args, **_with_flag(kwargs))

    class Popen(real_popen):  # type: ignore[misc, valid-type]
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **_with_flag(kwargs))

    # `real_run` builds its Popen from the module global, which is now the
    # subclass, so the flag is applied twice on that path. Or-ing a flag with
    # itself is why that is safe rather than merely harmless.
    subprocess.run = run
    subprocess.Popen = Popen
    setattr(subprocess, _INSTALLED_FLAG, True)
    return True


install()
