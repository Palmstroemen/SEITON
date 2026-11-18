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


# --- the panel (step 3): the same model as a list, opened at the pointer or at a button ------

def _panel(started):
    return _find(started, "panel")


def _open_panel(started, anchor):
    engine_backend = started["engine"]._backend
    engine_backend.panelRequested.emit(anchor)
    _settle(started["app"])
    return _panel(started)


def test_from_the_taskbar_the_panel_opens_upwards_above_the_button(started):
    screen = QGuiApplication.primaryScreen().availableGeometry()
    button = {"x": 10, "y": screen.y() + screen.height() - 2, "width": 40, "height": 40}
    panel = _open_panel(started, button)
    assert isinstance(panel, QWindow) and panel.isVisible()
    assert panel.y() + panel.height() <= button["y"]  # above the button: upwards
    assert panel.x() == 10


def test_the_panel_lists_the_path_the_standard_folders_and_the_perspectives(world, started):
    (world["root"] / META_DIR / "Perspectives.md").write_text("# Perspectives\n04_Finanz\n")
    panel = _open_panel(started, None)  # at the pointer
    assert panel.isVisible()
    assert [o.property("label") for o in _all(started, "panelPath", panel)] == ["Projekte", "Musikstudio"]
    folders = [o.property("label") for o in _all(started, "panelFolder", panel)]
    assert folders[:2] == ["01_Info", "02_Planung"] and len(folders) == 6
    assert [o.property("label") for o in _all(started, "panelPerspective", panel)] == ["04_Finanz"]


def test_a_perspective_in_the_panel_puts_the_lens_on(world, started):
    (world["root"] / META_DIR / "Perspectives.md").write_text("# Perspectives\n04_Finanz\n")
    panel = _open_panel(started, None)
    _activate(_all(started, "panelPerspective", panel)[0])
    _settle(started["app"])
    assert started["engine"]._backend.view()["lens"]["active"]
    assert _all(started, "panelPerspective", panel)[0].property("textBold")  # worn: lit


@pytest.fixture
def from_the_taskbar(world):
    from core.settings import Settings

    assert Settings().set("Headline/place", "taskbar")
    return world


def test_from_the_taskbar_there_is_no_line(from_the_taskbar, started):
    _settle(started["app"])
    assert not _find(started, "headlineLine").isVisible()
    assert _open_panel(started, None).isVisible()  # the panel still comes


# --- widgets (step 2a): the time tracking and others put themselves in ------------------------

@pytest.fixture
def a_clock(world, tmp_path):
    import json
    from Headline import widgets

    folder = tmp_path / "run" / "seiton-clock"
    folder.mkdir(parents=True)
    widgets.widgets_dir().mkdir(parents=True)
    (widgets.widgets_dir() / "clock.json").write_text(json.dumps(
        {"name": "Time", "folder": str(folder), "open": ["true"], "commands": ["start", "stop"]}))
    items = [{"text": f"P{i} · 0:{i}0", "path": str(world["root"] / f"P{i}")} for i in range(5)]
    (folder / "view.json").write_text(json.dumps({
        "text": "Musikstudio · 2:15", "state": "asking", "items": items,
        "question": {"text": "Still working on Musikstudio?",
                     "answers": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}]}}))
    return folder


def test_a_widget_stands_in_the_line(a_clock, started):
    _settle(started["app"])
    [widget] = _all(started, "widget")
    assert widget.property("label") == "Musikstudio · 2:15"
    assert [o.property("label") for o in _all(started, "widgetAnswer")] == ["Yes", "No"]


def test_an_answer_tells_the_widget(a_clock, started):
    _settle(started["app"])
    _activate(_all(started, "widgetAnswer")[0])
    _settle(started["app"])
    assert [p.name.split("-", 1)[1] for p in (a_clock / "commands").iterdir()] == ["yes"]


def test_in_the_panel_the_last_three_and_more(a_clock, started):
    panel = _open_panel(started, None)
    assert [o.property("label") for o in _all(started, "panelWidgetItem", panel)] == [
        "P0 · 0:00", "P1 · 0:10", "P2 · 0:20"]
    assert len(_all(started, "panelWidgetMore", panel)) == 1


def test_without_widgets_nothing_stands_there(started):
    _settle(started["app"])
    assert _all(started, "widget") == []


# --- dropdowns do not take the clicks (2026-11-17: a second popup took them on X11, so one
# --- could never click back in the way up; seen on the real desktop, not offscreen) ----------

def test_the_dropdowns_take_no_clicks_from_each_other(started):
    from PySide6.QtCore import Qt
    for name in ("climbList", "cascade", "moreList"):
        flags = _find(started, name).flags()
        assert (flags & Qt.WindowType.WindowType_Mask) == Qt.WindowType.ToolTip, name


def test_they_close_once_the_pointer_left_them_and_the_line(started):
    app = started["app"]
    _activate(_find(started, "cwdButton"))
    _settle(app)
    climb = _find(started, "climbList")
    climb.setProperty("pointerInside", True)
    _wait(app, 900)
    assert climb.isVisible()  # the pointer is in it
    _find(started, "headlineLine").setProperty("pointerInside", True)
    climb.setProperty("pointerInside", False)
    _wait(app, 900)
    assert climb.isVisible()  # on the line it stays too
    _find(started, "headlineLine").setProperty("pointerInside", False)
    _wait(app, 900)
    assert not climb.isVisible()


