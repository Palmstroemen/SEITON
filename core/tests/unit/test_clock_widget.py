"""The clock as the Headline's first widget (core/clock_widget.py; Scope/Designdocument
Headline.md, 3a): it keeps a small ledger of what it counted, writes its view - "Küche · 2:15",
grey when it stands, its question when it asks, the projects worked on last - and takes the
commands the Headline drops."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from core import clock as ck
from core import clock_widget as cw

NOW = datetime(2026, 11, 17, 11, 0)


@pytest.fixture
def ledger(tmp_path):
    return cw.Ledger(tmp_path / "ledger.json")


def test_the_ledger_sums_a_project_per_day(ledger):
    ledger.add(Path("/p/Küche"), NOW.date(), timedelta(minutes=50))
    ledger.add(Path("/p/Küche"), NOW.date(), timedelta(minutes=25))
    ledger.add(Path("/p/Küche"), NOW.date() - timedelta(days=1), timedelta(hours=3))
    assert ledger.on(Path("/p/Küche"), NOW.date()) == timedelta(minutes=75)


def test_the_ledger_is_kept(tmp_path, ledger):
    ledger.add(Path("/p/Küche"), NOW.date(), timedelta(minutes=50))
    ledger.seen(Path("/p/Küche"), NOW)
    again = cw.Ledger(tmp_path / "ledger.json")
    assert again.on(Path("/p/Küche"), NOW.date()) == timedelta(minutes=50)
    assert again.recent() == [Path("/p/Küche")]


def test_the_projects_worked_on_last_come_first(ledger):
    ledger.seen(Path("/p/Auto"), NOW - timedelta(hours=3))
    ledger.seen(Path("/p/Dachboden"), NOW - timedelta(hours=2))
    ledger.seen(Path("/p/Küche"), NOW - timedelta(hours=1))
    ledger.seen(Path("/p/Auto"), NOW)
    assert ledger.recent() == [Path("/p/Auto"), Path("/p/Küche"), Path("/p/Dachboden")]


def test_old_days_and_many_projects_are_forgotten(ledger):
    for i in range(30):
        ledger.seen(Path(f"/p/P{i}"), NOW - timedelta(minutes=30 - i))
    ledger.add(Path("/p/P29"), NOW.date() - timedelta(days=40), timedelta(hours=1))
    assert len(ledger.recent()) == cw.KEEP_PROJECTS
    assert ledger.on(Path("/p/P29"), NOW.date() - timedelta(days=40)) == timedelta(0)


def _clock(tmp_path, ledger):
    return ck.Clock(writer=cw.counting(lambda p, person, s: None, ledger), store=tmp_path / "c.json")


def test_what_the_clock_writes_goes_into_the_ledger(tmp_path, ledger):
    clock = _clock(tmp_path, ledger)
    clock.set_project(Path("/p/Küche"), "Oliver", NOW - timedelta(minutes=40))
    clock.set_project(Path("/p/Huber"), "Oliver", NOW)
    assert ledger.on(Path("/p/Küche"), NOW.date()) == timedelta(minutes=40)


def test_the_view_while_it_runs(tmp_path, ledger):
    clock = _clock(tmp_path, ledger)
    ledger.add(Path("/p/Küche"), NOW.date(), timedelta(hours=2))
    clock.set_project(Path("/p/Küche"), "Oliver", NOW - timedelta(minutes=15))
    view = cw.render(clock, ledger, NOW, language="de")
    assert view["text"] == "Küche · 2:15" and view["state"] == "active"
    assert "question" not in view


def test_the_view_while_it_stands_is_calm(tmp_path, ledger):
    clock = _clock(tmp_path, ledger)
    clock.set_project(Path("/p/Küche"), "Oliver", NOW - timedelta(minutes=15))
    clock.stop(NOW)
    view = cw.render(clock, ledger, NOW, language="de")
    assert view["state"] == "calm" and view["text"] == "Küche · 0:15"


def test_without_a_project(tmp_path, ledger):
    view = cw.render(_clock(tmp_path, ledger), ledger, NOW, language="en")
    assert view["state"] == "calm" and view["text"] == "No project"


def test_while_it_asks_the_question(tmp_path, ledger):
    clock = _clock(tmp_path, ledger)
    clock.set_project(Path("/p/Küche"), "Oliver", NOW - timedelta(minutes=10))
    clock.state = "asks"
    view = cw.render(clock, ledger, NOW, language="de")
    assert view["state"] == "asking"
    assert view["question"]["text"] == "Arbeitest du noch an Küche?"
    assert [a["id"] for a in view["question"]["answers"]] == ["yes", "no"]


def test_the_projects_worked_on_last_with_their_time_today(tmp_path, ledger):
    clock = _clock(tmp_path, ledger)
    for name, minutes in (("Auto", 20), ("Dachboden", 160), ("Küche", 150)):
        ledger.add(Path(f"/p/{name}"), NOW.date(), timedelta(minutes=minutes))
        ledger.seen(Path(f"/p/{name}"), NOW - timedelta(minutes=200 - minutes))
    items = cw.render(clock, ledger, NOW, language="de")["items"]
    assert [i["text"] for i in items] == ["Dachboden · 2:40", "Küche · 2:30", "Auto · 0:20"]
    assert items[0]["path"] == "/p/Dachboden"


def test_the_view_file_is_what_the_headline_reads(tmp_path, ledger, monkeypatch):
    from Headline import widgets

    folder = tmp_path / "seiton-clock"
    cw.write_view(folder, cw.render(_clock(tmp_path, ledger), ledger, NOW, language="en"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    widgets.widgets_dir().mkdir(parents=True)
    (widgets.widgets_dir() / "clock.json").write_text(json.dumps(cw.registration(folder, ["seiton-time"])))
    [shown] = widgets.shown()
    assert shown["text"] == "No project" and shown["state"] == "calm"


def test_the_commands_dropped_are_taken_once_in_order(tmp_path):
    commands = tmp_path / "seiton-clock" / "commands"
    commands.mkdir(parents=True)
    for stamp, name in ((2, "stop"), (1, "yes"), (3, "rm"), (4, "start")):
        (commands / f"{stamp}-{name}").write_text("")
    assert cw.take_commands(tmp_path / "seiton-clock") == ["yes", "stop", "start"]
    assert list(commands.iterdir()) == []
    assert cw.take_commands(tmp_path / "seiton-clock") == []


def test_a_command_moves_the_clock(tmp_path, ledger):
    clock = _clock(tmp_path, ledger)
    clock.set_project(Path("/p/Küche"), "Oliver", NOW - timedelta(minutes=10))
    cw.obey(clock, "stop", NOW)
    assert clock.state == "stopped"
    cw.obey(clock, "start", NOW)
    assert clock.state == "runs"
    clock.state = "asks"
    cw.obey(clock, "yes", NOW)
    assert clock.state == "runs"


# --- the time shown beside the projects worked on last (decided 2026-11-17: in all, settable) --

def _file(tmp_path, project, rows):
    from core import time_log as tl
    for day, minutes in rows:
        tl.add(project, "Oliver", tl.Stretch(day=day, start=None, duration=timedelta(minutes=minutes),
                                            kind="manual"), language="de")


@pytest.fixture
def projects(tmp_path):
    folders = {}
    for name in ("Küche", "Dachboden"):
        folder = tmp_path / "Projekte" / name
        folder.mkdir(parents=True)
        folders[name] = folder
    monday = NOW.date() - timedelta(days=NOW.weekday())
    _file(tmp_path, folders["Küche"], [(NOW.date() - timedelta(days=40), 600), (monday, 60), (NOW.date(), 30)])
    _file(tmp_path, folders["Dachboden"], [(NOW.date() - timedelta(days=3), 760)])
    return folders


def test_in_all_from_the_projects_time_file(projects, ledger):
    spent = cw.spent_from(lambda project, person: cw.tl.time_file(project, person))
    assert spent(projects["Küche"], "Oliver", "total", NOW.date()) == timedelta(minutes=690)
    assert spent(projects["Küche"], "Oliver", "today", NOW.date()) == timedelta(minutes=30)
    assert NOW.weekday() == 1  # a Tuesday: Monday's hour and today's half belong to the week
    assert spent(projects["Küche"], "Oliver", "week", NOW.date()) == timedelta(minutes=90)


def test_no_file_no_time(tmp_path, ledger):
    spent = cw.spent_from(lambda project, person: cw.tl.time_file(project, person))
    assert spent(tmp_path / "Nichts", "Oliver", "total", NOW.date()) == timedelta(0)


def test_the_list_shows_the_time_in_all(tmp_path, projects, ledger):
    clock = _clock(tmp_path, ledger)
    ledger.seen(projects["Küche"], NOW - timedelta(hours=2), "Oliver")
    ledger.seen(projects["Dachboden"], NOW - timedelta(hours=1), "Oliver")
    spent = cw.spent_from(lambda project, person: cw.tl.time_file(project, person))
    items = cw.render(clock, ledger, NOW, language="de", spent=spent, shows="total")["items"]
    assert [i["text"] for i in items] == ["Dachboden · 12:40", "Küche · 11:30"]


def test_the_running_stretch_counts_too(tmp_path, projects, ledger):
    clock = _clock(tmp_path, ledger)
    ledger.seen(projects["Küche"], NOW, "Oliver")
    clock.set_project(projects["Küche"], "Oliver", NOW - timedelta(minutes=10))
    spent = cw.spent_from(lambda project, person: cw.tl.time_file(project, person))
    items = cw.render(clock, ledger, NOW, language="de", spent=spent, shows="total")["items"]
    assert items[0]["text"] == "Küche · 11:40"


def test_what_the_list_shows_is_a_setting():
    from core.settings import SETTINGS
    kind, default, allowed = SETTINGS["Time/recentShows"]
    assert default == "total" and allowed == {"total", "week", "today"}
