"""The clock as the Headline's first widget (Scope/Designdocument Headline.md, 3a).

The time tracking is a program of its own; it puts itself into the Headline by the widget
protocol (Headline/widgets.py): it writes `view.json` into a folder of its own in the runtime
folder - "Küche · 2:15", calm when it stands, its question when it asks, the projects worked on
last - and takes the command files the Headline drops into `commands/` there.

What it shows it knows from a small ledger of its own (in the clock's state folder, writable in
its sandbox): what it counted per project and day, and when it was in which project last. It
reads no time files for that.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core import time_log as tl
from core.brand import config_dir, file_name

KEEP_PROJECTS = 10  # the projects worked on last that the ledger remembers
KEEP_DAYS = 31
SHOWN_ITEMS = 10
SHOWS = ("total", "week", "today")  # the time beside the projects worked on last (Time/recentShows)
COMMANDS = ("start", "stop", "yes", "no")

_WORDS = {
    "de": {"none": "Kein Projekt", "ask": "Arbeitest du noch an {project}?", "yes": "Ja", "no": "Nein",
           "name": "Zeit"},
    "en": {"none": "No project", "ask": "Still working on {project}?", "yes": "Yes", "no": "No",
           "name": "Time"},
}


def folder() -> Path:
    """The widget's folder: the runtime folder (gone at logout), else SEITON's settings folder."""
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    return (Path(runtime) if runtime else config_dir()) / file_name("clock")


def _words(language: str) -> Dict[str, str]:
    return _WORDS.get(language, _WORDS["en"])


def _hours(duration: timedelta) -> str:
    minutes = max(0, int(duration.total_seconds() // 60))
    return f"{minutes // 60}:{minutes % 60:02d}"


class Ledger:
    """What the clock counted, per project and day, and when it was in which project last."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"projects": {}}
        return data if isinstance(data, dict) and isinstance(data.get("projects"), dict) else {"projects": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.writing")
        temporary.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, self.path)

    def _entry(self, project: Path) -> Dict[str, Any]:
        entry = self._data["projects"].setdefault(str(project), {"last": "", "days": {}})
        entry.setdefault("days", {})
        return entry

    def _latest(self) -> str:
        """The newest day the ledger knows: what counts as today when old days are forgotten
        (a stretch added for an old day must not keep that day's company alive)."""
        days = [day for entry in self._data["projects"].values() for day in entry.get("days", {})]
        lasts = [str(entry.get("last") or "")[:10] for entry in self._data["projects"].values()]
        return max([d for d in days + lasts if d] or [""])

    def _forget(self, today: date) -> None:
        projects = self._data["projects"]
        latest = max(today.isoformat(), self._latest())
        oldest = (date.fromisoformat(latest) - timedelta(days=KEEP_DAYS)).isoformat()
        for entry in projects.values():
            entry["days"] = {day: minutes for day, minutes in entry.get("days", {}).items() if day >= oldest}
        for name in [p for p in projects if p not in {str(r) for r in self.recent()}]:
            del projects[name]

    def add(self, project: Path, day: date, duration: timedelta) -> None:
        days = self._entry(project)["days"]
        days[day.isoformat()] = days.get(day.isoformat(), 0) + duration.total_seconds() / 60
        if not self._entry(project)["last"]:
            self._entry(project)["last"] = datetime.combine(day, datetime.min.time()).isoformat()
        self._forget(day)
        self._save()

    def seen(self, project: Path, when: datetime, person: str = "") -> None:
        self._entry(project)["last"] = when.isoformat()
        if person:
            self._entry(project)["person"] = person
        self._forget(when.date())
        self._save()

    def on(self, project: Path, day: date) -> timedelta:
        entry = self._data["projects"].get(str(project)) or {}
        return timedelta(minutes=float((entry.get("days") or {}).get(day.isoformat(), 0)))

    def person(self, project: Path) -> str:
        return str((self._data["projects"].get(str(project)) or {}).get("person") or "")

    def recent(self) -> List[Path]:
        projects = self._data["projects"]
        ordered = sorted(projects, key=lambda p: str(projects[p].get("last") or ""), reverse=True)
        return [Path(p) for p in ordered[:KEEP_PROJECTS]]