# --- the tools: a row of small buttons on top of the way up and in the panel (2026-11-17) -----

TOOLS = ["toolScope", "toolSetup", "toolSearch", "toolClipboard", "toolTime", "toolTheme"]


def test_the_way_up_has_the_tools_on_top(started):
    _activate(_find(started, "cwdButton"))
    _settle(started["app"])
    climb = _find(started, "climbList")
    names = [i.objectName() for i in _items(climb.contentItem()) if i.objectName().startswith("tool")]
    assert names == TOOLS
    tools = _all(started, "toolSetup", climb)[0]
    assert tools.mapToScene(tools.boundingRect().topLeft()).y() < _all(started, "dropRow", climb)[0].mapToScene(
        _all(started, "dropRow", climb)[0].boundingRect().topLeft()).y()


def test_the_panel_has_them_too(started):
    panel = _open_panel(started, None)
    assert [i.objectName() for i in _items(panel.contentItem()) if i.objectName().startswith("tool")] == TOOLS


@pytest.mark.parametrize("tool, command_ends", [
    ("toolSetup", "--setup"), ("toolSearch", "--search"), ("toolClipboard", "--clipboard")])
def test_setup_search_and_clipboard_open_scope_here(started, world, tool, command_ends):
    backend = started["engine"]._backend
    ran = []
    backend._start = ran.append
    panel = _open_panel(started, None)
    _activate(_all(started, tool, panel)[0])
    _settle(started["app"])
    assert ran and ran[-1][-2:] == [str(world["studio"]), command_ends]
    assert ran[-1][-3].endswith("Scope.py")


def test_scope_alone_opens_scope_here(started, world):
    backend = started["engine"]._backend
    ran = []
    backend._start = ran.append
    panel = _open_panel(started, None)
    _activate(_all(started, "toolScope", panel)[0])
    _settle(started["app"])
    assert ran[-1][-1] == str(world["studio"]) and ran[-1][-2].endswith("Scope.py")  # no task


def test_time_opens_the_time_screen(started):
    backend = started["engine"]._backend
    ran = []
    backend._start = ran.append
    panel = _open_panel(started, None)
    _activate(_all(started, "toolTime", panel)[0])
    _settle(started["app"])
    assert ran and "seiton-time" in ran[-1][0]


def test_light_and_dark_switch_at_once(started):
    from core.settings import Settings
    before = Settings().get("General/darkTheme")
    line = _find(started, "headlineLine")
    colour = line.property("theme")["bg"]
    panel = _open_panel(started, None)
    _activate(_all(started, "toolTheme", panel)[0])
    _settle(started["app"])
    assert Settings().get("General/darkTheme") is (not before)
    assert line.property("theme")["bg"] != colour


def test_a_running_widget_counts_the_seconds(a_clock, started):
    import json
    import re
    import time as clock_time
    view = json.loads((a_clock / "view.json").read_text())
    view.update(state="active", counter={"prefix": "Musikstudio · ", "since": clock_time.time() - 3725})
    (a_clock / "view.json").write_text(json.dumps(view))
    started["engine"]._backend.checkWidgets()
    _wait(started["app"], 1200)
    label = _all(started, "widget")[0].property("label")
    assert re.fullmatch(r"Musikstudio · 1:02:0\d", label), label


# --- found in the review of 2026-11-18 -------------------------------------------------------

def _besides(started, entries):
    from PySide6.QtCore import Q_ARG as ARG
    cascade = _find(started, "cascade")
    cascade.setProperty("entries", entries)
    QMetaObject.invokeMethod(cascade, "besides", ARG("QVariant", _find(started, "cwdButton")))
    _settle(started["app"])
    return cascade


def test_a_cascade_too_tall_is_cut_and_a_short_one_after_it_is_not(world, started):
    # H2: cut once, it stayed that tall; placed with the size of the list before.
    room = QGuiApplication.primaryScreen().availableGeometry()
    many = [{"name": f"Ordner {i:02d}", "path": str(world["root"] / f"O{i}")} for i in range(80)]
    cascade = _besides(started, many)
    assert cascade.y() + cascade.height() <= room.y() + room.height()
    tall = cascade.height()
    cascade = _besides(started, many[:3])
    assert cascade.height() < tall / 4
    column_height = cascade.contentItem().childItems()[0].property("contentHeight")
    assert cascade.height() == column_height + 8


def _perspectives(world, count):
    standard = world["root"].parent / META_DIR / "Templates" / "Standard" / "04_Finanz"
    for i in range(count):
        (standard / f"Teil {i:02d}").mkdir(parents=True, exist_ok=True)
    (world["root"] / META_DIR / "Perspectives.md").write_text(
        "# Perspectives\n" + "".join(f"04_Finanz/Teil {i:02d}\n" for i in range(count)))


