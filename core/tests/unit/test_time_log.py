"""The time spent on a project (core/time_log.py, "Designdocument Time.md"): one file per person
in 0_Admin/Zeitaufwand, a Markdown table of when a stretch began and how long it lasted (no
"To": redundant, and confusing when summer time begins or ends), in German or English; a parent
collects the time of its children; rounding only in the sums, never in the file."""

from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from core import time_log as tl
from core.brand import META_DIR


def _project(folder: Path) -> Path:
    (folder / META_DIR).mkdir(parents=True, exist_ok=True)
    (folder / META_DIR / "Project.md").write_text("# Project\n", encoding="utf-8")
    return folder


def _stretch(day=date(2026, 11, 16), start=time(9, 12), minutes=148, kind="auto", note=""):
    return tl.Stretch(day=day, start=start, duration=timedelta(minutes=minutes), kind=kind, note=note)


GERMAN = """# Zeitaufwand Oliver

| Datum      | Von   | Dauer | Art          | Notiz    |
|------------|-------|-------|--------------|----------|
| 2026-11-16 | 09:12 | 2:28  | auto         |          |
| 2026-11-16 | 13:05 | 1:30  | nachgetragen | Baumarkt |
| 2026-11-17 |       | 0:45  | nachgetragen | Telefonat mit Huber |
"""


# --- where ---------------------------------------------------------------------------------

def test_each_person_has_a_file_in_0_admin(tmp_path):
    assert tl.time_file(tmp_path / "Küche", "Oliver") == tmp_path / "Küche" / "0_Admin" / "Zeitaufwand" / "Oliver.md"


@pytest.mark.parametrize("name", ["", "../Anna", "a/b", ".hidden"])
def test_a_person_is_no_path(tmp_path, name):
    with pytest.raises(ValueError):
        tl.time_file(tmp_path, name)


# --- reading -------------------------------------------------------------------------------

def test_reading_the_german_file():
    log = tl.parse(GERMAN)
    assert log.language == "de" and not log.problems
    assert log.stretches[0] == _stretch()
    assert log.stretches[1] == _stretch(start=time(13, 5), minutes=90, kind="added", note="Baumarkt")
    assert log.stretches[2].start is None and log.stretches[2].duration == timedelta(minutes=45)


def test_reading_the_english_file_with_columns_in_another_order():
    text = ("| Note | Date | Time | From | Kind |\n|---|---|---|---|---|\n"
            "| call | 2026-11-16 | 1:05 | 08:00 | manual |\n")
    log = tl.parse(text)
    assert log.language == "en"
    assert log.stretches == [_stretch(start=time(8, 0), minutes=65, kind="manual", note="call")]


def test_a_start_away_from_home_carries_its_offset():
    text = "| Datum | Von | Dauer | Art | Notiz |\n|-|-|-|-|-|\n| 2026-08-01 | 09:12+09:00 | 1:00 | auto | |\n"
    stretch = tl.parse(text).stretches[0]
    assert stretch.start == time(9, 12) and stretch.offset == timedelta(hours=9)


def test_a_row_one_cannot_read_is_named_not_dropped_silently():
    text = GERMAN + "| gestern | 09:00 | lang | auto | |\n"
    log = tl.parse(text)
    assert len(log.stretches) == 3
    assert len(log.problems) == 1 and "gestern" in log.problems[0]


def test_a_pipe_in_a_note_survives():
    text = tl.render("Oliver", [_stretch(note="Küche | Bad")], "de")
    assert tl.parse(text).stretches[0].note == "Küche | Bad"


def test_no_file_is_no_time(tmp_path):
    assert tl.read(tmp_path / "nothing.md").stretches == []


# --- writing -------------------------------------------------------------------------------

