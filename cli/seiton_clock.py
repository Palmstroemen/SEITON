#!/usr/bin/env python3
"""
seiton-clock - start the clock of the time tracking with its role ("Designdocument Time.md",
section 7): mount the drive of its role, start daemon/clock_daemon.py with bubblewrap, and
unmount when it ends. --no-sandbox runs it directly (development, or where bwrap is missing).
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from core import clock_widget as cw  # noqa: E402
from core import sandbox as sb  # noqa: E402
from core.clock import default_store  # noqa: E402
from core.clock_sources import active_file  # noqa: E402
from core.programs import role_for  # noqa: E402
from core.settings import Settings  # noqa: E402

PROGRAM = "seiton-clock"


def drive_place(runtime: Optional[str] = None) -> Path:
    """Where the role's drive is mounted: apart from the folder the sandbox gets (active file)."""
    runtime = runtime or os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / "seiton-drives" / PROGRAM


def no_new_privs(status: Path = Path("/proc/self/status")) -> bool:
    """True when this process may not gain privileges (no_new_privs): then the setuid
    fusermount cannot mount the role's drive. Tools that sandbox their shells set it."""
    try:
        for line in status.read_text().splitlines():
            if line.startswith("NoNewPrivs:"):
                return line.split(":", 1)[1].strip() == "1"
    except OSError:
        pass
    return False


def clock_arguments(settings: Settings) -> List[str]:
    args = ["--language", settings.get("General/language"), "--pause", str(settings.get("Time/pauseMinutes")),
            "--recent", settings.get("Time/recentShows")]
    if not settings.get("Time/autoResume"):
        args.append("--no-resume")
    if not settings.get("Time/deadMan"):
        args.append("--no-dead-man")
    return args


def sandboxed(projects_root: Path, *, python: str, settings: Settings, mount: Path,
              place: Optional[sb.Place] = None, info_fd: Optional[int] = None) -> List[str]:
    """The bwrap command for the clock: its role's folders, its state, the active project."""
    role = role_for(PROGRAM)
    if role is None:
        raise SystemExit(f"{PROGRAM}: no role in Programs.md")
    home = Path.home()
    keep = [REPO]
    prefix = Path(sys.prefix)
    if home in prefix.parents:
        keep.append(prefix)  # SEITON's venv
    # Always hidden: below the home it would show again inside a kept folder (SEITON_Test in
    # the repository), elsewhere it would show anyway.
    hide = [projects_root]
    place = place or sb.Place.here(keep=keep, hide=hide)
    store = default_store()
    store.parent.mkdir(parents=True, exist_ok=True)
    active = active_file()
    active.parent.mkdir(parents=True, exist_ok=True)
    # Its widget in the Headline (core/clock_widget.py): the one folder it writes besides its
    # state - its view, and the commands the Headline drops there.
    widget = cw.folder()
    widget.mkdir(parents=True, exist_ok=True)
    binds = sb.role_binds(role, mount=mount) + [
        sb.Bind(store.parent, sb.INSIDE / "state", writable=True),
        sb.Bind(active.parent, sb.INSIDE / "run", writable=False),
        sb.Bind(widget, sb.INSIDE / "widget", writable=True),
    ]
    program = [python, str(REPO / "daemon" / "clock_daemon.py"),
               "--drive", str(sb.INSIDE / "0_Admin" / "Zeitaufwand"), "--projects-root", str(projects_root),
               "--store", str(sb.INSIDE / "state" / store.name),
               "--active", str(sb.INSIDE / "run" / active.name), "--widget", str(sb.INSIDE / "widget"),
               *clock_arguments(settings)]
    return sb.command(program, place=place, binds=binds, env={"PYTHONPATH": str(REPO)}, info_fd=info_fd)


def _wait_mounted(mount: Path, drive: subprocess.Popen, seconds: float = 10.0) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if os.path.ismount(mount):
            return True
        if drive.poll() is not None:
            return False
        time.sleep(0.1)
    return False


def _run_sandboxed(projects_root: Path, *, python: str, settings: Settings, mount: Path) -> int:
    """Start the clock in its sandbox; SIGTERM, SIGINT and SIGHUP are passed on to it, so it
    closes its running stretch before it ends (bwrap itself would just kill it)."""
    read_end, write_end = os.pipe()
    clock = subprocess.Popen(sandboxed(projects_root, python=python, settings=settings, mount=mount,
                                       info_fd=write_end), pass_fds=(write_end,))
    os.close(write_end)
    try:
        info = json.loads(os.read(read_end, 4096).decode() or "{}")
    except ValueError:
        info = {}
    finally:
        os.close(read_end)
    child = info.get("child-pid")

    def pass_on(signum, _frame):
        if child:
            try:
                os.kill(child, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, pass_on)
    while True:
        try:
            return clock.wait()
        except InterruptedError:
            continue


def run(projects_root: Path, *, sandbox: bool = True) -> int:
    settings = Settings()
    python = sys.executable
    if not sandbox:
        return subprocess.call([python, str(REPO / "daemon" / "clock_daemon.py"), *clock_arguments(settings)])
    if shutil.which("bwrap") is None:
        print("bwrap is missing: install bubblewrap, or start with --no-sandbox", file=sys.stderr)
        return 1
    if no_new_privs():
        print(f"{PROGRAM}: this process runs with no_new_privs (started from a sandboxed tool?), so "
              "fusermount may not mount the drive of its role. Start it from a normal terminal, "
              "or with --no-sandbox.", file=sys.stderr)
        return 1
    mount = drive_place()
    mount.mkdir(parents=True, exist_ok=True)
    drive = subprocess.Popen([python, "-m", "core.role_drive", PROGRAM, str(projects_root), str(mount)], cwd=REPO)
    try:
        if not _wait_mounted(mount, drive):
            print(f"the drive of {PROGRAM} did not come up at {mount}", file=sys.stderr)
            return 1
        return _run_sandboxed(projects_root, python=python, settings=settings, mount=mount)
    finally:
        subprocess.call(["fusermount", "-u", str(mount)], stderr=subprocess.DEVNULL)
        try:
            drive.wait(timeout=5)
        except subprocess.TimeoutExpired:
            drive.terminate()


def default_root(home: Optional[Path] = None) -> Optional[Path]:
    """Started without a root (at login, from the time screen): the first root below the home
    folder, as the Headline does (Designdocument Perspective Resolver MVP.md, A11)."""
    from core.scope_api import roots_below  # late: heavy
    below = roots_below(Path(home) if home is not None else Path.home())
    return below[0] if below else None


def hold_lock(folder: Path):
    """One clock per user: the lock in the clock's widget folder, held while it runs; None when
    another clock holds it."""
    import fcntl
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    handle = open(folder / "clock.lock", "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Start the clock of the time tracking with its role.")
    parser.add_argument("--projects-root", type=Path, default=None,
                        help="the folder holding the projects; else the first root below the home folder")
    parser.add_argument("--no-sandbox", action="store_true", help="run without bubblewrap and role drive")
    args = parser.parse_args(argv)
    lock = hold_lock(cw.folder())
    if lock is None:
        return 0  # a clock runs already (a second start from the time screen, or at login)
    root = args.projects_root or default_root()
    if root is None:
        print(f"{PROGRAM}: no projects root below {Path.home()}; give one with --projects-root",
              file=sys.stderr)
        return 1
    return run(Path(root).expanduser().resolve(), sandbox=not args.no_sandbox)


if __name__ == "__main__":
    raise SystemExit(main())
