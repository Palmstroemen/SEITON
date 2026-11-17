# sandbox.py - a program with a role, started with bubblewrap
#
# See "Designdocument Time.md", 7.2 and 7.3. The program sees the system read-only, but no home,
# no /tmp (and with it no X11 socket), no runtime folder, no projects: of the projects only the
# folders its role names, from a drive of its own (core/role_drive.py), mounted inside at
# /tmp/seiton/<path in every project>. Its environment is cleared; the session bus comes along
# (the clock asks the idle time over it), the X11 display does not.
#
# Security: what stays open is named in the design document (7.3): the session bus without a
# filter, and whatever lies outside the home that is not hidden (pass it in `hide`).

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from core.programs import Role

INSIDE = Path("/tmp/seiton")  # where the program finds its folders (on the sandbox's own /tmp)


@dataclass(frozen=True)
class Bind:
    source: Path
    target: Path
    writable: bool


@dataclass(frozen=True)
class Place:
    """What the sandbox hides and keeps of the computer."""
    home: Path
    runtime: Path  # XDG_RUNTIME_DIR
    dbus: str  # DBUS_SESSION_BUS_ADDRESS
    keep: List[Path] = field(default_factory=list)  # read-only again (the code, the venv)
    hide: List[Path] = field(default_factory=list)  # also hidden (a projects root outside home)

    @classmethod
    def here(cls, keep: Sequence[Path] = (), hide: Sequence[Path] = ()) -> "Place":
        runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
        return cls(home=Path.home(), runtime=Path(runtime),
                   dbus=os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""), keep=list(keep), hide=list(hide))


def _bus_socket(address: str) -> Optional[str]:
    """The socket file of a session bus address; None for an abstract one (it cannot be bound)."""
    for part in address.split(";"):
        if part.startswith("unix:"):
            for item in part[5:].split(","):
                key, _, value = item.partition("=")
                if key == "path" and value:
                    return value
    return None


def role_binds(role: Role, *, mount: Path) -> List[Bind]:
    """The role's folders from its drive: writable where the role may write."""
    binds = []
    for path, rights in role.rules:
        rel = path.strip("/")
        writable = bool(rights & {"write", "delete", "*"})
        binds.append(Bind(mount / rel, INSIDE / rel, writable))
    return binds


def command(program: Sequence[str], *, place: Place, binds: Sequence[Bind],
            env: Optional[dict] = None, cwd: str = "/", info_fd: Optional[int] = None) -> List[str]:
    """The bwrap command line that starts program in its sandbox. The program is the sandbox's
    first process (--as-pid-1): bwrap does not pass signals on, so the launcher sends SIGTERM to
    it directly, by the pid bwrap writes to info_fd, and the program can end cleanly."""
    args = ["bwrap", "--die-with-parent", "--new-session", "--unshare-all", "--as-pid-1", "--clearenv",
            "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--tmpfs", "/tmp", "--tmpfs", str(place.home), "--tmpfs", str(place.runtime)]
    for kept in place.keep:
        args += ["--ro-bind", str(kept), str(kept)]
    # After the kept folders: a projects root inside the code (SEITON_Test) stays hidden too.
    for hidden in place.hide:
        if Path(hidden).is_dir():  # bwrap cannot put a tmpfs where there is nothing
            args += ["--tmpfs", str(hidden)]
    socket = _bus_socket(place.dbus)
    environment = {"HOME": str(place.home), "PATH": "/usr/local/bin:/usr/bin:/bin",
                   "LANG": os.environ.get("LANG", "C.UTF-8"), "XDG_RUNTIME_DIR": str(place.runtime)}
    if socket:
        args += ["--ro-bind", socket, socket]
        environment["DBUS_SESSION_BUS_ADDRESS"] = place.dbus
    for bind in binds:
        args += ["--bind" if bind.writable else "--ro-bind", str(bind.source), str(bind.target)]
    environment.update(env or {})
    for key, value in environment.items():
        args += ["--setenv", key, str(value)]
    if info_fd is not None:
        args += ["--info-fd", str(info_fd)]
    args += ["--chdir", cwd, "--"]
    return args + list(program)
