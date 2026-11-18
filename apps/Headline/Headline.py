#!/usr/bin/env python3
"""The Headline: SEITON at the screen's edge (apps/Scope/Designdocument Headline.md).

A program of its own and SEITON's master, always there (decided 2026-11-18); Scope is only a
first file browser. It shares where one is with Scope and SunTree through the session of the
lens. What it shows is worked out in apps/Headline/model.py, where its popups go in
apps/Headline/popup_place.py. Built: the line at the top edge (a dock with a strut, or hiding itself),
the panel from the taskbar, the cascade to climb, the standard folders taking drops, the
widgets (the clock first; apps/Headline/widgets.py), the active project for the clock, its tools and
its own settings (SettingsWindow.qml). One Headline per user (apps/Headline/instance.py).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
# Started as a script (python3 apps/Headline/Headline.py) its own folder comes first on sys.path:
# its files (model.py, instance.py, ...) would stand for modules of the same name. Off with it, and
# the repo root first, so "from apps.Headline.model import ..." means the package.
_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]
sys.path.insert(0, str(REPO_ROOT))

if __name__ == "__main__":
    # A later start (the applet, the launcher) hands over to the Headline running before it
    # loads Qt and Scope - else the panel came 1.5 s late (review 2026-11-18, H5).
    from apps.Headline import instance as _instance

    _place, _request = _instance.parse_start(sys.argv[1:])
    if _instance.hand_over(_instance.server_name(), _request or {"panel": None}):
        raise SystemExit(0)

from PySide6.QtCore import QObject, QPoint, QRect, QTimer, QTranslator, QUrl, Signal, Slot  # noqa: E402
from PySide6.QtGui import QCursor, QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from core.brand import getenv  # noqa: E402
from core.clock_sources import active_file, write_active  # noqa: E402
from core.color_schemes import load_scheme  # noqa: E402
from core.scope_api import ScopeApi, start_place  # noqa: E402  (start_place: shared with SunTree, Scope)
from core.settings import Settings  # noqa: E402
from daemon.lens_link import LensLink  # noqa: E402
from apps.Headline.model import HeadlineModel  # noqa: E402
from apps.Headline import instance, popup_place, widgets, x11_dock  # noqa: E402
from apps.Scope.Scope import ThemeIconProvider  # noqa: E402
from apps.Scope.window_icon import seiton_icon  # noqa: E402

FOLLOW_MS = 1000  # how often the Headline looks where Scope or SunTree went


def _rect(value) -> tuple:
    return (int(value["x"]), int(value["y"]), int(value["width"]), int(value["height"]))


class HeadlineBackend(QObject):
    changed = Signal()
    dockChanged = Signal()
    widgetsChanged = Signal()
    themeChanged = Signal()
    setupRequested = Signal()  # its own settings window (SettingsWindow.qml)
    # "Open the panel": at an anchor {x, y, width, height} (the applet's button), or None: at
    # the pointer (the launcher, the shortcut). From a later start (apps/Headline/instance.py).
    panelRequested = Signal("QVariant")

    def __init__(self, model: HeadlineModel) -> None:
        super().__init__()
        self._model = model
        # How the tools start Scope and the time screen (tests put a recorder here).
        self._start = lambda command: subprocess.Popen(command, cwd=str(REPO_ROOT),
                                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._dock = (self._read_dock(), self.placeMode())
        self._look = self._read_look()
        self._widgets = widgets.shown()
        self._follow = QTimer(self)
        self._follow.setInterval(FOLLOW_MS)
        self._follow.timeout.connect(self._tick)

    def start_following(self) -> None:
        self._follow.start()

    @Slot(result="QVariantMap")
    def view(self) -> dict:
        return self._model.view()

    @Slot(result="QVariantList")
    def climb(self) -> list:
        return self._model.climb()

    @Slot(str, result="QVariantList")
    def children(self, path: str) -> list:
        return self._model.children(path)

    @Slot(str, result=bool)
    def go(self, path: str) -> bool:
        ok = self._model.go(path)
        if ok:
            self.changed.emit()
        return ok

    def _tick(self) -> None:
        self.followPlace()
        self.checkDock()
        self.checkTheme()
        self.checkWidgets()

    # --- widgets (apps/Headline/widgets.py; Designdocument Headline.md, 3a) -------------------------

    @Slot(result="QVariantList")
    def widgets(self) -> list:
        return self._widgets

    @Slot(result=bool)
    def checkWidgets(self) -> bool:
        """Read the widgets' views anew; True when what they show changed."""
        now = widgets.shown()
        if now == self._widgets:
            return False
        self._widgets = now
        self.widgetsChanged.emit()
        return True

    @Slot(str, str, result=bool)
    def widgetTell(self, widget_id: str, command: str) -> bool:
        return widgets.tell(widget_id, command)

    @Slot(str, result=bool)
    def widgetOpen(self, widget_id: str) -> bool:
        return widgets.open_screen(widget_id)

    @staticmethod
    def _read_dock() -> str:
        return str(Settings().get("Headline/dock"))

    @Slot(result=str)
    def placeMode(self) -> str:
        """Where the Headline lives: "top" (the line) or "taskbar" (only the panel)."""
        return str(Settings().get("Headline/place"))

    @Slot(result=str)
    def dockMode(self) -> str:
        return self._dock[0]

    @Slot(result=bool)
    def checkDock(self) -> bool:
        """Read the settings anew (Setup may have changed them); True when one changed."""
        now = (self._read_dock(), self.placeMode())
        if now == self._dock:
            return False
        self._dock = now
        self.dockChanged.emit()
        return True

    @staticmethod
    def _read_look() -> tuple:
        settings = Settings()
        return (bool(settings.get("General/darkTheme")), float(settings.get("General/embryoOpacity")))

    @Slot(result=bool)
    def checkTheme(self) -> bool:
        """Light / dark and the embryos' paleness, as Scope or Setup left them: the line is always
        there and must not wait for a new start (review 2026-11-18, H7). True when one changed."""
        now = self._read_look()
        if now == self._look:
            return False
        self._look = now
        self.themeChanged.emit()
        return True

    @Slot(result=bool)
    def followPlace(self) -> bool:
        ok = self._model.follow()
        if ok:
            self.changed.emit()
        return ok

    @Slot(result="QVariantList")
    def perspectives(self) -> list:
        return self._model.perspectives()

    @Slot("QVariantList", result=bool)
    def wear(self, lens) -> bool:
        ok = self._model.wear([str(part) for part in lens])
        if ok:
            self.changed.emit()
        return ok

    @Slot(str, str, result="QVariantMap")
    def dropPlan(self, payload: str, target: str) -> dict:
        """What a drop onto the folder target would move (H9); ask: folders among it are asked
        about first (Setup: General/askBeforeMove, off by default)."""
        plan = self._model.plan_drop(payload, target)
        plan["ask"] = bool(Settings().get("General/askBeforeMove"))
        return plan

    @Slot("QVariantList", str, result="QVariantMap")
    def dropMove(self, sources, target: str) -> dict:
        result = self._model.move([str(source) for source in sources], target)
        if result["moved"]:
            self.changed.emit()  # an embryo born, the folders as they are now
        return result

    @Slot(result="QVariantMap")
    def pointerRect(self) -> dict:
        pos = QCursor.pos()
        return {"x": pos.x(), "y": pos.y(), "width": 1, "height": 1}

    # --- its own settings (2026-11-18: a program of its own, SEITON's master) -------------------

    # What its settings window may set: where and how it sits, and SEITON's look.
    OWN_SETTINGS = ("Headline/place", "Headline/dock", "General/darkTheme")

    @Slot()
    def openSetup(self) -> None:
        self.setupRequested.emit()

    @Slot(str, result="QVariant")
    def setting(self, key: str):
        return Settings().get(key) if key in self.OWN_SETTINGS else None

    @Slot(str, "QVariant", result=bool)
    def setSetting(self, key: str, value) -> bool:
        """Set one of its own settings; it takes effect at once (the line, the dock, the look)."""
        if key not in self.OWN_SETTINGS or not Settings().set(key, value):
            return False
        self.checkDock()
        self.checkTheme()
        return True

    @Slot(str, result=bool)
    def openScope(self, action: str) -> bool:
        """Scope where one is, perhaps with a task (setup, search, clipboard; Scope.py --<task>).
        A program of its own; the Headline does not wait for it."""
        command = [sys.executable, str(REPO_ROOT / "apps" / "Scope" / "Scope.py"), self._model.cwd]
        if action in ("setup", "search", "clipboard"):
            command.append(f"--{action}")
        try:
            self._start(command)
            return True
        except OSError:
            return False

    @Slot(result=bool)
    def openTime(self) -> bool:
        """The time screen of the time tracking (its launcher, written by the installer)."""
        launcher = shutil.which("seiton-time") or str(Path.home() / ".local" / "bin" / "seiton-time")
        try:
            self._start([launcher])
            return True
        except OSError:
            return False

    @Slot()
    def switchTheme(self) -> None:
        """Light / dark, for Scope, SunTree and the Headline (General/darkTheme)."""
        settings = Settings()
        settings.set("General/darkTheme", not settings.get("General/darkTheme"))
        self._look = self._read_look()
        self.themeChanged.emit()

    @Slot(result="QVariantMap")
    def colorScheme(self) -> dict:
        return load_scheme("dark" if Settings().get("General/darkTheme") else "light")

    @Slot(result=float)
    def embryoOpacity(self) -> float:
        return float(Settings().get("General/embryoOpacity"))

    # --- where popups go (popup_place.py) ------------------------------------------------------

    @staticmethod
    def _room(anchor: tuple) -> tuple:
        x, y, w, h = anchor
        screen = QGuiApplication.screenAt(QPoint(x + w // 2, y + h // 2)) or QGuiApplication.primaryScreen()
        room: QRect = screen.availableGeometry()
        return (room.x(), room.y(), room.width(), room.height())

    @Slot("QVariantMap", int, int, result="QVariantMap")
    def placeDrop(self, anchor, width: int, height: int) -> dict:
        """anchor: {x, y, width, height} on the screen; where a dropdown of that size goes."""
        rect = _rect(anchor)
        return popup_place.drop(rect, (width, height), self._room(rect))

    @Slot("QVariantMap", int, int, result="QVariantMap")
    def placeSide(self, anchor, width: int, height: int) -> dict:
        rect = _rect(anchor)
        return popup_place.side(rect, (width, height), self._room(rect))


def dock(window, backend: HeadlineBackend) -> bool:
    """The line as a dock at the top of its screen (X11): with its room kept while always
    there, without while it hides itself. False where there is no X11 (offscreen, Wayland)."""
    if QGuiApplication.platformName() != "xcb":
        return False
    screen = window.screen().geometry()
    height = int(window.property("lineHeight"))
    ratio = window.devicePixelRatio()
    partial = (x11_dock.device_strut((screen.x(), screen.y(), screen.width(), screen.height()), height, ratio)
               if backend.dockMode() == "keep" else None)
    return x11_dock.apply_to(int(window.winId()), partial)


def load_headline(model: HeadlineModel, app: QGuiApplication) -> QQmlApplicationEngine:
    """The Headline's window on the model (no root object when main.qml fails). Shared by main()
    and the tests, so both load it alike."""
    engine = QQmlApplicationEngine()
    engine.addImageProvider("theme", ThemeIconProvider())
    backend = HeadlineBackend(model)
    engine.rootContext().setContextProperty("headline", backend)
    engine._backend = backend
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name("main.qml").resolve())))
    return engine