def test_the_panel_in_the_middle_of_the_screen_is_cut_to_the_room(world, started):
    # H3 (review 2026-11-18): at the pointer it took no cut, its lower part ran out.
    _perspectives(world, 30)
    room = QGuiApplication.primaryScreen().availableGeometry()
    middle = {"x": 100, "y": room.y() + room.height() // 2, "width": 1, "height": 1}
    panel = _open_panel(started, middle)
    assert panel.y() >= room.y() and panel.y() + panel.height() <= room.y() + room.height()
    above, below = panel.y() + panel.height() <= middle["y"], panel.y() >= middle["y"] + 1
    assert above or below  # beside the pointer, not over it


def test_the_open_panel_grows_towards_the_room(world, started):
    # H3: what it shows changed while open - it kept its place and grew over the taskbar.
    room = QGuiApplication.primaryScreen().availableGeometry()
    button = {"x": 10, "y": room.y() + room.height() - 2, "width": 40, "height": 40}
    panel = _open_panel(started, button)
    small = panel.height()
    _perspectives(world, 6)
    started["engine"]._backend.changed.emit()
    _settle(started["app"])
    assert panel.height() > small
    assert panel.y() + panel.height() <= button["y"]  # still above the button


def test_light_dark_and_the_embryos_paleness_from_scope_or_setup_arrive(started):
    # H7 (review 2026-11-18): only its own switch reached the line, which is always there.
    from core.settings import Settings
    window, backend = started["window"], started["engine"]._backend
    before = window.property("theme")["bg"]
    settings = Settings()
    assert settings.set("General/darkTheme", not settings.get("General/darkTheme"))
    assert settings.set("General/embryoOpacity", 0.7)
    assert backend.checkTheme() is True
    _settle(started["app"])
    assert window.property("theme")["bg"] != before
    assert abs(window.property("embryoOpacity") - 0.7) < 1e-6
    assert backend.checkTheme() is False  # seen


def test_the_widgets_question_stands_in_the_line(a_clock, started):
    # H8 (review 2026-11-18): only "Yes" and "No" stood there, not what was asked.
    _settle(started["app"])
    [question] = _all(started, "widgetQuestion")
    assert question.property("text") == "Still working on Musikstudio?" and question.property("visible")


def test_hiding_itself_it_comes_out_while_a_widget_asks(hiding, a_clock, started):
    # H8: hidden, the question was never seen and the clock paused at the time it asked.
    _settle(started["app"])
    line = _find(started, "headlineLine")
    assert line.property("expanded") is True and line.height() == line.property("lineHeight")


def test_the_panel_counts_the_seconds_too(a_clock, started):
    # H8 (aside): the panel showed the widget's text without its counter.
    import json
    import re
    import time as clock_time
    view = json.loads((a_clock / "view.json").read_text())
    view.update(state="active", counter={"prefix": "Musikstudio · ", "since": clock_time.time() - 3725})
    (a_clock / "view.json").write_text(json.dumps(view))
    started["engine"]._backend.checkWidgets()
    panel = _open_panel(started, None)
    _wait(started["app"], 1200)
    label = _all(started, "panelWidget", panel)[0].property("label")
    assert re.fullmatch(r"Musikstudio · 1:02:0\d", label), label


# --- dropping onto a folder (H9) ---------------------------------------------------------------

def _drop(item, payload):
    QMetaObject.invokeMethod(item, "dropReceived", Q_ARG(str, payload))


def test_a_file_dropped_onto_a_pale_folder_in_the_line_bears_it(world, started):
    _settle(started["app"])
    note = world["studio"] / "Rechnung.pdf"
    note.write_text("r")
    [finanz] = [o for o in _all(started, "standardFolder") if o.property("label") == "04_Finanz"]
    _drop(finanz, f"file://{note}")
    _settle(started["app"])
    assert (world["studio"] / "04_Finanz" / "Rechnung.pdf").is_file() and not note.exists()
    [finanz] = [o for o in _all(started, "standardFolder") if o.property("label") == "04_Finanz"]
    assert finanz.property("opacity") == 1.0  # born now


def test_a_folder_dropped_is_asked_about_first(world, started):
    _settle(started["app"])
    folder = world["studio"] / "Alte Sachen"
    folder.mkdir()
    [info] = [o for o in _all(started, "standardFolder") if o.property("label") == "01_Info"]
    _drop(info, str(folder))
    _settle(started["app"])
    ask = _find(started, "dropAsk")
    assert ask.isVisible() and folder.exists()  # not yet
    [ok] = _all(started, "dropAskOk", ask)
    _activate(ok)
    _settle(started["app"])
    assert not ask.isVisible()
    assert (world["studio"] / "01_Info" / "Alte Sachen").is_dir() and not folder.exists()


def test_a_drop_into_the_panel_moves_too(world, started):
    note = world["studio"] / "Plan.pdf"
    note.write_text("p")
    panel = _open_panel(started, None)
    [planung] = [o for o in _all(started, "panelFolder", panel) if o.property("label") == "02_Planung"]
    _drop(planung, str(note))
    _settle(started["app"])
    assert (world["studio"] / "02_Planung" / "Plan.pdf").is_file()
