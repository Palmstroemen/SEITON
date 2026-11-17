# role_drive.py - the drive of a program with a role
#
# See "Designdocument Time.md", 7.2. Each program with a role gets a perspective drive of its
# own (core/perspective_drive.py), without fallback: a missing department folder is shown empty,
# never the project or a folder above it. Every access must be allowed by the program's role
# (core/programs.py) and by the person's ACLs, the role asked first. Which program asks is told
# by the mount point, not by a process number: the program only ever sees this drive.

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

from core import time_log as tl
from core.perspective_drive import PROJECTS
from core.programs import Role, role_for

logger = logging.getLogger(__name__)

Acls = Callable[[str, Path], bool]  # acl_allows(action, path), as ScopeApi has it


def role_may(role: Role, projects_root: Union[str, Path], acls: Acls) -> Callable[[Path, str], bool]:
    """The drive's check: the role, then the person's ACLs."""
    root = Path(projects_root)

    def may(path: Path, action: str) -> bool:
        # Security: the role is a fence; the ACLs are not even asked outside it.
        if not role.allows(root, path, action):
            return False
        return bool(acls(action, Path(path)))
    return may


def drive_writer(folder: Path, projects_root: Union[str, Path], *, language: str,
                 add: Callable = tl.add_to_file):
    """The clock's writer inside its sandbox: a project's time file through the drive at folder
    (the role's /0_Admin/Zeitaufwand), /Projekte/<the project's way>/<person>.md."""
    root = Path(projects_root)

    def write(project: Path, person: str, stretch):
        try:
            rel = Path(project).relative_to(root)
        except ValueError:
            raise ValueError(f"{project}: not below {root}")
        name = tl.time_file(Path("/"), person).name  # Security: checks the person's name
        if not rel.parts or any(part in ("..", ".") or part.startswith(".") for part in rel.parts):
            raise ValueError(f"{project}: no project way")
        return add(Path(folder) / PROJECTS / rel / name, person, stretch, language=language)
    return write


def mount(program: str, projects_root: str, mount_point: str, acls: Optional[Acls] = None) -> None:
    """Mount the drive of program at mount_point (blocks until unmounted)."""
    from core.perspective_fuse import mount_perspective_drive

    role = role_for(program)
    if role is None:
        raise SystemExit(f"{program}: no role in Programs.md")
    if acls is None:
        from core.scope_api import ScopeApi  # late: heavy
        acls = ScopeApi(start_path=projects_root).acl_allows
    Path(mount_point).mkdir(parents=True, exist_ok=True)
    logger.info("role_drive.mount program=%s root=%s at=%s", program, projects_root, mount_point)
    mount_perspective_drive(projects_root=projects_root, mount_point=mount_point,
                            may=role_may(role, projects_root, acls), foreground=True, fallback=False)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mount the drive of a program with a role.")
    parser.add_argument("program")
    parser.add_argument("projects_root")
    parser.add_argument("mount_point")
    args = parser.parse_args(argv)
    mount(args.program, args.projects_root, args.mount_point)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
