"""The Headline's line, offscreen (apps/Headline/main.qml): it starts without QML errors, shows the
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
    from core.settings import Settings
    assert Settings().set("Headline/dock", "keep")  # most tests look at the open line
    return {"root": root.resolve(), "studio": studio.resolve()}


@pytest.fixture
def started(world):
    from core.scope_api import ScopeApi
    from daemon.lens_link import LensLink
    from apps.Headline.Headline import load_headline
    from apps.Headline.model import HeadlineModel

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
    labels = [o.property("label") for o in _all(started, "dropRow", climb)]
    assert labels[0] == "/" and labels[-2:] == ["Projekte", "Musikstudio"]  # above the root too


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
    _wait(app, 700)
    assert line.height() <= 2  # gone about 0.5 s after the pointer left, slid out


def _row_y(started):
    return _find(started, "cwdButton").mapToItem(None, 0, 0).y()


def test_hiding_itself_it_slides_in_and_out(hiding, started):
    """It slides in from above and out again (2026-11-18), the window as high as the line
    meanwhile: the pointer stays in it."""
    app = started["app"]
    line = _find(started, "headlineLine")
    _settle(app)
    _call(line, "pointerEntered")
    _settle(app)
    assert line.height() == line.property("lineHeight")
    assert line.property("reveal") < 1 and _row_y(started) < 0  # still coming in
    _wait(app, 300)
    assert line.property("reveal") == 1 and _row_y(started) >= 0
    _call(line, "pointerLeft")
    import time
    seen, end = [], time.monotonic() + 1.2  # 0.5 s, then 150 ms sliding out
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.005)
        seen.append((line.property("reveal"), line.height()))
    going = [(r, h) for r, h in seen if 0 < r < 1]
    assert going and all(h == line.property("lineHeight") for _r, h in going)  # slid, the window high
    assert line.property("reveal") == 0 and line.height() <= 2


def test_always_there_it_does_not_slide(started):
    line = _find(started, "headlineLine")
    assert line.property("reveal") == 1 and _row_y(started) >= 0


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
    from apps.Headline import widgets

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
    _find(started, "headlineLine").setProperty("pointerOnLine", True)
    climb.setProperty("pointerInside", False)
    _wait(app, 900)
    assert climb.isVisible()  # on the line it stays too
    _find(started, "headlineLine").setProperty("pointerOnLine", False)
    _wait(app, 900)
    assert not climb.isVisible()


# --- the tools: a row of small buttons on top of the way up and in the panel (2026-11-17) -----

# No time tool since 2026-11-18: the stopwatch in the CWD's tab opens the time screen.
TOOLS = ["toolScope", "toolSetup", "toolSearch", "toolClipboard", "toolTheme"]


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


@pytest.mark.parametrize("tool, command_ends", [("toolSearch", "--search"), ("toolClipboard", "--clipboard")])
def test_search_and_clipboard_open_scope_here(started, world, tool, command_ends):
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


def test_a_folder_dropped_moves_without_asking_by_default(world, started):
    _settle(started["app"])
    folder = world["studio"] / "Alte Sachen"
    folder.mkdir()
    [info] = [o for o in _all(started, "standardFolder") if o.property("label") == "01_Info"]
    _drop(info, str(folder))
    _settle(started["app"])
    assert not _find(started, "dropAsk").isVisible()
    assert (world["studio"] / "01_Info" / "Alte Sachen").is_dir()


def test_a_folder_dropped_is_asked_about_first_when_setup_says_so(world, started):
    from core.settings import Settings
    assert Settings().set("General/askBeforeMove", True)
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



# --- its own settings (2026-11-18: the Headline is a program of its own, SEITON's master) -----

def _settings_window(started):
    panel = _open_panel(started, None)
    _activate(_all(started, "toolSetup", panel)[0])
    _settle(started["app"])
    return _find(started, "headlineSettings")


def test_setup_opens_its_own_settings_not_scope(started):
    backend = started["engine"]._backend
    ran = []
    backend._start = ran.append
    window = _settings_window(started)
    assert isinstance(window, QWindow) and window.isVisible()
    assert ran == []  # no Scope started


def test_where_and_how_it_sits_take_effect_at_once(started):
    from core.settings import Settings
    window = _settings_window(started)
    line = _find(started, "headlineLine")
    assert _all(started, "settingsDock_keep", window)[0].property("on")
    _activate(_all(started, "settingsDock_hide", window)[0])
    _settle(started["app"])
    assert Settings().get("Headline/dock") == "hide" and line.property("dockMode") == "hide"
    _activate(_all(started, "settingsPlace_taskbar", window)[0])
    _settle(started["app"])
    assert Settings().get("Headline/place") == "taskbar" and not line.isVisible()
    assert not _all(started, "settingsDock_keep", window)[0].property("visible")  # only for the top edge


def test_light_or_dark_is_set_here(started):
    from core.settings import Settings
    window = _settings_window(started)
    line = _find(started, "headlineLine")
    colour = line.property("theme")["bg"]
    dark = Settings().get("General/darkTheme")
    _activate(_all(started, "settingsLook_light" if dark else "settingsLook_dark", window)[0])
    _settle(started["app"])
    assert Settings().get("General/darkTheme") is (not dark)
    assert line.property("theme")["bg"] != colour


def test_more_settings_are_in_scope(started, world):
    backend = started["engine"]._backend
    ran = []
    backend._start = ran.append
    window = _settings_window(started)
    _activate(_all(started, "settingsMoreInScope", window)[0])
    _settle(started["app"])
    assert ran and ran[-1][-1] == "--setup" and ran[-1][-3].endswith("Scope.py")


def test_only_its_own_settings_can_be_set_from_its_window(started):
    backend = started["engine"]._backend
    assert backend.setSetting("General/postFix", False) is False  # not its own
    assert backend.setSetting("Headline/dock", "nonsense") is False


# --- small things (2026-11-18) -----------------------------------------------------------------

def test_the_cwd_shows_it_is_a_project(started):
    _settle(started["app"])
    assert _find(started, "cwdButton").property("projectBadge") is True  # Musikstudio is one


def test_a_cwd_that_is_no_project_has_no_p(world, started):
    plain = world["studio"] / "01_Info"
    backend = started["engine"].rootContext().contextProperty("headline")
    assert backend.go(str(plain))
    _settle(started["app"])
    assert _find(started, "cwdButton").property("projectBadge") is False


def test_when_all_fit_none_hides_behind_more(started):
    """» takes room only when something must hide: just wide enough for all, all are shown."""
    engine, app = started, started["app"]
    line = _find(engine, "headlineLine")
    line.setProperty("width", 3000)
    _settle(app)
    folders = _all(engine, "standardFolder")
    spacing = 4
    cwd = _find(engine, "cwdButton").property("width")
    needed = cwd + sum(f.property("implicitWidth") + spacing for f in folders) + 2 * spacing + 8
    line.setProperty("width", int(needed) + 1)
    _settle(app)
    assert all(f.property("visible") for f in _all(engine, "standardFolder"))
    assert not _find(engine, "moreButton").property("visible")
    line.setProperty("width", int(needed) - 20)
    _settle(app)
    assert _find(engine, "moreButton").property("visible")


def _text_middle(item, label):
    """The middle of the text that shows label inside item, in the window."""
    for child in _items(item):
        if child.property("text") == label and child.property("visible") and child.property("height"):
            return child.mapToItem(None, 0, 0).y() + child.property("height") / 2
    raise AssertionError(f"no text {label!r}")


def test_the_cwd_s_name_stands_on_the_line_of_the_folders(started):
    """The CWD's name stood a few pixels above the folders' names (2026-11-18)."""
    _settle(started["app"])
    cwd = _find(started, "cwdButton")
    folder = _all(started, "standardFolder")[0]
    assert abs(_text_middle(cwd, "Musikstudio") - _text_middle(folder, "01_Info")) <= 1


# --- the clock as a stopwatch in the CWD's tab (2026-11-18) ------------------------------------

def _stopwatch_view(folder, **view):
    import json
    base = {"text": "Musikstudio · 2:15", "state": "active", "icon": "stopwatch",
            "tooltip": "Musikstudio: 2:15 h today"}
    base.update(view)
    (folder / "view.json").write_text(json.dumps(base))


def test_a_widget_with_an_icon_sits_in_the_cwd_s_tab(a_clock, started):
    _stopwatch_view(a_clock)
    started["engine"]._backend.checkWidgets()
    _wait(started["app"], 300)  # rows are laid out with the next frame (late under load)
    assert _all(started, "widget") == []  # nothing at the right
    [icon] = _all(started, "widgetIcon")
    cwd = _find(started, "cwdButton")
    x = icon.mapToItem(cwd, 0, 0).x()
    assert 0 < x and x + icon.property("width") <= cwd.property("width")  # inside the tab
    assert icon.property("tip") == "Musikstudio: 2:15 h today"


def test_while_it_counts_it_beats_else_not(a_clock, started):
    _stopwatch_view(a_clock)
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    assert icon.property("beating") is True and icon.property("warn") is False
    _stopwatch_view(a_clock, state="calm")
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    assert icon.property("beating") is False and icon.property("opacity") < 1
    _stopwatch_view(a_clock, state="calm", warn=True)
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    assert icon.property("warn") is True and icon.property("opacity") == 1


def test_a_click_on_the_icon_opens_its_screen_not_the_cwd(a_clock, started, monkeypatch):
    from apps.Headline import widgets
    opened = []
    monkeypatch.setattr(widgets, "open_screen", lambda widget_id, *a, **k: opened.append(widget_id) or True)
    _stopwatch_view(a_clock)
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    QMetaObject.invokeMethod(icon, "open")
    _settle(started["app"])
    assert opened == ["clock"]
    assert not _find(started, "climbList").property("visible")


def test_asking_its_question_stands_at_the_right_without_a_button(a_clock, started):
    _stopwatch_view(a_clock, state="asking", question={
        "text": "Still working on Musikstudio?",
        "answers": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}]})
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    assert _all(started, "widget") == []
    [question] = _all(started, "widgetQuestion")
    assert question.property("visible") and question.property("text") == "Still working on Musikstudio?"
    assert [o.property("label") for o in _all(started, "widgetAnswer")] == ["Yes", "No"]


def test_a_real_click_on_the_icon_reaches_it_not_the_tab(a_clock, started, monkeypatch):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from apps.Headline import widgets
    opened = []
    monkeypatch.setattr(widgets, "open_screen", lambda widget_id, *a, **k: opened.append(widget_id) or True)
    _stopwatch_view(a_clock)
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    middle = icon.mapToItem(None, icon.property("width") / 2, icon.property("height") / 2)
    QTest.mouseClick(started["window"], Qt.LeftButton, Qt.NoModifier, QPoint(int(middle.x()), int(middle.y())))
    _wait(started["app"], 400)  # the tab's single click waits for a double click
    assert opened == ["clock"]
    assert not _find(started, "climbList").property("visible")


def test_the_tooltip_is_a_window_of_its_own_below_the_line(a_clock, started):
    """In the line's window (30 px) the tooltip was cut off at the bottom (2026-11-18)."""
    _stopwatch_view(a_clock)
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    QMetaObject.invokeMethod(icon, "showTip")
    _wait(started["app"], 600)  # it comes after a short while
    tip = _find(started, "tipWindow")
    line = _find(started, "headlineLine")
    assert isinstance(tip, QWindow) and tip.isVisible()
    assert tip.property("text") == "Musikstudio: 2:15 h today"
    assert tip.y() >= line.y() + line.property("lineHeight")  # below the line, whole
    QMetaObject.invokeMethod(icon, "hideTip")
    _settle(started["app"])
    assert not tip.isVisible()


