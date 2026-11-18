# clock.py - the clock of the time tracking: when a stretch begins and ends
#
# See "Designdocument Time.md", section 4. The clock counts while one works in the active
# project. It is told the time, the idle time (how long no input came) and whether a program
# keeps the screensaver away (a video); it does not watch the system itself, so it runs the
# same in tests and in seiton-clock. A closed stretch goes to the writer, one row per day.
#
# States:
#   stands   no project
#   runs     counting
#   asks     the pause limit passed while a video runs: "Still working on ...?"
#   paused   the pause limit passed; the next input resumes (or a click, without auto resume)
#   stopped  stopped by hand; only start() counts again
#
# The running stretch lives in a small file on the computer (store), written at most once a
# minute, so a crash loses at most a minute and the project's file only changes when a
# stretch closes. Stretches a project cannot take now (a cloud folder away) are kept there too
# and written later.

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core import time_log as tl
from core.brand import CONFIG_DIR
from core.perspective_session import is_project

logger = logging.getLogger(__name__)

Writer = Callable[[Path, str, tl.Stretch], Any]
SAVE_EVERY = timedelta(minutes=1)
INPUT_WOBBLE = timedelta(seconds=1)


@dataclass(frozen=True)
class ClockSettings:
    pause: timedelta = timedelta(minutes=5)  # the pause limit
    auto_resume: bool = True
    dead_man: bool = True
    answer: timedelta = timedelta(minutes=2)  # how long the question waits for "Yes"
    shortest: timedelta = timedelta(minutes=1)  # a shorter stretch is a glance, not time

    @classmethod
    def from_settings(cls, settings) -> "ClockSettings":
        return cls(pause=timedelta(minutes=float(settings.get("Time/pauseMinutes"))),
                   auto_resume=bool(settings.get("Time/autoResume")),
                   dead_man=bool(settings.get("Time/deadMan")))


def rounding_from_settings(settings) -> tl.Rounding:
    return tl.Rounding(step=int(settings.get("Time/roundStep")), mode=settings.get("Time/roundMode"),
                       per=settings.get("Time/roundPer"))


def file_writer(*, language: str) -> Writer:
    """The writer of seiton-clock: the person's file in the project (core/time_log.py). A
    project that is gone (renamed, in the trash) is not made anew as a ghost folder: the stretch
    waits (FileNotFoundError) until someone looks after it."""
    def write(project: Path, person: str, stretch: tl.Stretch) -> None:
        if not is_project(Path(project)):
            raise FileNotFoundError(f"{project}: no project there (renamed or gone?)")
        tl.add(project, person, stretch, language=language)
    return write


def local_now() -> datetime:
    """Now with its zone: differences are real durations, also in the night the clocks change."""
    return datetime.now().astimezone()


def _like(moment: datetime, now: datetime) -> datetime:
    """A moment read from the store, comparable with now (stores of before had no zone)."""
    if moment.tzinfo is None and now.tzinfo is not None:
        return moment.astimezone()
    if moment.tzinfo is not None and now.tzinfo is None:
        return moment.astimezone().replace(tzinfo=None)
    return moment


def default_store() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / CONFIG_DIR / "clock.json"


@dataclass
class _Running:
    begin: datetime
    activity: datetime  # the last input (or confirmation) that counts
    kind: str