def counting(writer: Callable, ledger: Ledger) -> Callable:
    """The clock's writer, also telling the ledger what it wrote."""
    def write(project: Path, person: str, stretch) -> Any:
        result = writer(project, person, stretch)
        ledger.add(Path(project), stretch.day, stretch.duration)
        return result
    return write


def spent_from(path_of: Callable[[Path, str], Path]) -> Callable[[Path, str, str, date], timedelta]:
    """The time a person spent on a project, from the time file at path_of(project, person) -
    the project's own file, or in the sandbox the one on the role's drive. shows: "total",
    "week" (since Monday) or "today"."""
    def spent(project: Path, person: str, shows: str, today: date) -> timedelta:
        if not person:
            return timedelta(0)
        try:
            stretches = tl.read(path_of(Path(project), person)).stretches
        except (OSError, ValueError):
            return timedelta(0)
        since = {"today": today, "week": today - timedelta(days=today.weekday())}.get(shows)
        return sum((s.duration for s in stretches if since is None or s.day >= since), timedelta(0))
    return spent


def render(clock, ledger: Ledger, now: datetime, *, language: str,
           spent: Optional[Callable[[Path, str, str, date], timedelta]] = None,
           shows: str = "total") -> Dict[str, Any]:
    """The widget's view (Headline/widgets.py) for the clock as it is now. Beside the projects
    worked on last the time `shows` from their time files (spent); without, what the ledger
    counted today."""
    words = _words(language)
    view: Dict[str, Any] = {}
    project = clock.project
    if project is None:
        view.update(text=words["none"], state="calm")
    else:
        running = clock.view(now)["running"] if clock.state in ("runs", "asks") else timedelta(0)
        today = ledger.on(Path(project), now.date()) + running
        state = {"runs": "active", "asks": "asking"}.get(clock.state, "calm")
        view.update(text=f"{Path(project).name} · {_hours(today)}", state=state)
        if clock.state == "asks":
            view["question"] = {"text": words["ask"].format(project=Path(project).name),
                                "answers": [{"id": "yes", "label": words["yes"]},
                                            {"id": "no", "label": words["no"]}]}
    items = []
    for recent in ledger.recent()[:SHOWN_ITEMS]:
        if spent is None:
            time_there = ledger.on(recent, now.date())
        else:
            person = ledger.person(recent) or (clock.person if project is not None and recent == Path(project) else "")
            time_there = spent(recent, person, shows, now.date())
        if project is not None and recent == Path(project) and clock.state in ("runs", "asks"):
            time_there += clock.view(now)["running"]  # not written yet
        items.append({"text": f"{recent.name} · {_hours(time_there)}", "path": str(recent)})
    view["items"] = items
    return view


def write_view(place: Path, view: Dict[str, Any]) -> None:
    place.mkdir(parents=True, exist_ok=True)
    temporary = place / ".view.json.writing"
    temporary.write_text(json.dumps(view, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, place / "view.json")


def take_commands(place: Path) -> List[str]:
    """The command files dropped since last time, oldest first; each is taken once. Anything but
    the clock's own commands is thrown away."""
    commands = Path(place) / "commands"
    try:
        files = sorted(commands.iterdir(), key=lambda p: p.name)
    except OSError:
        return []
    taken = []
    for path in files:
        stamp, _sep, command = path.name.partition("-")
        try:
            path.unlink()
        except OSError:
            continue
        if stamp.isdigit() and command in COMMANDS:
            taken.append(command)
    return taken


def obey(clock, command: str, now: datetime) -> None:
    if command == "start":
        clock.start(now)
    elif command == "stop":
        clock.stop(now)
    elif command in ("yes", "no"):
        clock.answer(command == "yes", now)


def registration(place: Path, open_command: List[str], language: str = "de") -> Dict[str, Any]:
    """The widget's file for the Headline (<config>/headline/widgets/clock.json)."""
    return {"name": _words(language)["name"], "folder": str(place), "open": list(open_command),
            "commands": ["start", "stop"], "staleAfter": 60}
