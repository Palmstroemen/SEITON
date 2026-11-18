"""The time screen (Time/model.py; Designdocument Time.md, 5): Now, Entries, Overview - the
time tracking's own window, with the person's own rights. No Qt here; its window only draws it.
It talks to the running clock as the Headline does: it reads the clock's view and drops
commands (core/clock_widget.py)."""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from core import clock_sources as cs
from core import time_log as tl
from core.brand import META_DIR, env_name

TODAY = date(2026, 11, 17)


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# SEITON Project\n")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("ACL_USER"), "Oliver")
    root = _project(tmp_path / "Projekte")
    haus = _project(root / "Haus")
    kueche = _project(haus / "Küche")
    for project, person, day, minutes in ((haus, "Oliver", TODAY, 30), (kueche, "Oliver", TODAY, 90),
                                          (kueche, "Oliver", TODAY - timedelta(days=40), 60),
                                          (kueche, "Liesl", TODAY, 45)):
        tl.add(project, person, tl.Stretch(day=day, start=time(9, 0), duration=timedelta(minutes=minutes),
                                           kind="auto"), language="de")
    active = tmp_path / "run" / "seiton" / "active-project.json"
    cs.write_active(active, kueche, "Oliver")
    return {"root": root, "haus": haus, "kueche": kueche, "active": active,
            "widget": tmp_path / "run" / "seiton-clock"}


@pytest.fixture
def model(world):
    from Time.model import TimeModel
    return TimeModel(active=world["active"], widget=world["widget"], today=lambda: TODAY)


def test_now_without_the_clock(model, world):
    now = model.now()
    assert now["project"] == str(world["kueche"]) and now["projectName"] == "Küche"
    assert now["clockRuns"] is False


def test_now_with_the_clock(model, world):
    world["widget"].mkdir(parents=True)
    (world["widget"] / "view.json").write_text(json.dumps({"text": "Küche · 1:30", "state": "active", "items": []}))
    now = model.now()
    assert now["clockRuns"] and now["text"] == "Küche · 1:30" and now["state"] == "active"


def test_start_and_stop_go_to_the_clock(model, world):
    assert model.start() and model.stop()
    names = sorted(p.name.split("-", 1)[1] for p in (world["widget"] / "commands").iterdir())
    assert names == ["start", "stop"]


def test_the_entries_of_the_active_project_newest_first(model):
    rows = model.entries()
    assert [(r["day"], r["minutes"]) for r in rows] == [("2026-11-17", 90), ("2026-10-08", 60)]
    assert rows[0]["start"] == "09:00" and rows[0]["kind"] == "auto"


def test_entries_of_another_project(model, world):
    assert [r["minutes"] for r in model.entries(str(world["haus"]))] == [30]


def test_adding_what_was_done_away(model):
    assert model.add({"day": "2026-11-17", "start": "", "minutes": 90, "note": "Baumarkt"})
    added = model.entries()[0]
    assert added["kind"] == "added" and added["note"] == "Baumarkt" and added["minutes"] == 90


def test_correcting_a_row(model):
    row = model.entries()[0]
    assert model.change(row, {**row, "minutes": 100})
    changed = model.entries()[0]
    assert changed["minutes"] == 100 and changed["kind"] == "corrected"


def test_taking_a_row_away(model):
    assert model.remove(model.entries()[1])
    assert [r["minutes"] for r in model.entries()] == [90]


@pytest.mark.parametrize("row", [
    {"day": "gestern", "start": "", "minutes": 5},
    {"day": "2026-11-17", "start": "25:00", "minutes": 5},
    {"day": "2026-11-17", "start": "", "minutes": -5},
    {"day": "2026-11-17", "start": "", "minutes": 24 * 60 + 1},
])
def test_nonsense_is_not_written(model, row):
    assert not model.add(row)


def test_the_overview_with_the_children(model, world):
    view = model.overview(str(world["haus"]), period="all")
    assert view["total"] == "3:45"
    assert {p["name"]: p["time"] for p in view["byProject"]} == {"Haus": "0:30", "Küche": "3:15"}
    assert {p["name"]: p["time"] for p in view["byPerson"]} == {"Oliver": "3:00", "Liesl": "0:45"}


def test_the_overview_of_a_period_and_a_person(model, world):
    view = model.overview(str(world["haus"]), period="week", person="Oliver")
    assert view["total"] == "2:00"
    view = model.overview(str(world["haus"]), period="month")
    assert view["total"] == "2:45"  # the row of 40 days ago is out


