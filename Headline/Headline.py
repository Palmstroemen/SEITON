#!/usr/bin/env python3
"""The Headline: SEITON at the screen's edge (Scope/Designdocument Headline.md).

A program of its own, as SunTree is. It shares where one is with Scope and SunTree through the
session of the lens; what it shows is worked out in Headline/model.py, where its popups go in
Headline/popup_place.py. Step 1: a line of its own with the CWD, the standard folders, the
cascade to climb; docking at the top edge comes in step 2.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QObject, QPoint, QRect, QTimer, QUrl, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from core.brand import getenv  # noqa: E402
from core.color_schemes import load_scheme  # noqa: E402
from core.scope_api import ScopeApi  # noqa: E402
from core.settings import Settings  # noqa: E402
from daemon.lens_link import LensLink  # noqa: E402
from Headline.model import HeadlineModel  # noqa: E402
from Headline import popup_place  # noqa: E402
from Scope.Scope import ThemeIconProvider  # noqa: E402
from Scope.window_icon import seiton_icon  # noqa: E402

FOLLOW_MS = 1000  # how often the Headline looks where Scope or SunTree went


def _rect(value) -> tuple:
    return (int(value["x"]), int(value["y"]), int(value["width"]), int(value["height"]))


class HeadlineBackend(QObject):
    changed = Signal()

    def __init__(self, model: HeadlineModel) -> None:
        super().__init__()
        self._model = model
        self._follow = QTimer(self)
        self._follow.setInterval(FOLLOW_MS)
        self._follow.timeout.connect(self.followPlace)

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

    @Slot(result=bool)
    def followPlace(self) -> bool:
        ok = self._model.follow()
        if ok:
            self.changed.emit()
        return ok

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


def main() -> int:
    start = sys.argv[1] if len(sys.argv) > 1 else str(Path.home())
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Headline")
    app.setWindowIcon(seiton_icon())
    api = ScopeApi(start)
    link = LensLink(api, start_daemon=getenv("SCOPE_START_DAEMON", "1") != "0")
    engine = load_headline(HeadlineModel(api, link, start), app)
    if not engine.rootObjects():
        return 1
    engine._backend.start_following()
    code = app.exec()
    link.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
