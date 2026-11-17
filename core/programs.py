# programs.py - programs with a role, as people have one
#
# See "Designdocument Time.md", 7.1. What a program may at most is written down once, readable,
# in ~/.config/seiton/Programs.md:
#
#   ## Zeiterfassung
#   - Program: seiton-clock
#   - /0_Admin/Zeitaufwand/: read, write
#
# A rule's path is a path in every project (as in ACLs.md): one rule fits all projects, also
# those that do not exist yet. The role is a fence, not a right: the drive of the program asks
# the role and the person's ACLs, and both must allow.

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, List, Optional, Tuple, Union

from core.acl import _path_matches
from core.brand import META_DIR, config_dir

RIGHTS = {"read", "write", "delete", "*"}

# The roles SEITON's own programs have when Programs.md does not name them.
DEFAULT = """# Programs

## Zeiterfassung
- Program: seiton-clock
- /0_Admin/Zeitaufwand/: read, write
"""

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RULE = re.compile(r"^[-*]\s+(/\S.*?)\s*:\s*(.+)$")
_PROGRAM = re.compile(r"^[-*]\s+Program\s*:\s*(\S.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class Role:
    name: str
    program: str
    rules: List[Tuple[str, FrozenSet[str]]] = field(default_factory=list)

    def allows(self, projects_root: Union[str, Path], real: Union[str, Path], action: str) -> bool:
        """Whether the role lets the program do action on real (a path below projects_root)."""
        inside = _in_project(Path(projects_root), Path(real))
        if inside is None:
            return False
        rights: set = set()
        matching = [(path, r) for path, r in self.rules if _path_matches(path, inside)]
        if matching:  # the nearest rule wins, as in ACLs.md
            depth = max(len([p for p in path.split("/") if p]) for path, _r in matching)
            for path, r in matching:
                if len([p for p in path.split("/") if p]) == depth:
                    rights |= r
        return "*" in rights or action.strip().lower() in rights


def _in_project(projects_root: Path, real: Path) -> Optional[str]:
    """real as a path inside its nearest project ("/0_Admin/Zeitaufwand/Anna.md"), or None
    outside the projects root or outside any project."""
    # Security: the path is made absolute and "..", symlinks resolved first, so a way back out
    # of the allowed folder never matches its rule.
    try:
        root = projects_root.expanduser().resolve()
        target = Path(os.path.realpath(real.expanduser()))
    except OSError:
        return None
    if target != root and root not in target.parents:
        return None
    for folder in [target, *target.parents]:
        if folder == root.parent:
            break
        if (folder / META_DIR / "Project.md").is_file():
            rel = target.relative_to(folder).as_posix()
            return "/" if rel == "." else "/" + rel
    return None


def programs_file() -> Path:
    return config_dir() / "Programs.md"


def parse_with_problems(text: str) -> Tuple[List[Role], List[str]]:
    roles: List[Role] = []
    problems: List[str] = []
    name: Optional[str] = None
    program: Optional[str] = None
    rules: List[Tuple[str, FrozenSet[str]]] = []

    def close() -> None:
        if name is None:
            return
        if program:
            roles.append(Role(name=name, program=program, rules=list(rules)))
        else:
            problems.append(f"## {name}: no '- Program: ...' line")

    for line in text.splitlines():
        stripped = line.strip()
        heading = _HEADING.match(stripped)
        if heading:
            close()
            name, program, rules = (heading.group(2).strip(), None, []) if len(heading.group(1)) == 2 else (None, None, [])
            continue
        if name is None or not stripped.startswith(("- ", "* ")):
            continue
        found = _PROGRAM.match(stripped)
        if found:
            program = found.group(1).strip()
            continue
        rule = _RULE.match(stripped)
        rights = frozenset(r.strip().lower() for r in rule.group(2).split(",")) if rule else frozenset()
        if not rule or not rights or not rights <= RIGHTS or ".." in rule.group(1).split("/"):
            problems.append(f"## {name}: {stripped}")
            continue
        path = rule.group(1).strip().rstrip("/") or "/"
        rules.append((path, rights))
    close()
    return roles, problems


def parse(text: str) -> List[Role]:
    return parse_with_problems(text)[0]


def load() -> List[Role]:
    """The roles of Programs.md; SEITON's own programs keep their default role unless named there."""
    try:
        own = parse(programs_file().read_text(encoding="utf-8"))
    except OSError:
        own = []
    named = {role.program for role in own}
    return own + [role for role in parse(DEFAULT) if role.program not in named]


def role_for(program: str, roles: Optional[List[Role]] = None) -> Optional[Role]:
    for role in (roles if roles is not None else load()):
        if role.program == program:
            return role
    return None
