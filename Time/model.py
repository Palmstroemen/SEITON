"""The time screen (core/Dokumentation/Designdocument Time.md, 5): the time tracking's own
window, opened from its widget in the Headline (Scope/Designdocument Headline.md, 3a).

Now (the active project, the clock, Start/Stop), Entries (one's own rows of a project, newest
first: add, correct, take away), Overview (a project with its children, by period and person,
rounded as set). It works with the person's own rights - not the sandboxed clock - and talks to
the running clock as the Headline does: it reads the clock's view and drops commands.
No Qt here; its window only draws it.
"""

from __future__ import annotations

import json
import re
import time as clock_time
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core import clock_widget as cw
from core import time_log as tl
from core.clock import rounding_from_settings
from core.clock_sources import active_file, read_active
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


class TimeModel:
    def __init__(self, *, active: Optional[Path] = None, widget: Optional[Path] = None,
                 today: Callable[[], date] = date.today, language: str = "de") -> None:
        self._active = Path(active) if active is not None else active_file()
        self._widget = Path(widget) if widget is not None else cw.folder()
        self._today = today
        self._language = language

    def today(self) -> date:
        return self._today()

    # --- now ------------------------------------------------------------------------------------

    def active_project(self) -> Optional[Path]:
        project, _person = read_active(self._active)
        return project

    def _person(self, project: Path) -> str:
        return person_for(project)

    def now(self) -> Dict[str, Any]:
        project = self.active_project()
        view = self._clock_view()
        return {"project": str(project) if project else "", "projectName": project.name if project else "",
                "clockRuns": view is not None, "text": (view or {}).get("text", ""),
                "state": (view or {}).get("state", "calm")}

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
        if path is None:
            return []
        stretches = tl.read(path).stretches
        # Newest first: by day, then as written (a row added later, without a beginning, on top).
        ordered = sorted(enumerate(stretches), key=lambda pair: (pair[1].day, pair[0]), reverse=True)
        return [row_of(stretch) for _index, stretch in ordered]

    def add(self, row: Dict[str, Any], project: Optional[str] = None) -> bool:
        """What was done away from the computer ("Baumarkt, 1½ h")."""
        stretch = stretch_of(row, kind="added")
        path = self._file(project)
        if stretch is None or path is None:
            return False
        if not is_project(path.parents[2]):
            return False  # gone (renamed, in the trash): no ghost folder at the old place
        tl.add_to_file(path, self._person(path.parents[2]), stretch, language=self._language)
        return True

    def change(self, old: Dict[str, Any], new: Dict[str, Any], project: Optional[str] = None) -> bool:
        before, after = stretch_of(old), stretch_of(new, kind="corrected")
        path = self._file(project)
        return bool(before and after and path) and tl.change(path, before, after)

    def remove(self, row: Dict[str, Any], project: Optional[str] = None) -> bool:
        stretch = stretch_of(row)
        path = self._file(project)
        return bool(stretch and path) and tl.remove(path, stretch)

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
            return {"total": "0:00", "byProject": [], "byPerson": [], "conflicts": 0}
        entries = tl.only(tl.collect(folder, children=True), person=person or None,
                          since=self._since(period))
        rounding = rounding_from_settings(Settings())
        by_project = tl.sums(entries, by="project", rounding=rounding)
        by_person = tl.sums(entries, by="person", rounding=rounding)
        return {
            "total": _hours(tl.total(entries, rounding)),
            "byProject": [{"name": Path(p).name, "path": str(p), "time": _hours(t)} for p, t in by_project.items()],
            "byPerson": [{"name": p, "time": _hours(t)} for p, t in by_person.items()],
            "conflicts": len(tl.conflicts(folder)),
        }