# --- found on the desktop (2026-11-18) ---------------------------------------------------------

@pytest.mark.parametrize("mode", ["keep", "hide"])
def test_a_dropdown_left_without_a_choice_goes(world, started, mode):
    """The dropdown stayed for ever when one chose nothing: the line counted the pointer as in
    it while a dropdown was open, the dropdown waited for the pointer to leave the line."""
    from core.settings import Settings
    app = started["app"]
    line = _find(started, "headlineLine")
    Settings().set("Headline/dock", mode)
    started["engine"]._backend.checkDock()
    _settle(app)
    _call(line, "pointerEntered")
    _settle(app)
    _activate(_find(started, "cwdButton"))
    _settle(app)
    climb = _find(started, "climbList")
    assert climb.property("visible")
    _call(line, "pointerLeft")  # and not into the dropdown
    _wait(app, 1500)
    assert not climb.property("visible")
    if mode == "hide":
        _wait(app, 800)
        assert line.height() <= 2  # then the line slides out too


def _open_cascade(started, level, path):
    line = _find(started, "headlineLine")
    QMetaObject.invokeMethod(line, "openCascade", Q_ARG("QVariant", level),
                             Q_ARG("QVariant", _find(started, "cwdButton")), Q_ARG("QVariant", {"path": str(path)}))
    _settle(started["app"])


