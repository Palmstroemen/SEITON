#!/usr/bin/env python3
"""
seiton - the one command of SEITON, like git or gh.

    seiton                      starts Scope where one is
    seiton <path> | --<task>    starts Scope there, or with a task (--setup, --search, --clipboard)
    seiton <command> ...        runs a tool: seiton ls, seiton tag, seiton acl sync, ...
    seiton help                 lists the commands

A first word that is a command is the command; everything else is for Scope. A folder that
happens to be called like a command opens with a path: seiton ./tag. A bare word that is
neither a command nor a folder here is a typo, not a place: it is said, with the closest
command.
"""

from __future__ import annotations

import difflib
import importlib
import os
import runpy
import sys
from pathlib import Path
from typing import Callable, List, Optional, Sequence

REPO = Path(__file__).resolve().parents[1]
# Started as a script, Python puts cli/ first on the path, and this file would hide every
# module called seiton (a package of that name is planned: Designdocument Public Interface).
if sys.path and Path(sys.path[0] or ".").resolve() == Path(__file__).resolve().parent:
    sys.path.pop(0)
if str(REPO) not in sys.path:  # make core and cli importable
    sys.path.insert(0, str(REPO))

from core.brand import COMMAND, NAME  # noqa: E402

# Each command and its module (cli/seiton_<name>.py), in the order the help shows them.
COMMANDS = {
    "ls": "list a folder, with embryos, tags, the newest files",
    "project": "create, check and tidy projects; the trash",
    "tag": "tags of files and folders",
    "acl": "rights: show, check, edit; bring them to Nextcloud (acl sync)",
    "edit": "open a project's settings files",
    "filter": "choose and show filters",
    "export": "pack a folder with its metadata",
    "import": "unpack such a package into a project",
    "drive": "mount the drive \"Perspektiven\"",
}
HELP_WORDS = ("help", "-h", "--help")


def prog(name: str) -> str:
    """The name a tool's help and errors show: "seiton ls"."""
    return f"{COMMAND} {name}"


def load(name: str):
    """The module of a command; imported only when it runs, so Scope starts without them."""
    return importlib.import_module(f"cli.seiton_{name}")


def usage() -> str:
    width = max(len(name) for name in COMMANDS)
    lines = [
        f"usage: {COMMAND} [<path> | --setup | --search | --clipboard]",
        f"       {COMMAND} <command> [<args>]",
        "",
        f"Without a command {COMMAND} starts Scope, {NAME}'s file browser. The commands:",
        "",
    ]
    lines += [f"  {name.ljust(width)}  {text}" for name, text in COMMANDS.items()]
    lines += ["", f"{COMMAND} <command> --help tells more about each."]
    return "\n".join(lines) + "\n"


def start_scope(args: List[str]) -> None:
    """Scope as if started itself (python3 apps/Scope/Scope.py): its folder first on the path,
    as Python puts it there for a script (Scope imports its neighbours), the arguments behind."""
    script = REPO / "apps" / "Scope" / "Scope.py"
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *args]
    runpy.run_path(str(script), run_name="__main__")


def _is_for_scope(word: str) -> bool:
    return word.startswith("-") or os.sep in word or Path(word).exists()


def main(argv: Optional[Sequence[str]] = None,
         start_gui: Callable[[List[str]], None] = start_scope) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        start_gui([])
        return 0
    first, rest = args[0], args[1:]
    if first in HELP_WORDS:
        sys.stdout.write(usage())
        return 0
    if first in COMMANDS:
        result = load(first).main(rest)
        return result if isinstance(result, int) else 0
    if _is_for_scope(first):
        start_gui(args)
        return 0
    close = difflib.get_close_matches(first, COMMANDS, n=1)
    hint = f" Did you mean: {COMMAND} {close[0]}?" if close else f" {COMMAND} help lists the commands."
    print(f"{COMMAND}: '{first}' is no command and no folder here.{hint}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
