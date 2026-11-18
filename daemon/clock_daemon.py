# clock_daemon.py - seiton-clock: the clock of the time tracking, running
#
# See "Designdocument Time.md", sections 4 and 7. Every 15 seconds it reads the active project
# (written by the top bar), asks the idle time and whether a video runs, and tells the clock
# (core/clock.py). Started by cli/seiton_clock.py, normally in its sandbox: then it writes the
# time files through the drive of its role (--drive), and sees nothing else of the projects.

from __future__ import annotations

import argparse
import functools
import logging
import signal
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import clock_widget as cw  # noqa: E402
from core.clock import Clock, ClockSettings, default_store, file_writer, local_now  # noqa: E402
from core.clock_sources import IdleTime, Inhibited, active_file, read_active  # noqa: E402

logger = logging.getLogger(__name__)
TICK = 15.0  # seconds
LISTEN = 1.0  # how often it looks for the Headline's commands


class Widget:
    """The clock as the Headline's widget (core/clock_widget.py): where its view goes, its ledger."""

    def __init__(self, folder: Path, ledger: "cw.Ledger", language: str = "de",
                 spent=None, shows: str = "total") -> None:
        self.folder = Path(folder)
        self.ledger = ledger
        self.language = language
        self.spent = spent  # the time in a project from its time file (cw.spent_from)
        self.shows = shows  # beside the projects worked on last: total, week, today


class ClockService:
    """One step of the running clock: the active project, then the idle time; as a widget its
    view after each step, and the Headline's commands in between."""

    def __init__(self, clock: Clock, *, active: Path, idle: Callable[[], Optional[timedelta]],
                 inhibited: Callable[[], bool], now: Callable[[], datetime] = local_now,
                 widget: Optional[Widget] = None, projects_root: Optional[Path] = None) -> None:
        self.clock = clock
        self.active = active
        self.idle = idle
        self.inhibited = inhibited
        self.now = now
        self.widget = widget
        self.projects_root = Path(projects_root) if projects_root is not None else None
        self._seen = (None, "")
        self._outside_said: set = set()
        self._idle_unknown_said = False

    def show(self) -> None:
        if self.widget is not None:
            cw.write_view(self.widget.folder, cw.render(self.clock, self.widget.ledger, self.now(),
                                                        language=self.widget.language,
                                                        spent=self.widget.spent, shows=self.widget.shows))

    def listen(self) -> bool:
        """The Headline's commands (start, stop, yes, no); True when there were any."""
        if self.widget is None:
            return False
        commands = cw.take_commands(self.widget.folder)
        for command in commands:
            cw.obey(self.clock, command, self.now())
        if commands:
            self.show()
        return bool(commands)

    def _inside(self, project: Optional[Path]) -> Optional[Path]:
        """The active project, if the clock can write it: below its projects root. One in another
        root (A11) counts as no project - better not counting than counting time it must drop."""
        if project is None or self.projects_root is None:
            return project
        if self.projects_root in Path(project).parents:
            return project
        if project not in self._outside_said:
            self._outside_said.add(project)
            logger.warning("clock.outside project=%s root=%s: not counted", project, self.projects_root)
        return None

    def step(self) -> None:
        now = self.now()
        self.clock.wake(now)  # first: a switch right after waking must not count the sleep
        project, person = read_active(self.active)
        project = self._inside(project)
        if (project, person) != self._seen:
            self._seen = (project, person)
            self.clock.set_project(project, person, now)
            if project is not None and self.widget is not None:
                self.widget.ledger.seen(project, now, person)
        idle = self.idle()
        if idle is None:
            # No source answers: the clock cannot see a pause, only a switch of project.
            if not self._idle_unknown_said:
                logger.warning("clock.idle unknown: pauses are not seen")
                self._idle_unknown_said = True
            idle = timedelta(0)
        self.clock.tick(now, idle, inhibited=self.inhibited() if self.clock.state in ("runs", "asks") else False)
        self.show()


def drive_writers(drive: Path, projects_root: Path, *, language: str):
    """Writer and reader of the time files through the role's drive. Written without a helper
    file: the drive lets the person write their own file ({Self}.md), nothing beside it."""
    from core.role_drive import drive_path, drive_writer
    writer = drive_writer(drive, projects_root, language=language,
                          add=functools.partial(cw.tl.add_to_file, atomic=False))
    spent = cw.spent_from(lambda project, person: drive_path(drive, projects_root, project, person))
    return writer, spent


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="The clock of the time tracking.")
    parser.add_argument("--drive", type=Path, help="the role's /0_Admin/Zeitaufwand (in the sandbox)")
    parser.add_argument("--projects-root", type=Path, help="the projects root the drive shows")
    parser.add_argument("--store", type=Path, default=None)
    parser.add_argument("--active", type=Path, default=None)
    parser.add_argument("--widget", type=Path, default=None, help="the folder of its widget in the Headline")
    parser.add_argument("--recent", default="total", choices=list(cw.SHOWS),
                        help="the time beside the projects worked on last")
    parser.add_argument("--language", default="de", choices=["de", "en"])
    parser.add_argument("--pause", type=float, default=5.0, help="the pause limit in minutes")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--no-dead-man", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    if args.drive is not None:
        if args.projects_root is None:
            parser.error("--drive needs --projects-root")
        writer, spent = drive_writers(args.drive, args.projects_root, language=args.language)
    else:
        writer = file_writer(language=args.language)
        spent = cw.spent_from(cw.tl.time_file)
    settings = ClockSettings(pause=timedelta(minutes=args.pause), auto_resume=not args.no_resume,
                             dead_man=not args.no_dead_man)
    store = args.store or default_store()
    ledger = cw.Ledger(store.with_name("ledger.json"))
    clock = Clock(writer=cw.counting(writer, ledger), store=store, settings=settings)
    clock.recover(local_now())
    widget = Widget(folder=args.widget or cw.folder(), ledger=ledger, language=args.language,
                    spent=spent, shows=args.recent)
    service = ClockService(clock, active=args.active or active_file(), idle=IdleTime(), inhibited=Inhibited(),
                           widget=widget, projects_root=args.projects_root)

    ending = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, lambda *_: ending.set())
    logger.info("clock.start store=%s active=%s drive=%s", clock.store, service.active, args.drive)
    beats = int(TICK / LISTEN)
    beat = 0
    while not ending.is_set():
        try:
            if beat == 0:
                service.step()
            else:
                service.listen()
        except Exception:  # one bad step must not end the clock
            logger.exception("clock.step failed")
        beat = (beat + 1) % beats
        ending.wait(LISTEN)
    clock.pause_now()
    logger.info("clock.end")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