def _cascade_rows(started, level):
    name = "cascade" if level == 1 else f"cascade{level}"
    window = _find(started, name)
    if window is None or not window.isVisible():
        return None
    return [o.property("label") for o in _all(started, "dropRow", window)]


def test_the_cascades_go_as_deep_as_the_folders(world, started):
    """Only one step to the right could be opened; in Scope's trial it went on (2026-11-18)."""
    deep = world["studio"] / "01_Info" / "Archiv" / "2025"
    deep.mkdir(parents=True)
    _open_cascade(started, 1, world["root"])
    assert "Musikstudio" in _cascade_rows(started, 1)
    _open_cascade(started, 2, world["studio"])
    assert _cascade_rows(started, 2) == ["01_Info"]
    _open_cascade(started, 3, world["studio"] / "01_Info")
    assert _cascade_rows(started, 3) == ["Archiv"]
    _open_cascade(started, 4, world["studio"] / "01_Info" / "Archiv")
    assert _cascade_rows(started, 4) == ["2025"]
    assert _find(started, "headlineLine").property("popupOpen")
    _open_cascade(started, 2, world["studio"])  # back up: the deeper ones go
    assert _cascade_rows(started, 2) == ["01_Info"] and _cascade_rows(started, 3) is None
    assert _cascade_rows(started, 4) is None