@dataclass
class Clock:
    writer: Writer
    store: Optional[Path] = None
    settings: ClockSettings = field(default_factory=ClockSettings)

    def __post_init__(self) -> None:
        self.state = "stands"
        self.project: Optional[Path] = None
        self.person = ""
        self.pending: List[Dict[str, Any]] = []
        self._running: Optional[_Running] = None
        self._asked: Optional[datetime] = None
        self._paused_at: Optional[datetime] = None  # inputs after this resume
        self._saved_activity: Optional[datetime] = None
        self._last_tick: Optional[datetime] = None  # a long gap since: the computer slept
        self._told_later: set = set()  # stretches already reported as waiting

    # --- what one does ---------------------------------------------------------------------

    def set_project(self, project: Optional[Path], person: str, now: datetime) -> None:
        """The active project changed (or is gone: None). Switching is an input."""
        if self._running is not None:
            self._close(now)
        self.project = Path(project) if project is not None else None
        self.person = person
        if self.project is None:
            if self.state != "stopped":
                self.state = "stands"
        elif self.state != "stopped":
            self._begin(now, "auto")
        self._save(force=True)

    def start(self, now: datetime) -> None:
        if self.project is None or self.state in ("runs", "asks"):
            return
        self._begin(now, "manual")
        self._save(force=True)

    def stop(self, now: datetime) -> None:
        if self._running is not None:
            self._close(now)
        if self.project is not None:
            self.state = "stopped"
        self._save(force=True)

    def answer(self, yes: bool, now: datetime) -> None:
        """The answer to "Still working on ...?"."""
        if self.state != "asks" or self._running is None:
            return
        if yes:
            self._running.activity = now
            self._asked = None
            self.state = "runs"
        else:
            self._pause(self._asked or now)
            self._paused_at = now  # the click on "No" is no input that resumes
        self._save(force=True)

    # --- what the system tells -------------------------------------------------------------

    def tick(self, now: datetime, idle: timedelta, inhibited: bool = False) -> None:
        """Every few seconds: the idle time, and whether a video keeps the screensaver away."""
        self._retry()
        state_before = self.state
        last_input = now - idle
        self.wake(now)
        if self.state in ("runs", "asks") and self._running is not None:
            running = self._running
            if last_input > running.activity:
                running.activity = last_input
            if self.state == "asks":
                if self._asked is not None and running.activity > self._asked:
                    self.state, self._asked = "runs", None  # an input is a yes
                elif self._asked is not None and now - self._asked > self.settings.answer:
                    self._pause(self._asked)
            elif now - running.activity > self.settings.pause:
                if inhibited and self.settings.dead_man:
                    self.state, self._asked = "asks", now
                else:
                    self._pause(running.activity)
        elif self.state == "paused" and self.project is not None and self.settings.auto_resume:
            # Only an input clearly after the pause resumes: the estimate of the last input
            # wobbles by the time it takes to ask the idle time (review 2026-11-18, Z12).
            if self._paused_at is not None and last_input - self._paused_at > INPUT_WOBBLE:
                self._begin(last_input, "auto")
        self._save(force=self.state != state_before)

    def pause_now(self) -> None:
        """The clock ends (logout, shutdown): the running stretch closes at its last activity."""
        if self._running is not None:
            self._pause(self._running.activity)
        self._save(force=True)

    # --- what the top bar shows --------------------------------------------------------------

    def view(self, now: datetime) -> Dict[str, Any]:
        running = now - self._running.begin if self._running is not None else timedelta(0)
        return {"state": self.state, "project": self.project, "running": running}

    # --- after a crash -------------------------------------------------------------------------

    def recover(self, now: datetime) -> None:
        """Read the store of a clock that did not close: its stretch ends at its last activity."""
        data = self._load()
        if not data:
            return
        self.pending = list(data.get("pending", []))
        project = data.get("project")
        self.project = Path(project) if project else None
        self.person = data.get("person", "")
        state = data.get("state", "stands")
        running = data.get("running")
        if running:
            self._running = _Running(begin=_like(datetime.fromisoformat(running["begin"]), now),
                                     activity=_like(datetime.fromisoformat(running["activity"]), now),
                                     kind=running["kind"])
            self._pause(self._running.activity)
        elif state == "stopped" and self.project is not None:
            self.state = "stopped"
        elif self.project is not None:
            self.state = "paused"
            self._paused_at = now
        self._retry()
        self._save(force=True)

    # --- inside --------------------------------------------------------------------------------

    def wake(self, now: datetime) -> None:
        """Called first on each step (tick does it too). Did the process stand still (suspend,
        lid closed) since the last one, the idle time does not count the sleep, and waking is a
        fresh input: the stretch ends where it was left."""
        slept = self._last_tick is not None and now - self._last_tick > self.settings.pause
        self._last_tick = now
        if slept and self.state in ("runs", "asks") and self._running is not None:
            asked = self._asked if self.state == "asks" else None
            self._pause(asked or self._running.activity)

    def _begin(self, now: datetime, kind: str) -> None:
        self._running = _Running(begin=now, activity=now, kind=kind)
        self._asked = None
        self.state = "runs"

    def _pause(self, end: datetime) -> None:
        self._close(end)
        self.state = "paused"
        self._paused_at = end

    def _close(self, end: datetime) -> None:
        running, self._running, self._asked = self._running, None, None
        if running is None or self.project is None:
            return
        duration = end - running.begin
        if duration < self.settings.shortest:
            return
        for stretch in tl.split_days(running.begin, duration, kind=running.kind):
            self.pending.append(_to_json(self.project, self.person, stretch))
        self._retry()

    def _retry(self) -> None:
        left = []
        for item in self.pending:
            try:
                project, person, stretch = _from_json(item)
                self.writer(project, person, stretch)
            except OSError as error:
                key = json.dumps(item, sort_keys=True)
                if key not in self._told_later:  # told once, not every 15 seconds
                    self._told_later.add(key)
                    logger.info("clock.write later project=%s error=%s", item.get("project"), error)
                left.append(item)
            except (ValueError, KeyError, TypeError) as error:
                # never writable (outside the projects, a broken entry): waiting would not help
                logger.warning("clock.write dropped project=%s error=%s", item.get("project"), error)
        self._told_later &= {json.dumps(item, sort_keys=True) for item in left}
        if len(left) != len(self.pending):
            self.pending = left
            self._save(force=True)

    def _save(self, force: bool = False) -> None:
        if self.store is None:
            return
        activity = self._running.activity if self._running is not None else None
        if not force:
            if activity is None:
                return
            if self._saved_activity is not None and activity - self._saved_activity < SAVE_EVERY:
                return
        data = {"state": self.state, "project": str(self.project) if self.project else None,
                "person": self.person, "pending": self.pending,
                "running": None if self._running is None else {
                    "begin": self._running.begin.isoformat(),
                    "activity": self._running.activity.isoformat(), "kind": self._running.kind}}
        self.store.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.store.with_name(f".{self.store.name}.writing")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporary, self.store)
        self._saved_activity = activity

    def _load(self) -> Optional[Dict[str, Any]]:
        if self.store is None:
            return None
        try:
            return json.loads(self.store.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None


def _to_json(project: Path, person: str, stretch: tl.Stretch) -> Dict[str, Any]:
    return {"project": str(project), "person": person, "day": stretch.day.isoformat(),
            "start": stretch.start.isoformat() if stretch.start else None,
            "seconds": stretch.duration.total_seconds(), "kind": stretch.kind, "note": stretch.note}


def _from_json(item: Dict[str, Any]):
    stretch = tl.Stretch(day=date.fromisoformat(item["day"]),
                         start=time.fromisoformat(item["start"]) if item.get("start") else None,
                         duration=timedelta(seconds=item["seconds"]), kind=item["kind"],
                         note=item.get("note", ""))
    return Path(item["project"]), item["person"], stretch
