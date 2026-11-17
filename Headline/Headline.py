#!/usr/bin/env python3
"""The Headline: SEITON at the screen's edge (Scope/Designdocument Headline.md).

A program of its own, as SunTree is. It shares where one is with Scope and SunTree through the
session of the lens; what it shows is worked out in Headline/model.py, where its popups go in
Headline/popup_place.py. Step 1: a line of its own with the CWD, the standard folders, the
cascade to climb; docking at the top edge comes in step 2.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QObject, QPoint, QRect, QTimer, QTranslator, QUrl, Signal, Slot  # noqa: E402
from PySide6.QtGui import QCursor, QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from core.brand import getenv  # noqa: E402
from core.color_schemes import load_scheme  # noqa: E402
from core.scope_api import ScopeApi  # noqa: E402
from core.settings import Settings  # noqa: E402
from daemon.lens_link import LensLink  # noqa: E402
from Headline.model import HeadlineModel  # noqa: E402
from Headline import instance, popup_place, x11_dock  # noqa: E402
from Scope.Scope import ThemeIconProvider  # noqa: E402
from Scope.window_icon import seiton_icon  # noqa: E402

FOLLOW_MS = 1000  # how often the Headline looks where Scope or SunTree went


def _rect(value) -> tuple:
    return (int(value["x"]), int(value["y"]), int(value["width"]), int(value["height"]))


class HeadlineBackend(QObject):
    changed = Signal()
    dockChanged = Signal()
    # "Open the panel": at an anchor {x, y, width, height} (the applet's button), or None: at
    # the pointer (the launcher, the shortcut). From a later start (Headline/instance.py).
    panelRequested = Signal("QVariant")

    def __init__(self, model: HeadlineModel) -> None:
        super().__init__()
        self._model = model
        self._dock = (self._read_dock(), self.placeMode())
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

    @Slot(result="QVariantMap")
    def pointerRect(self) -> dict:
        pos = QCursor.pos()
        return {"x": pos.x(), "y": pos.y(), "width": 1, "height": 1}

    @Slot(result=bool)
    def openScope(self) -> bool:
        """Scope where one is (a program of its own; the Headline does not wait for it)."""
        try:
            subprocess.Popen([sys.executable, str(REPO_ROOT / "Scope" / "Scope.py"), self._model.cwd],
                             cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            return False

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
    partial = (x11_dock.strut((screen.x(), screen.y(), screen.width(), screen.height()), height)
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


def main(argv: Optional[list] = None) -> int:
    """Headline.py [--panel] [place]: one Headline per user; a later start hands "open the
    panel" to the one running (the launcher in the taskbar, the shortcut) and ends."""
    args = list(sys.argv[1:] if argv is None else argv)
    wants_panel = "--panel" in args
    places = [a for a in args if not a.startswith("--")]
    name = instance.server_name()
    if instance.hand_over(name, {"panel": None}):
        return 0
    start = places[0] if places else str(Path.home())
    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("Headline")
    app.setWindowIcon(seiton_icon())
    install_translator(app, str(Settings().get("General/language")))
    server = instance.InstanceServer(name)
    server.listen()
    api = ScopeApi(start)
    link = LensLink(api, start_daemon=getenv("SCOPE_START_DAEMON", "1") != "0")
    engine = load_headline(HeadlineModel(api, link, start), app)
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    backend = engine._backend
    dock(window, backend)
    backend.dockChanged.connect(lambda: dock(window, backend))
    server.panelRequested.connect(backend.panelRequested.emit)
    backend.start_following()
    if wants_panel:
        QTimer.singleShot(0, lambda: backend.panelRequested.emit(None))
    code = app.exec()
    server.close()
    link.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