def test_a_row_hovered_in_a_cascade_opens_the_next(world, started):
    (world["studio"] / "01_Info" / "Archiv").mkdir(parents=True)
    _open_cascade(started, 1, world["root"])
    cascade = _find(started, "cascade")
    [studio] = [o for o in _all(started, "dropRow", cascade) if o.property("label") == "Musikstudio"]
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest
    middle = studio.mapToItem(None, studio.property("width") / 2, studio.property("height") / 2)
    QTest.mouseMove(cascade, QPoint(int(middle.x()), int(middle.y())))
    _settle(started["app"])
    assert _cascade_rows(started, 2) == ["01_Info"]


def test_a_project_row_wears_its_colour_and_the_way_above_is_pale(world, started):
    (world["studio"] / META_DIR / "Color.md").write_text("#c03030\n")
    _activate(_find(started, "cwdButton"))
    _settle(started["app"])
    climb = _find(started, "climbList")
    rows = {o.property("label"): o for o in _all(started, "dropRow", climb)}
    plain, studio = rows["Projekte"], rows["Musikstudio"]
    assert studio.property("fillColor") != plain.property("fillColor")
    assert studio.property("fillColor").red() > studio.property("fillColor").blue()  # tinted red
    above = [o for name, o in rows.items() if name not in ("Projekte", "Musikstudio")]
    assert above and all(o.property("opacity") < 1 for o in above)
    assert plain.property("opacity") == 1


def _visible_items(item, name):
    return [c for c in _items(item) if c.objectName() == name and c.property("visible")]


def test_a_project_is_a_folder_with_a_small_p_not_a_big_badge(started):
    """The big P instead of the folder shouted (2026-11-18): a folder, a small P on it."""
    _settle(started["app"])
    cwd = _find(started, "cwdButton")
    assert _visible_items(cwd, "badge") == []  # the folder icon stays
    assert len(_visible_items(cwd, "projectP")) == 1
    _activate(cwd)
    _settle(started["app"])
    climb = _find(started, "climbList")
    [studio] = [o for o in _all(started, "dropRow", climb) if o.property("label") == "Musikstudio"]
    assert _visible_items(studio, "badge") == [] and len(_visible_items(studio, "projectP")) == 1


def test_without_a_clock_the_stopwatch_is_greyed_and_opens_the_time_screen(a_clock, started, monkeypatch):
    import json
    from apps.Headline import widgets
    registration = json.loads((widgets.widgets_dir() / "clock.json").read_text())
    registration["icon"] = "stopwatch"
    (widgets.widgets_dir() / "clock.json").write_text(json.dumps(registration))
    (a_clock / "view.json").unlink()  # no clock runs
    opened = []
    monkeypatch.setattr(widgets, "open_screen", lambda widget_id, *a, **k: opened.append(widget_id) or True)
    started["engine"]._backend.checkWidgets()
    _settle(started["app"])
    [icon] = _all(started, "widgetIcon")
    assert icon.property("off") is True and icon.property("opacity") < 0.45
    assert icon.property("beating") is False and "not running" in icon.property("tip")
    QMetaObject.invokeMethod(icon, "open")
    _settle(started["app"])
    assert opened == ["clock"]
