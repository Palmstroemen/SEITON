"""The Headline's line, offscreen (Headline/main.qml): it starts without QML errors, shows the
CWD and the standard folders, hides what does not fit behind », and its dropdowns are windows
of their own that open towards the room."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, Q_ARG, QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication, QWindow  # noqa: E402

from core.brand import META_DIR, env_name  # noqa: E402


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# SEITON Project\n")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("SCOPE_START_DAEMON"), "0")
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    standard = tmp_path / META_DIR / "Templates" / "Standard"
    for name in ("01_Info", "02_Planung", "03_Recht", "04_Finanz", "05_Material", "06_Fotos"):
        (standard / name).mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio")
    (studio / "01_Info").mkdir()
    return {"root": root.resolve(), "studio": studio.resolve()}


@pytest.fixture
def started(world):
    from core.scope_api import ScopeApi
    from daemon.lens_link import LensLink
    from Headline.Headline import load_headline
    from Headline.model import HeadlineModel

    messages = []

    def handler(kind, _context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) and "file://" in message:
            messages.append(message)

    previous = qInstallMessageHandler(handler)
    app = QGuiApplication.instance() or QGuiApplication([])
    api = ScopeApi(str(world["studio"]))
    engine = load_headline(HeadlineModel(api, LensLink(api, start_daemon=False), str(world["studio"])), app)
    app.processEvents()
    # Held here: PySide deletes the window once its last wrapper from rootObjects() is gone.
    window = engine.rootObjects()[0]
    yield {"engine": engine, "app": app, "messages": messages, "window": window}
    # Gone before the next test: a dying engine re-evaluates its bindings without "headline".
    for window in engine.rootObjects():
        window.close()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    qInstallMessageHandler(previous)


def _find(started, name):
    root = started["window"]
    return root if root.objectName() == name else root.findChild(QObject, name)


def _items(item):
    """Visual children, all the way down (a Repeater's items are no QObject children)."""
    for child in item.childItems():
        yield child
        yield from _items(child)


def _all(started, name, window=None):
    root = (window or started["window"]).contentItem()
    return [item for item in _items(root) if item.objectName() == name]


def _settle(app, rounds=5):
    for _ in range(rounds):
        app.processEvents()


def test_it_starts_without_qml_errors(started):
    assert started["engine"].rootObjects(), "QML failed to load"
    assert not started["messages"], "\n".join(started["messages"])


def test_the_line_shows_the_cwd_and_the_standard_folders(started):
    engine = started
    _settle(started["app"])
    assert _find(engine, "cwdButton").property("label") == "Musikstudio"
    labels = [o.property("label") for o in _all(engine, "standardFolder")]
    assert labels == ["01_Info", "02_Planung", "03_Recht", "04_Finanz", "05_Material", "06_Fotos"]
    pale = {o.property("label"): o.property("opacity") for o in _all(engine, "standardFolder")}
    assert pale["01_Info"] == 1.0 and pale["04_Finanz"] < 1.0  # born, suggested


def test_what_does_not_fit_goes_behind_more(started):
    engine, app = started, started["app"]
    line = _find(engine, "headlineLine")
    line.setProperty("width", 2000)
    _settle(app)
    assert not _find(engine, "moreButton").property("visible")
    line.setProperty("width", 330)
    _settle(app)
    shown = [o for o in _all(engine, "standardFolder") if o.property("visible")]
    assert 0 < len(shown) < 6
    assert _find(engine, "moreButton").property("visible")


def _activate(item):
    QMetaObject.invokeMethod(item, "activate", Q_ARG(bool, False), Q_ARG(bool, False))


def test_the_way_up_is_a_window_of_its_own_below_the_line(started):
    engine, app = started, started["app"]
    _settle(app)
    _activate(_find(engine, "cwdButton"))
    _settle(app)
    climb = _find(engine, "climbList")
    assert isinstance(climb, QWindow) and climb.isVisible()
    line = _find(engine, "headlineLine")
    assert climb.y() >= line.y() + line.height()  # from the top it drops down
    assert [o.property("label") for o in _all(started, "dropRow", climb)] == ["Projekte", "Musikstudio"]


def _wait(app, ms):
    import time
    end = time.monotonic() + ms / 1000
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


def _call(item, name):
    QMetaObject.invokeMethod(item, name)


def test_always_there_it_keeps_its_height(started):
    line = _find(started, "headlineLine")
    assert line.property("dockMode") == "keep"
    assert line.height() == line.property("lineHeight")


@pytest.fixture
def hiding(world, monkeypatch):
    from core.settings import Settings

    assert Settings().set("Headline/dock", "hide")
    return world


def test_hiding_itself_it_is_a_thin_edge_until_the_pointer_comes(hiding, started):
    app = started["app"]
    line = _find(started, "headlineLine")
    _settle(app)
    assert line.property("dockMode") == "hide"
    assert line.height() <= 2
    _call(line, "pointerEntered")
    _settle(app)
    assert line.height() == line.property("lineHeight")  # at once
    _call(line, "pointerLeft")
    _wait(app, 200)
    assert line.height() == line.property("lineHeight")  # not yet
    _wait(app, 500)
    assert line.height() <= 2  # gone about 0.5 s after the pointer left


def test_while_a_dropdown_is_open_it_stays(hiding, started):
    app = started["app"]
    line = _find(started, "headlineLine")
    _call(line, "pointerEntered")
    _settle(app)
    _activate(_find(started, "cwdButton"))
    _settle(app)
    _call(line, "pointerLeft")
    _wait(app, 800)
    assert line.height() == line.property("lineHeight")