def install_translator(app: QGuiApplication, code: str) -> Optional[QTranslator]:
    """The Headline in the language code (as Scope and SunTree): the strings in the code are
    English, others load i18n/headline_<code>.qm. None for English or without a translation."""
    if code == "en":
        return None
    translator = QTranslator(app)
    if not translator.load(str(Path(__file__).with_name("i18n") / f"headline_{code}.qm")):
        return None
    app.installTranslator(translator)
    return translator


parse_start = instance.parse_start  # read before Qt is loaded (H5)


def to_logical(anchor: Optional[dict], ratio: float) -> Optional[dict]:
    """An anchor in device pixels (Cinnamon) in Qt's logical pixels."""
    if anchor is None or not ratio or ratio == 1.0:
        return anchor
    return {key: int(round(anchor[key] / ratio)) for key in instance.ANCHOR_KEYS}


def main(argv: Optional[list] = None) -> int:
    """Headline.py [--panel [--anchor x,y,w,h]] [place]: one Headline per user; a later start
    hands "open the panel" to the one running (the applet, the launcher, the shortcut) and
    ends; a later plain start opens the panel at the pointer."""
    place, request = parse_start(list(sys.argv[1:] if argv is None else argv))
    name = instance.server_name()
    if instance.hand_over(name, request or {"panel": None}):
        return 0
    start = start_place(place)
    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("Headline")
    app.setWindowIcon(seiton_icon())
    install_translator(app, str(Settings().get("General/language")))
    server = instance.InstanceServer(name)
    if not server.listen():
        # Another one came up meanwhile (two starts at once): it gets the request (H6).
        instance.hand_over(name, request or {"panel": None})
        return 0
    api = ScopeApi(start)
    link = LensLink(api, start_daemon=getenv("SCOPE_START_DAEMON", "1") != "0")
    # The active project for whoever wants it - the clock reads it (Designdocument Time.md, 4.1).
    told = active_file()
    report = lambda project, person: write_active(told, Path(project) if project else None, person)  # noqa: E731
    engine = load_headline(HeadlineModel(api, link, start, report=report), app)
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    backend = engine._backend
    dock(window, backend)
    backend.dockChanged.connect(lambda: dock(window, backend))
    ratio = app.primaryScreen().devicePixelRatio()
    server.panelRequested.connect(lambda anchor: backend.panelRequested.emit(to_logical(anchor, ratio)))
    backend.start_following()
    if request is not None:
        QTimer.singleShot(0, lambda: backend.panelRequested.emit(to_logical(request["panel"], ratio)))
    from core.quit_on_signal import quit_on_sigterm
    quit_on_sigterm(app)  # kill/logout: link.close() below still unmounts the lens drive (O2)
    code = app.exec()
    server.close()
    link.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
