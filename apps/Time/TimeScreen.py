#!/usr/bin/env python3
"""The time screen (core/Dokumentation/Designdocument Time.md, 5): the time tracking's own
window, opened from its widget in the Headline. What it shows is worked out in apps/Time/model.py;
it works with the person's own rights, not the clock's.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
# Started as a script its own folder comes first on sys.path; its files (model.py) would stand
# for modules of the same name, not the package apps.Time (as for the Headline).
_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QObject, QTimer, QTranslator, QUrl, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from core.color_schemes import load_scheme  # noqa: E402
from core.settings import SETTINGS, Settings  # noqa: E402
from apps.Scope.window_icon import seiton_icon  # noqa: E402
from apps.Time import instance  # noqa: E402
from apps.Time.model import TimeModel  # noqa: E402

REFRESH_MS = 5000  # how often Now is read anew (the clock writes every 15 s)
# After Start or Stop: read soon and often for a while - the clock obeys within a second and
# writes its view at once; at 5 s the screen lagged up to six seconds (2026-11-18).
SOON_MS = 250
SOON_FOR_MS = 3000
_DURATION = re.compile(r"^\s*(\d{1,2}):([0-5]\d)\s*$|^\s*(\d{1,4})\s*$")
# What the time screen sets (its settings live here, Designdocument Headline.md, 3a).
TIME_SETTINGS = [key for key in SETTINGS if key.startswith("Time/")]


def parse_minutes(text: str) -> int:
    """"1:30" or "90" as minutes; -1 when it is neither."""
    match = _DURATION.match(str(text or ""))
    if not match:
        return -1
    if match.group(3) is not None:
        return int(match.group(3))
    return int(match.group(1)) * 60 + int(match.group(2))


class TimeBackend(QObject):
    changed = Signal()

    def __init__(self, model: TimeModel) -> None:
        super().__init__()
        self._model = model
        self._timer = QTimer(self)
        self._timer.setInterval(REFRESH_MS)
        self._timer.timeout.connect(self.changed.emit)
        self._soon = QTimer(self)
        self._soon.setInterval(SOON_MS)
        self._soon.timeout.connect(self._read_soon)
        self._soon_left = 0

    def start_refreshing(self) -> None:
        self._timer.start()

    @Slot(result="QVariantMap")
    def now(self) -> dict:
        return self._model.now()

    @Slot(result=bool)
    def start(self) -> bool:
        return self._done(self._model.start())

    @Slot(result=bool)
    def stop(self) -> bool:
        return self._done(self._model.stop())

    @Slot(result=bool)
    def startClock(self) -> bool:
        """Start the clock itself (its launcher, written by the installer)."""
        launcher = shutil.which("seiton-clock") or str(Path.home() / ".local" / "bin" / "seiton-clock")
        try:
            subprocess.Popen([launcher], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            return False

    @Slot(str, result="QVariantList")
    def entries(self, project: str) -> list:
        return self._model.entries(project or None)

    @Slot(result="QVariantList")
    def projects(self) -> list:
        return self._model.projects()

    @Slot(str, result=int)
    def unreadable(self, project: str) -> int:
        return self._model.unreadable(project or None)

    @Slot("QVariantMap", str, result=bool)
    def add(self, row, project: str) -> bool:
        return self._done(self._model.add(dict(row), project or None))

    @Slot("QVariantMap", "QVariantMap", str, result=bool)
    def change(self, old, new, project: str) -> bool:
        return self._done(self._model.change(dict(old), dict(new), project or None))

    @Slot("QVariantMap", str, result=bool)
    def remove(self, row, project: str) -> bool:
        return self._done(self._model.remove(dict(row), project or None))

    @Slot(str, str, str, result="QVariantMap")
    def overview(self, project: str, period: str, person: str) -> dict:
        return self._model.overview(project or None, period=period, person=person or None)

    @Slot(str, result=int)
    def parseMinutes(self, text: str) -> int:
        return parse_minutes(text)

    @Slot(result=str)
    def today(self) -> str:
        return self._model.today().isoformat()

    @Slot(str, result="QVariant")
    def setting(self, key: str):
        return Settings().get(key) if key in TIME_SETTINGS else None

    @Slot(str, "QVariant", result=bool)
    def setSetting(self, key: str, value) -> bool:
        return key in TIME_SETTINGS and Settings().set(key, value)

    @Slot(result="QVariantMap")
    def colorScheme(self) -> dict:
        return load_scheme("dark" if Settings().get("General/darkTheme") else "light")

    def _done(self, ok: bool) -> bool:
        if ok:
            self.changed.emit()
            self._soon_left = SOON_FOR_MS // SOON_MS
            self._soon.start()
        return ok

    def _read_soon(self) -> None:
        self._soon_left -= 1
        if self._soon_left <= 0:
            self._soon.stop()
        self.changed.emit()


def load_time_screen(model: TimeModel, app: QGuiApplication) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    backend = TimeBackend(model)
    engine.rootContext().setContextProperty("timeScreen", backend)
    engine._backend = backend
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name("main.qml").resolve())))
    return engine


def install_translator(app: QGuiApplication, code: str) -> Optional[QTranslator]:
    if code == "en":
        return None
    translator = QTranslator(app)
    if not translator.load(str(Path(__file__).with_name("i18n") / f"time_{code}.qm")):
        return None
    app.installTranslator(translator)
    return translator


def main() -> int:
    # One time screen per user (2026-11-18: two could be opened): a later start brings the one
    # open to the front and ends.
    name = instance.server_name()
    if instance.hand_over(name):
        return 0
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SEITON Time")
    app.setWindowIcon(seiton_icon("time.svg"))  # its own: a stopwatch, not SEITON's box
    server = instance.InstanceServer(name)
    if not server.listen():
        instance.hand_over(name)  # another came up meanwhile
        return 0
    language = str(Settings().get("General/language"))
    install_translator(app, language)
    engine = load_time_screen(TimeModel(language=language), app)
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    server.showRequested.connect(lambda: _to_front(window))
    engine._backend.start_refreshing()
    code = app.exec()
    server.close()
    return code


def _to_front(window) -> None:
    """Asked by a later start: the window open, in front, minimised or not."""
    window.showNormal()
    window.raise_()
    window.requestActivate()


if __name__ == "__main__":
    raise SystemExit(main())
