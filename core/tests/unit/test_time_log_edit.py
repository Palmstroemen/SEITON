"""Correcting one's time (core/time_log.py; Designdocument Time.md, 5): a row is changed or
taken away by the time screen, with the person's own rights - not by the clock. The file is
written anew and swapped in; everything else in it stays as it was."""

from datetime import date, time, timedelta

import pytest

from core import time_log as tl


def _s(day, minutes, start=None, kind="auto", note=""):
    return tl.Stretch(day=day, start=start, duration=timedelta(minutes=minutes), kind=kind, note=note)


@pytest.fixture
def log(tmp_path):
    path = tmp_path / "Küche" / tl.TIME_DIR / "Oliver.md"
    for stretch in (_s(date(2026, 11, 16), 50, time(9, 0)), _s(date(2026, 11, 16), 30, time(14, 0)),
                    _s(date(2026, 11, 17), 90, None, "manual", "Baumarkt")):
        tl.add_to_file(path, "Oliver", stretch, language="de")
    text = path.read_text(encoding="utf-8")
    path.write_text("Vorher ein Satz.\n\n" + text + "\nDanach ein Satz.\n", encoding="utf-8")
    return path


def test_a_row_is_changed(log):
    old = _s(date(2026, 11, 16), 30, time(14, 0))
    new = _s(date(2026, 11, 16), 45, time(14, 0), "manual", "länger")
    assert tl.change(log, old, new)
    assert tl.read(log).stretches[1] == new
    text = log.read_text(encoding="utf-8")
    assert text.startswith("Vorher ein Satz.") and text.rstrip().endswith("Danach ein Satz.")


def test_a_row_is_taken_away(log):
    assert tl.remove(log, _s(date(2026, 11, 17), 90, None, "manual", "Baumarkt"))
    assert [s.duration for s in tl.read(log).stretches] == [timedelta(minutes=50), timedelta(minutes=30)]


def test_a_row_not_there_changes_nothing(log):
    before = log.read_text(encoding="utf-8")
    assert not tl.remove(log, _s(date(2026, 11, 1), 5))
    assert not tl.change(log, _s(date(2026, 11, 1), 5), _s(date(2026, 11, 1), 6))
    assert log.read_text(encoding="utf-8") == before


def test_of_two_equal_rows_only_the_first(log):
    tl.add_to_file(log, "Oliver", _s(date(2026, 11, 16), 50, time(9, 0)), language="de")
    assert tl.remove(log, _s(date(2026, 11, 16), 50, time(9, 0)))
    assert [s.duration for s in tl.read(log).stretches].count(timedelta(minutes=50)) == 1


def test_no_file_nothing_to_change(tmp_path):
    assert not tl.remove(tmp_path / "nichts.md", _s(date(2026, 11, 16), 5))
