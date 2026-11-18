"""The time screen's window, offscreen (apps/Time/main.qml): it starts without QML errors, shows
Now, and adding a row there writes it."""

import os
from datetime import date, time, timedelta
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from core import clock_sources as cs  # noqa: E402
from core.brand import META_DIR, env_name  # noqa: E402


@pytest.fixture
def started(tmp_path, monkeypatch):
    from apps.Time.model import TimeModel
    from apps.Time.TimeScreen import load_time_screen

    monkeypatch.setenv(env_name("ACL_USER"), "Oliver")
    project = tmp_path / "Projekte" / "Küche"
    (project / META_DIR).mkdir(parents=True)
    (project / META_DIR / "Project.md").write_text("x")
    active = tmp_path / "run" / "seiton" / "active-project.json"
    cs.write_active(active, project, "Oliver")
    messages = []

    def handler(kind, _context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) and "file://" in message:
            messages.append(message)

    previous = qInstallMessageHandler(handler)
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = load_time_screen(TimeModel(active=active, widget=tmp_path / "run" / "seiton-clock",
                                        today=lambda: date(2026, 11, 17)), app)
    window = engine.rootObjects()[0]
    app.processEvents()
    yield {"engine": engine, "window": window, "app": app, "messages": messages, "project": project}
    window.close()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    qInstallMessageHandler(previous)


def _named(started, name):
    from PySide6.QtCore import QObject
    return started["window"].findChildren(QObject, name)


def test_it_starts_without_qml_errors(started):
    assert not started["messages"], "\n".join(started["messages"])


def test_now_names_the_project_and_says_the_clock_is_not_running(started):
    assert _named(started, "nowProject")[0].property("text") == "Küche"
    assert _named(started, "clockNotRunning")[0].property("visible")


def test_adding_a_row_writes_it_and_lists_it(started):
    from core import time_log as tl
    backend = started["engine"]._backend
    assert backend.add({"day": "2026-11-17", "start": "", "minutes": backend.parseMinutes("1:30"),
                        "note": "Baumarkt"}, "")
    started["app"].processEvents()
    rows = tl.read(tl.time_file(started["project"], "Oliver")).stretches
    assert rows[0].note == "Baumarkt" and rows[0].duration == timedelta(minutes=90)
    assert started["window"].property("rows")[0]["note"] == "Baumarkt"


@pytest.mark.parametrize("text, minutes", [("1:30", 90), ("90", 90), ("0:05", 5), ("x", -1), ("1:75", -1)])
def test_a_duration_is_typed_as_hours_and_minutes_or_minutes(text, minutes):
    from apps.Time.TimeScreen import parse_minutes
    assert parse_minutes(text) == minutes


def test_started_as_a_script_it_finds_its_modules():
    # As a script its own folder comes first on sys.path (the Headline failed so, 2026-11-17).
    import subprocess
    import sys
    script = Path(__file__).resolve().parents[1] / "TimeScreen.py"
    probe = (f"import runpy, sys; sys.path.insert(0, {str(script.parent)!r}); "
             f"names = runpy.run_path({str(script)!r}, run_name='probe'); "
             "from apps.Time.model import TimeModel; assert names['TimeModel'] is TimeModel; print('ok')")
    done = subprocess.run([sys.executable, "-c", probe], cwd=str(script.parent), capture_output=True,
                          text=True, timeout=60, env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().endswith("ok")


def test_the_project_is_chosen_the_active_one_first(started):
    # Z7 (review 2026-11-18): Entries and Overview were about the active project only.
    [choice] = _named(started, "projectChoice")
    assert choice.property("currentText") == "Küche"


def test_a_beginning_can_be_given_when_adding(started):
    from PySide6.QtCore import QMetaObject
    from core import time_log as tl
    window = started["window"]
    for name, text in (("addStart", "9:30"), ("addDuration", "0:45"), ("addNote", "Holz")):
        _named(started, name)[0].setProperty("text", text)
    QMetaObject.invokeMethod(_named(started, "addButton")[0], "clicked")
    started["app"].processEvents()
    [row] = tl.read(tl.time_file(started["project"], "Oliver")).stretches
    assert row.start.strftime("%H:%M") == "09:30" and row.duration == timedelta(minutes=45)
    assert window.property("rows")[0]["note"] == "Holz"


def test_how_it_rounds_is_set_here(started):
    from core.settings import Settings
    mode, per = _named(started, "roundMode")[0], _named(started, "roundPer")[0]
    assert mode.property("currentValue") == "up" and per.property("currentValue") == "stretch"


def test_a_chosen_project_stays_chosen_when_the_screen_refreshes(started, tmp_path):
    window = started["window"]
    other = started["project"].parent / "Dachboden"
    (other / META_DIR).mkdir(parents=True)
    (other / META_DIR / "Project.md").write_text("x")
    window.setProperty("project", str(other))
    from PySide6.QtCore import QMetaObject
    QMetaObject.invokeMethod(window, "refresh")
    started["app"].processEvents()
    assert window.property("project") == str(other)


# --- the dial on Now (2026-11-18): a green wedge for the hour, a seconds hand while it counts --

def _view(started, **view):
    import json
    folder = started["project"].parents[1] / "run" / "seiton-clock"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "view.json").write_text(json.dumps(view))
    started["window"].setProperty("nowView", started["engine"].rootContext().contextProperty("timeScreen").now())
    started["app"].processEvents()


def test_the_dial_counts_on_while_the_clock_counts(started):
    import time as clock_time
    _view(started, text="Küche · 2:15", short="2:15", state="active", clock="runs",
          counter={"prefix": "Küche · ", "shortPrefix": "", "since": clock_time.time() - (2 * 3600 + 15 * 60 + 7)})
    [dial] = _named(started, "nowDial")
    assert dial.property("running") is True
    assert abs(dial.property("seconds") - (2 * 3600 + 15 * 60 + 7)) < 3
    assert dial.property("wedgeAngle") == pytest.approx(15 / 60 * 360, abs=1)


def test_standing_the_dial_stands(started):
    _view(started, text="Küche · 0:15 · gestoppt", short="0:15 · gestoppt", state="calm", clock="stopped")
    [dial] = _named(started, "nowDial")
    assert dial.property("running") is False and dial.property("seconds") == 15 * 60


def test_now_says_for_whom_it_counts(started):
    [person] = _named(started, "nowPerson")
    assert person.property("text") == "Oliver"


def test_stopped_is_said_in_the_dial_and_no_line_repeats_the_time(started):
    _view(started, text="Küche · 0:15 · gestoppt", short="0:15 · gestoppt", state="calm", clock="stopped")
    [stopped] = _named(started, "dialStopped")
    assert stopped.property("visible") and stopped.property("text") == "stopped"
    assert _named(started, "nowText") == []
    _view(started, text="Küche · 0:15", short="0:15", state="calm", clock="paused")
    assert not _named(started, "dialStopped")[0].property("visible")  # a pause is no stop
