# clock_sources.py - what the clock is told by the system
#
# See "Designdocument Time.md", 4.1 to 4.3. Three things, and nothing more:
#   - the idle time: how long no input came. Asked from the desktop's idle monitor (Cinnamon,
#     GNOME), the freedesktop screensaver (KDE) or, on X11, the XScreenSaver extension.
#   - whether a program keeps the screensaver away (a video): the session manager's
#     "idle inhibited" flag (GNOME, Cinnamon), or KDE's power management.
#   - the active project: the top bar writes it into a small file, the clock reads it.
#
# Security: the clock never reads which keys were pressed or where the mouse is; it asks only
# "how long since the last input?". D-Bus is asked through gdbus, one call each.

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from core.brand import CONFIG_DIR, config_dir

Run = Callable[[Sequence[str]], Tuple[int, str]]
_VALUE = re.compile(r"^\((?:(?:uint64|uint32|int64|int32)\s+)?(\d+|true|false),\)$")


def run_command(command: Sequence[str]) -> Tuple[int, str]:
    try:
        done = subprocess.run(list(command), capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return done.returncode, done.stdout


def gdbus_value(output: str):
    """The one value of a gdbus answer: a number or true/false; None if it is something else."""
    match = _VALUE.match(output.strip())
    if not match:
        return None
    text = match.group(1)
    if text in ("true", "false"):
        return text == "true"
    return int(text)


def _call(run: Run, dest: str, path: str, method: str, *args: str):
    code, output = run(["gdbus", "call", "--session", "--dest", dest, "--object-path", path,
                        "--method", method, *args])
    return gdbus_value(output) if code == 0 else None


# --- idle time -------------------------------------------------------------------------------

@dataclass(frozen=True)
class BusIdle:
    """An idle monitor on the session bus; unit: seconds per answer unit (0.001: milliseconds)."""
    name: str
    dest: str
    path: str
    method: str
    unit: float

    def idle(self, run: Run) -> Optional[timedelta]:
        value = _call(run, self.dest, self.path, self.method)
        if value is None or isinstance(value, bool):
            return None
        return timedelta(seconds=value * self.unit)


class X11Idle:
    """The XScreenSaver extension of X11 (what xprintidle asks)."""
    name = "x11"

    class _Info(ctypes.Structure):
        _fields_ = [("window", ctypes.c_ulong), ("state", ctypes.c_int), ("kind", ctypes.c_int),
                    ("til_or_since", ctypes.c_ulong), ("idle", ctypes.c_ulong),
                    ("eventMask", ctypes.c_ulong)]

    def __init__(self, load: Callable[[str], Optional[ctypes.CDLL]] = None) -> None:
        self._load = load or _load_library
        self._libraries = None
        self._display = None

    def idle(self, _run: Run) -> Optional[timedelta]:
        if self._libraries is None:
            x11, xss = self._load("X11"), self._load("Xss")
            if x11 is None or xss is None:
                return None
            x11.XOpenDisplay.restype = ctypes.c_void_p
            x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
            x11.XDefaultRootWindow.restype = ctypes.c_ulong
            x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
            xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(self._Info)
            xss.XScreenSaverQueryInfo.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(self._Info)]
            self._libraries = (x11, xss)
        x11, xss = self._libraries
        if self._display is None:
            self._display = x11.XOpenDisplay(None)
            if not self._display:
                self._display = None
                return None
        info = xss.XScreenSaverAllocInfo()
        try:
            if not xss.XScreenSaverQueryInfo(self._display, x11.XDefaultRootWindow(self._display), info):
                return None
            return timedelta(milliseconds=info.contents.idle)
        finally:
            x11.XFree(info)


def _load_library(name: str) -> Optional[ctypes.CDLL]:
    found = ctypes.util.find_library(name)
    if not found:
        return None
    try:
        return ctypes.CDLL(found)
    except OSError:
        return None


MUFFIN = BusIdle("cinnamon", "org.cinnamon.Muffin.IdleMonitor", "/org/cinnamon/Muffin/IdleMonitor/Core",
                 "org.cinnamon.Muffin.IdleMonitor.GetIdletime", 0.001)
MUTTER = BusIdle("gnome", "org.gnome.Mutter.IdleMonitor", "/org/gnome/Mutter/IdleMonitor/Core",
                 "org.gnome.Mutter.IdleMonitor.GetIdletime", 0.001)
FREEDESKTOP = BusIdle("freedesktop", "org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver",
                      "org.freedesktop.ScreenSaver.GetSessionIdleTime", 1.0)
X11 = X11Idle()


def idle_sources(desktop: str = "", session: str = "") -> List:
    """The sources to try, the desktop's own first."""
    desktop, session = desktop.lower(), session.lower()
    if "cinnamon" in desktop:
        order = [MUFFIN, FREEDESKTOP]
    elif "gnome" in desktop:
        order = [MUTTER, FREEDESKTOP]
    else:
        order = [FREEDESKTOP, MUFFIN, MUTTER]
    if session != "wayland":
        order.append(X11)
    return order


class IdleTime:
    """The idle time from the first source that answers; that one is kept."""

    def __init__(self, sources: Optional[List] = None, run: Run = run_command) -> None:
        self.sources = sources if sources is not None else idle_sources(
            os.environ.get("XDG_CURRENT_DESKTOP", ""), os.environ.get("XDG_SESSION_TYPE", ""))
        self.run = run
        self.source = None

    def __call__(self) -> Optional[timedelta]:
        if self.source is not None:
            value = self.source.idle(self.run)
            if value is not None:
                return value
            self.source = None
        for source in self.sources:
            value = source.idle(self.run)
            if value is not None:
                self.source = source
                return value
        return None


# --- a video ---------------------------------------------------------------------------------

_IDLE_FLAG = "8"  # GsmInhibitorFlag "idle": a program keeps the session from going idle


class Inhibited:
    """Whether a program keeps the screensaver away (a video plays)."""

    def __init__(self, run: Run = run_command) -> None:
        self.run = run

    def __call__(self) -> bool:
        session = _call(self.run, "org.gnome.SessionManager", "/org/gnome/SessionManager",
                        "org.gnome.SessionManager.IsInhibited", _IDLE_FLAG)
        if session is True:
            return True
        power = _call(self.run, "org.freedesktop.PowerManagement", "/org/freedesktop/PowerManagement/Inhibit",
                      "org.freedesktop.PowerManagement.Inhibit.HasInhibit")
        return power is True


# --- the active project ----------------------------------------------------------------------

def active_file() -> Path:
    """Where the top bar tells the clock the active project: the runtime folder (gone at logout)."""
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    base = Path(runtime) / CONFIG_DIR if runtime else config_dir()
    return base / "active-project.json"


def write_active(place: Path, project: Optional[Path], person: str) -> None:
    place.parent.mkdir(parents=True, exist_ok=True)
    temporary = place.with_name(f".{place.name}.writing")
    temporary.write_text(json.dumps({"project": str(project) if project else None, "person": person},
                                    ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, place)


def read_active(place: Path) -> Tuple[Optional[Path], str]:
    try:
        data = json.loads(place.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, ""
    if not isinstance(data, dict):
        return None, ""
    project, person = data.get("project"), data.get("person")
    if not isinstance(project, str) or not project:
        return None, ""
    return Path(project), person if isinstance(person, str) else ""