def test_the_overview_is_rounded_as_set(model, world, monkeypatch):
    from core.settings import Settings
    Settings().set("Time/roundStep", "30")
    Settings().set("Time/roundMode", "up")
    view = model.overview(str(world["haus"]), period="all")
    assert view["total"] == "4:00"  # 0:30 + 1:30 + 1:00 + 1:00 (0:45 up to 1:00)


def test_adding_to_a_project_that_is_gone_makes_no_ghost(model, world):
    # X1 (review 2026-11-18): renamed while the active project still names the old place.
    world["kueche"].rename(world["haus"] / "Küche neu")
    assert model.add({"day": "2026-11-17", "start": "", "minutes": 30, "note": "Baumarkt"}) is False
    assert not world["kueche"].exists()


# --- the person's rights under enforce (review 2026-11-18, A7, A14) -------------------------

FIRMA_ACLS = ("# Permissions\n\n"
              "## Everyone\n- /0_Admin/Zeitaufwand/{Self}.md: read, write\n\n"
              "## Chef\n- /*: *\n\n"
              "## Buchhaltung\n- /4_Finanz/: read, write\n\n"
              "# Users\nOliver: Chef\nAnna: Buchhaltung\n")


def _stretch(minutes):
    return tl.Stretch(day=TODAY, start=time(9, 0), duration=timedelta(minutes=minutes), kind="auto")


@pytest.fixture
def firma(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("ACL_MODE"), "enforce")
    monkeypatch.delenv(env_name("ACL_BACKEND"), raising=False)
    root = _project(tmp_path / "Firma")
    (root / META_DIR / "ACLs.md").write_text(FIRMA_ACLS)
    geheim = _project(root / "Geheimkunde Huber")
    tl.add(root, "Oliver", _stretch(420), language="de")
    tl.add(root, "Anna", _stretch(30), language="de")
    tl.add(geheim, "Oliver", _stretch(120), language="de")
    active = tmp_path / "run" / "seiton" / "active-project.json"
    cs.write_active(active, root, "Anna")
    from Time.model import TimeModel
    return {"root": root, "active": active,
            "model": TimeModel(active=active, widget=tmp_path / "run" / "seiton-clock", today=lambda: TODAY)}


def test_the_overview_shows_only_what_the_person_may_read(firma, monkeypatch):
    # A7: everyone saw every colleague's hours and the hidden subprojects.
    monkeypatch.setenv(env_name("ACL_USER"), "anna")
    view = firma["model"].overview(period="month")
    assert view["byPerson"] == [{"name": "Anna", "time": "0:30"}]
    assert [p["name"] for p in view["byProject"]] == ["Firma"] and view["total"] == "0:30"
    monkeypatch.setenv(env_name("ACL_USER"), "oliver")
    assert {p["name"] for p in firma["model"].overview(period="month")["byPerson"]} == {"Anna", "Oliver"}


def test_without_the_right_to_write_nothing_is_added(firma, monkeypatch):
    # A14: it wrote where Scope and the clock's drive refuse.
    (firma["root"] / META_DIR / "ACLs.md").write_text(
        "# Permissions\n\n## Buchhaltung\n- /4_Finanz/: read, write\n\n# Users\nAnna: Buchhaltung\n")
    monkeypatch.setenv(env_name("ACL_USER"), "anna")
    model = firma["model"]
    assert model.add({"day": "2026-11-17", "start": "", "minutes": 30, "note": "Baumarkt"}) is False
    assert model.change({"day": "2026-11-17", "start": "09:00", "minutes": 30, "kind": "auto", "note": ""},
                        {"day": "2026-11-17", "start": "09:00", "minutes": 45, "kind": "auto", "note": ""}) is False
    assert model.remove({"day": "2026-11-17", "start": "09:00", "minutes": 30, "kind": "auto", "note": ""}) is False
    assert tl.read(tl.time_file(firma["root"], "Anna")).stretches == [_stretch(30)]


def test_with_the_right_to_write_ones_own_file_it_adds(firma, monkeypatch):
    monkeypatch.setenv(env_name("ACL_USER"), "anna")
    assert firma["model"].add({"day": "2026-11-17", "start": "", "minutes": 30, "note": "Baumarkt"}) is True


def test_ones_own_rows_need_the_right_to_read_them(firma, monkeypatch):
    monkeypatch.setenv(env_name("ACL_USER"), "anna")
    assert len(firma["model"].entries()) == 1
    (firma["root"] / META_DIR / "ACLs.md").write_text(
        "# Permissions\n\n## Buchhaltung\n- /4_Finanz/: read, write\n\n# Users\nAnna: Buchhaltung\n")
    assert firma["model"].entries() == []