def test_render_writes_the_columns_of_the_language():
    text = tl.render("Oliver", [_stretch(kind="added")], "de")
    assert text.startswith("# Zeitaufwand Oliver\n")
    assert "| Datum | Von | Dauer | Art | Notiz |" in text and "Bis" not in text
    assert "| 2026-11-16 | 09:12 | 2:28 | nachgetragen |  |" in text
    english = tl.render("Oliver", [_stretch(kind="corrected")], "en")
    assert "| Date | From | Time | Kind | Note |" in english and "| corrected |" in english


def test_the_first_stretch_makes_the_file_in_the_users_language(tmp_path):
    path = tl.add(tmp_path, "Oliver", _stretch(), language="en")
    assert path == tl.time_file(tmp_path, "Oliver")
    assert tl.read(path).language == "en" and tl.read(path).stretches == [_stretch()]


def test_adding_keeps_the_files_language_and_what_was_written_by_hand(tmp_path):
    path = tl.time_file(tmp_path, "Oliver")
    path.parent.mkdir(parents=True)
    path.write_text(GERMAN + "\nNotiz von Hand unter der Tabelle.\n", encoding="utf-8")
    tl.add(tmp_path, "Oliver", _stretch(day=date(2026, 11, 18), minutes=10), language="en")
    text = path.read_text(encoding="utf-8")
    assert text.startswith(GERMAN.rstrip("\n") + "\n| 2026-11-18 | 09:12 | 0:10 | auto |  |\n")
    assert text.endswith("Notiz von Hand unter der Tabelle.\n")


def test_durations_over_ten_hours_and_without_start(tmp_path):
    long = tl.Stretch(day=date(2026, 11, 16), start=None, duration=timedelta(hours=11, minutes=5),
                      kind="added", note="")
    assert tl.parse(tl.render("Oliver", [long], "de")).stretches == [long]


# --- the day and the gaps ------------------------------------------------------------------

def test_a_stretch_does_not_run_over_midnight():
    parts = tl.split_days(datetime(2026, 11, 16, 23, 30), timedelta(hours=2), kind="auto")
    assert [(p.day, p.start, p.duration) for p in parts] == [
        (date(2026, 11, 16), time(23, 30), timedelta(minutes=30)),
        (date(2026, 11, 17), time(0, 0), timedelta(minutes=90)),
    ]


def test_short_gaps_join_one_row():
    first = _stretch(start=time(9, 0), minutes=30)
    near = _stretch(start=time(9, 30, 40), minutes=10)
    far = _stretch(start=time(10, 30), minutes=10)
    joined = tl.join_gaps([first, near, far], gap=timedelta(minutes=1))
    assert [(s.start, s.duration) for s in joined] == [
        (time(9, 0), timedelta(minutes=40, seconds=40)), (time(10, 30), timedelta(minutes=10))]


def test_only_stretches_of_the_same_kind_join():
    joined = tl.join_gaps([_stretch(start=time(9, 0), minutes=30),
                           _stretch(start=time(9, 30), minutes=5, kind="added")])
    assert len(joined) == 2


def test_the_file_counts_whole_minutes():
    odd = tl.Stretch(day=date(2026, 11, 16), start=time(9, 0, 40),
                     duration=timedelta(minutes=40, seconds=40), kind="auto", note="")
    text = tl.render("Oliver", [odd], "de")
    assert "| 09:00 | 0:41 |" in text  # a begun minute counts; the seconds stay out of the file


# --- parents and children ------------------------------------------------------------------

@pytest.fixture
def firm(tmp_path):
    firma = _project(tmp_path / "Firma")
    huber = _project(firma / "7_Arbeit" / "Kunde Huber")
    kitchen = _project(huber / "7_Arbeit" / "Küche")
    tl.add(firma, "Oliver", _stretch(minutes=60), language="de")
    tl.add(huber, "Oliver", _stretch(minutes=30), language="de")
    tl.add(huber, "Anna", _stretch(minutes=15), language="de")
    tl.add(kitchen, "Anna", _stretch(minutes=45), language="de")
    return firma, huber, kitchen


