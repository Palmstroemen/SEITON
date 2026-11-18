"""The time screen (core/Dokumentation/Designdocument Time.md, 5): the time tracking's own
window, opened from its widget in the Headline (apps/Scope/Designdocument Headline.md, 3a).

Now (the active project, the clock, Start/Stop), Entries (one's own rows of a project, newest
first: add, correct, take away), Overview (a project with its children, by period and person,
rounded as set). It works with the person's own rights - not the sandboxed clock - and talks to
the running clock as the Headline does: it reads the clock's view and drops commands.
No Qt here; its window only draws it.
"""

from __future__ import annotations

import getpass
import json
import re
import time as clock_time
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core import clock_widget as cw
from core import time_log as tl
from core.clock import default_store, rounding_from_settings
from core.clock_sources import active_file, read_active
from core.acl_enforcement import allowed_at
from core.identity import person_for
from core.perspective_session import is_project
from core.settings import Settings

STALE = 60  # seconds: an older view means the clock does not run
MAX_MINUTES = 24 * 60
_START = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _hours(duration: timedelta) -> str:
    minutes = max(0, int(round(duration.total_seconds() / 60)))
    return f"{minutes // 60}:{minutes % 60:02d}"


def row_of(stretch: tl.Stretch) -> Dict[str, Any]:
    offset = stretch.offset
    return {"day": stretch.day.isoformat(),
            "start": stretch.start.strftime("%H:%M") if stretch.start else "",
            "minutes": int(round(stretch.duration.total_seconds() / 60)),
            "kind": stretch.kind, "note": stretch.note,
            "offset": int(offset.total_seconds() // 60) if offset is not None else None}


def stretch_of(row: Dict[str, Any], kind: Optional[str] = None) -> Optional[tl.Stretch]:
    """A row from the screen as a stretch, or None when it is no sensible one."""
    try:
        day = date.fromisoformat(str(row.get("day")))
        start_text = str(row.get("start") or "")
        start = None
        if start_text:
            match = _START.match(start_text)
            if not match:
                return None
            start = time(int(match.group(1)), int(match.group(2)))
        minutes = row.get("minutes")
        if type(minutes) is not int or not 0 < minutes <= MAX_MINUTES:
            return None
        offset = row.get("offset")
        kind = kind or str(row.get("kind") or "added")
        if kind not in tl.KINDS:
            return None
        return tl.Stretch(day=day, start=start, duration=timedelta(minutes=minutes), kind=kind,
                          note=str(row.get("note") or "").replace("\n", " ")[:200],
                          offset=timedelta(minutes=offset) if type(offset) is int else None)
    except (TypeError, ValueError):
        return None



def _seconds_of(short: Any) -> int:
    """"2:15" (or "0:15 · gestoppt", the clock's short text) as seconds; 0 without."""
    match = re.match(r"^\s*(\d+):([0-5]\d)", str(short or ""))
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 if match else 0


def system_face(home: Optional[Path] = None, login: Optional[str] = None,
                accounts: Path = Path("/var/lib/AccountsService/icons")) -> Optional[Path]:
    """The person's picture as the system keeps it (AccountsService, which the login screen
    and the desktop show), else ~/.face; None without one."""
    home = Path(home) if home is not None else Path.home()
    try:
        login = login or getpass.getuser()
    except Exception:
        login = ""
    for candidate in ([accounts / login] if login else []) + [home / ".face", home / ".face.icon"]:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None

class TimeModel:
    def __init__(self, *, active: Optional[Path] = None, widget: Optional[Path] = None,
                 today: Callable[[], date] = date.today, language: str = "de",
                 ledger: Optional[Path] = None, face: Optional[Callable[[], Optional[Path]]] = None) -> None:
        self._active = Path(active) if active is not None else active_file()
        # The clock's ledger: the projects worked on last, to choose from (Z7).
        self._ledger = Path(ledger) if ledger is not None else default_store().with_name("ledger.json")
        self._widget = Path(widget) if widget is not None else cw.folder()
        self._today = today
        self._language = language
        self._face = face if face is not None else system_face

    def today(self) -> date:
        return self._today()

    # --- now ------------------------------------------------------------------------------------

    def active_project(self) -> Optional[Path]:
        project, _person = read_active(self._active)
        return project

    def projects(self) -> List[Dict[str, str]]:
        """The projects to choose from: the active one first, then those worked on last (the
        clock's ledger) that are projects still. Choosing one moves nothing: not the clock, not
        the Headline (Designdocument Time.md, 4.4 and 5)."""
        found: List[Path] = []
        active = self.active_project()
        if active is not None:
            found.append(Path(active))
        for recent in cw.Ledger(self._ledger).recent():
            if recent not in found and is_project(recent):
                found.append(recent)
        return [{"name": path.name, "path": str(path)} for path in found]

    def _person(self, project: Path) -> str:
        return person_for(project)

    def now(self) -> Dict[str, Any]:
        project = self.active_project()
        view = self._clock_view()
        counter = (view or {}).get("counter")
        since = counter.get("since") if isinstance(counter, dict) else None
        face = self._face()
        return {"project": str(project) if project else "", "projectName": project.name if project else "",
                "clockRuns": view is not None, "text": (view or {}).get("text", ""),
                "state": (view or {}).get("state", "calm"), "clock": str((view or {}).get("clock") or ""),
                # The dial (2026-11-18): today's time as the view says it, and while it counts
                # where it would be naught - the screen counts on to the second from there.
                "todaySeconds": _seconds_of((view or {}).get("short")),
                "since": float(since) if type(since) in (int, float) else 0,
                # Who is counted: the person of the project, with the system's picture.
                "person": self._person(project) if project else "",
                "picture": face.as_uri() if face is not None else ""}

    def _clock_view(self) -> Optional[Dict[str, Any]]:
        path = self._widget / "view.json"
        try:
            if clock_time.time() - path.stat().st_mtime > STALE:
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _tell(self, command: str) -> bool:
        folder = self._widget / "commands"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"{clock_time.time_ns()}-{command}").write_text("", encoding="utf-8")
        except OSError:
            return False
        return True

    def start(self) -> bool:
        return self._tell("start")

    def stop(self) -> bool:
        return self._tell("stop")

    # --- entries --------------------------------------------------------------------------------

    def _file(self, project: Optional[str]) -> Optional[Path]:
        folder = Path(project) if project else self.active_project()
        if folder is None:
            return None
        return tl.time_file(folder, self._person(folder))

    def entries(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """One's own rows of a project (the active one by default), newest first."""
        path = self._file(project)
        if path is None or not allowed_at(path, "read"):
            return []
        stretches = tl.read(path).stretches
        # Newest first: by day, then as written (a row added later, without a beginning, on top).
        ordered = sorted(enumerate(stretches), key=lambda pair: (pair[1].day, pair[0]), reverse=True)
        return [row_of(stretch) for _index, stretch in ordered]

    def unreadable(self, project: Optional[str] = None) -> int:
        """How many rows of one's own file could not be read (left in the file as they are; Z11)."""
        path = self._file(project)
        if path is None or not allowed_at(path, "read"):
            return 0
        return len(tl.read(path).problems)

    def add(self, row: Dict[str, Any], project: Optional[str] = None) -> bool:
        """What was done away from the computer ("Baumarkt, 1½ h")."""
        stretch = stretch_of(row, kind="added")
        path = self._file(project)
        if stretch is None or path is None:
            return False
        if not is_project(path.parents[2]):
            return False  # gone (renamed, in the trash): no ghost folder at the old place
        if not allowed_at(path, "write"):
            return False  # the person's rights, as Scope and the clock's drive ask them (A14)
        tl.add_to_file(path, self._person(path.parents[2]), stretch, language=self._language)
        return True

    def change(self, old: Dict[str, Any], new: Dict[str, Any], project: Optional[str] = None) -> bool:
        before = stretch_of(old)
        # "corrected" is an auto row changed by hand; an added or manual one stays what it is (Z10).
        kind = "corrected" if before is not None and before.kind == "auto" else (before.kind if before else None)
        after = stretch_of(new, kind=kind)
        path = self._file(project)
        return bool(before and after and path) and allowed_at(path, "write") and tl.change(path, before, after)

    def remove(self, row: Dict[str, Any], project: Optional[str] = None) -> bool:
        stretch = stretch_of(row)
        path = self._file(project)
        return bool(stretch and path) and allowed_at(path, "write") and tl.remove(path, stretch)

    # --- overview -------------------------------------------------------------------------------

    def _since(self, period: str) -> Optional[date]:
        today = self._today()
        return {"today": today, "week": today - timedelta(days=today.weekday()),
                "month": today.replace(day=1)}.get(period)

    def overview(self, project: Optional[str] = None, *, period: str = "month",
                 person: Optional[str] = None) -> Dict[str, Any]:
        """A project with its children: sums per project and per person, rounded as set."""
        folder = Path(project) if project else self.active_project()
        if folder is None:
            return {"total": "0:00", "byProject": [], "byPerson": [], "conflicts": 0, "unreadable": 0}
        # Only what the person may read (A7): a colleague's file, a hidden subproject is not
        # summed up where Scope does not show it - checked by the file's own ACLs.
        readable = [e for e in tl.collect(folder, children=True)
                    if e.source is None or allowed_at(e.source, "read")]
        # A cloud's conflict copy holds nearly all rows of the original: not counted, only told
        # (in the whole project, its children too) until there is a way to merge (Z2).
        copies = {e.source for e in readable if e.conflict}
        readable = [e for e in readable if not e.conflict]
        entries = tl.only(readable, person=person or None, since=self._since(period))
        rounding = rounding_from_settings(Settings())
        by_project = tl.sums(entries, by="project", rounding=rounding)
        by_person = tl.sums(entries, by="person", rounding=rounding)
        return {
            "total": _hours(tl.total(entries, rounding)),
            "byProject": [{"name": Path(p).name, "path": str(p), "time": _hours(t)} for p, t in by_project.items()],
            "byPerson": [{"name": p, "time": _hours(t)} for p, t in by_person.items()],
            "conflicts": len(copies),
            # Rows that could not be read are not summed: told, not dropped silently (Z11).
            "unreadable": sum(len(tl.read(path).problems) for path in tl.time_files(folder)
                              if allowed_at(path, "read")),
        }