def test_a_parent_collects_its_children_down_to_the_grandchild(firm):
    firma, huber, kitchen = firm
    entries = tl.collect(firma)
    assert tl.total(entries) == timedelta(minutes=150)
    assert tl.total(tl.collect(huber)) == timedelta(minutes=90)
    assert tl.total(tl.collect(kitchen)) == timedelta(minutes=45)


def test_each_entry_knows_its_project_and_person(firm):
    firma, huber, kitchen = firm
    by_project = tl.sums(tl.collect(firma), by="project")
    assert by_project == {firma: timedelta(minutes=60), huber: timedelta(minutes=45),
                          kitchen: timedelta(minutes=45)}
    assert tl.sums(tl.collect(firma), by="person") == {"Oliver": timedelta(minutes=90),
                                                       "Anna": timedelta(minutes=60)}


def test_own_time_only(firm):
    firma, huber, _kitchen = firm
    assert tl.total(tl.collect(huber, children=False)) == timedelta(minutes=45)


def test_hidden_folders_and_other_files_are_not_time(firm):
    firma, _huber, _kitchen = firm
    folder = tl.time_file(firma, "x").parent
    (folder / "Liesmich.txt").write_text("not time")
    hidden = _project(firma / ".Papierkorb" / "Alt")
    tl.add(hidden, "Oliver", _stretch(minutes=999), language="de")
    assert tl.total(tl.collect(firma)) == timedelta(minutes=150)


def test_a_conflict_copy_of_the_cloud_is_read_and_shown(firm):
    firma, _huber, _kitchen = firm
    original = tl.time_file(firma, "Oliver")
    copy = original.with_name("Oliver (conflicted copy 2026-11-16 101112).md")
    copy.write_text(tl.render("Oliver", [_stretch(day=date(2026, 11, 17), minutes=20)], "de"), encoding="utf-8")
    own = tl.collect(firma, children=False)
    assert {e.person for e in own} == {"Oliver"}
    assert [e.conflict for e in own] == [False, True]
    assert tl.conflicts(firma) == [copy]


def test_filters(firm):
    firma, _huber, _kitchen = firm
    entries = tl.collect(firma)
    assert tl.total(tl.only(entries, person="Anna")) == timedelta(minutes=60)
    assert tl.only(entries, since=date(2026, 11, 17)) == []
    assert len(tl.only(entries, until=date(2026, 11, 16), kinds={"auto"})) == 4


# --- rounding ------------------------------------------------------------------------------

@pytest.mark.parametrize("rounding, expected", [
    (tl.Rounding(), 7 + 22),
    (tl.Rounding(step=15, mode="up", per="stretch"), 15 + 30),
    (tl.Rounding(step=15, mode="nearest", per="stretch"), 0 + 15),
    (tl.Rounding(step=15, mode="up", per="day"), 30),
    (tl.Rounding(step=10, mode="nearest", per="day"), 30),
])
def test_rounding_happens_in_the_sum(rounding, expected):
    entries = [tl.Entry(stretch=_stretch(minutes=7), person="Oliver", project=Path("/p")),
               tl.Entry(stretch=_stretch(start=time(14, 0), minutes=22), person="Oliver", project=Path("/p"))]
    assert tl.total(entries, rounding) == timedelta(minutes=expected)


def test_rounding_per_day_rounds_each_day_and_person():
    a = tl.Entry(stretch=_stretch(minutes=7), person="Oliver", project=Path("/p"))
    b = tl.Entry(stretch=_stretch(day=date(2026, 11, 17), minutes=7), person="Oliver", project=Path("/p"))
    c = tl.Entry(stretch=_stretch(minutes=7), person="Anna", project=Path("/p"))
    assert tl.total([a, b, c], tl.Rounding(step=15, mode="up", per="day")) == timedelta(minutes=45)


def test_unknown_rounding_is_refused():
    with pytest.raises(ValueError):
        tl.Rounding(step=7)
    with pytest.raises(ValueError):
        tl.Rounding(step=15, mode="down")
