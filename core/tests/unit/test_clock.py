"""The clock of the time tracking (core/clock.py, "Designdocument Time.md", section 4): it counts
while one works in the active project, stops after the pause limit without input (the idle
minutes do not count), asks when only a video runs (the dead man's button), can be stopped and
started by hand, and survives a crash. No Qt, no system: the time, the idle time and the
writer are handed in."""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from core import clock as ck
from core import time_log as tl

T0 = datetime(2026, 11, 16, 9, 0)
KITCHEN = Path("/p/Küche")
HUBER = Path("/p/Huber")


def at(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


def idle(minutes: float) -> timedelta:
    return timedelta(minutes=minutes)


class Writer:
    def __init__(self):
        self.written = []
        self.failing = False

    def __call__(self, project, person, stretch):
        if self.failing:
            raise OSError("cloud folder not there")
        self.written.append((project, person, stretch))

    def stretches(self):
        return [(p, s.start, s.duration, s.kind) for p, _person, s in self.written]


@pytest.fixture
def writer():
    return Writer()


@pytest.fixture
def clock(writer, tmp_path):
    return ck.Clock(writer=writer, store=tmp_path / "clock.json")


def minutes(m):
    return timedelta(minutes=m)


# --- counting --------------------------------------------------------------------------------

def test_without_a_project_the_clock_stands(clock, writer):
    clock.tick(at(1), idle(0))
    assert clock.state == "stands" and writer.written == []


def test_it_counts_in_the_active_project_until_one_switches(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    for m in range(1, 30):
        clock.tick(at(m), idle(0.2))
    clock.set_project(HUBER, "Oliver", at(30))
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(30), "auto")]
    assert writer.written[0][1] == "Oliver"
    assert clock.state == "runs" and clock.project == HUBER


def test_after_the_pause_limit_it_stops_at_the_last_input(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(10), idle(0))
    clock.tick(at(16), idle(6))  # last input at 9:10, the limit is 5 minutes
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(10), "auto")]
    assert clock.state == "paused"


def test_the_next_input_resumes_in_the_same_project(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(10), idle(0))
    clock.tick(at(16), idle(6))
    clock.tick(at(60), idle(50))  # lunch
    clock.tick(at(75), idle(0.5))  # back at 10:14:30
    assert clock.state == "runs"
    clock.set_project(None, "Oliver", at(80))
    assert writer.stretches()[-1] == (KITCHEN, time(10, 14, 30), timedelta(minutes=5, seconds=30), "auto")


def test_without_automatic_resume_it_waits_for_a_click(writer, tmp_path):
    clock = ck.Clock(writer=writer, store=tmp_path / "c.json", settings=ck.ClockSettings(auto_resume=False))
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(16), idle(16))
    clock.tick(at(30), idle(0))
    assert clock.state == "paused"
    clock.start(at(31))
    clock.stop(at(41))
    assert writer.stretches()[-1] == (KITCHEN, time(9, 31), minutes(10), "manual")


def test_the_pause_limit_is_a_setting(writer, tmp_path):
    clock = ck.Clock(writer=writer, store=tmp_path / "c.json", settings=ck.ClockSettings(pause=minutes(10)))
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(8), idle(8))
    assert clock.state == "runs"


def test_a_stretch_does_not_run_over_midnight(clock, writer):
    late = datetime(2026, 11, 16, 23, 30)
    clock.set_project(KITCHEN, "Oliver", late)
    clock.tick(late + minutes(45), idle(0))
    clock.set_project(None, "Oliver", late + minutes(60))
    assert [(s.day, s.start, s.duration) for _p, _o, s in writer.written] == [
        (date(2026, 11, 16), time(23, 30), minutes(30)), (date(2026, 11, 17), time(0, 0), minutes(30))]


def test_a_glance_into_a_project_is_not_time(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.set_project(HUBER, "Oliver", at(0.5))  # passing through
    clock.set_project(None, "Oliver", at(20))
    assert [p for p, *_ in writer.stretches()] == [HUBER]


# --- video and the dead man's button ---------------------------------------------------------

def test_with_a_video_it_asks_instead_of_stopping(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(6), idle(6), inhibited=True)
    assert clock.state == "asks" and writer.written == []


def test_yes_keeps_counting_and_it_asks_again_after_the_next_limit(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(6), idle(6), inhibited=True)
    clock.answer(True, at(6.5))
    clock.tick(at(10), idle(10), inhibited=True)
    assert clock.state == "runs"
    clock.tick(at(12), idle(12), inhibited=True)
    assert clock.state == "asks"


def test_no_ends_the_stretch_when_it_asked(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(6), idle(6), inhibited=True)
    clock.answer(False, at(7))
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(6), "auto")]
    assert clock.state == "paused"


def test_no_answer_within_two_minutes_is_a_no(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(6), idle(6), inhibited=True)
    clock.tick(at(7), idle(7), inhibited=True)
    assert clock.state == "asks"
    clock.tick(at(8.5), idle(8.5), inhibited=True)
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(6), "auto")]


def test_an_input_while_it_asks_is_a_yes(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(6), idle(6), inhibited=True)
    clock.tick(at(7), idle(0.1), inhibited=True)
    assert clock.state == "runs" and writer.written == []


def test_without_the_dead_mans_button_a_video_does_not_count(writer, tmp_path):
    clock = ck.Clock(writer=writer, store=tmp_path / "c.json", settings=ck.ClockSettings(dead_man=False))
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(3), idle(0))
    clock.tick(at(9), idle(6), inhibited=True)
    assert clock.state == "paused" and writer.stretches() == [(KITCHEN, time(9, 0), minutes(3), "auto")]


# --- by hand -----------------------------------------------------------------------------------

def test_stopped_by_hand_it_stays_stopped_even_with_input(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.stop(at(20))
    clock.tick(at(25), idle(0))
    clock.set_project(HUBER, "Oliver", at(26))
    assert clock.state == "stopped" and clock.project == HUBER
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(20), "auto")]


def test_started_by_hand_it_counts_as_manual_and_the_pause_limit_still_applies(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.stop(at(20))
    clock.start(at(30))
    clock.tick(at(40), idle(0))
    clock.tick(at(46), idle(6))
    assert writer.stretches()[-1] == (KITCHEN, time(9, 30), minutes(10), "manual")


def test_start_without_a_project_does_nothing(clock, writer):
    clock.start(at(0))
    assert clock.state == "stands"


# --- what the top bar shows --------------------------------------------------------------------

def test_the_view_for_the_button(clock):
    assert clock.view(at(0)) == {"state": "stands", "project": None, "running": timedelta(0)}
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(30), idle(0))
    view = clock.view(at(30))
    assert view["state"] == "runs" and view["project"] == KITCHEN and view["running"] == minutes(30)


# --- a crash, a cloud folder away ----------------------------------------------------------------

def test_after_a_crash_the_stretch_is_closed_at_its_last_activity(writer, tmp_path):
    store = tmp_path / "clock.json"
    first = ck.Clock(writer=writer, store=store)
    first.set_project(KITCHEN, "Oliver", at(0))
    for m in range(1, 41):
        first.tick(at(m), idle(0))
    # the computer goes off; hours later
    second = ck.Clock(writer=writer, store=store)
    second.recover(at(300))
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(40), "auto")]
    assert second.state == "paused" and second.project == KITCHEN


def test_the_store_is_not_written_more_than_each_minute(writer, tmp_path):
    store = tmp_path / "clock.json"
    clock = ck.Clock(writer=writer, store=store)
    clock.set_project(KITCHEN, "Oliver", at(0))
    written = store.stat().st_mtime_ns
    saved = json.loads(store.read_text())
    clock.tick(at(0.25), idle(0))
    assert json.loads(store.read_text()) == saved
    clock.tick(at(1.25), idle(0))
    assert json.loads(store.read_text()) != saved


def test_a_stretch_the_project_cannot_take_now_is_kept_and_written_later(writer, clock):
    clock.set_project(KITCHEN, "Oliver", at(0))
    writer.failing = True
    clock.set_project(HUBER, "Oliver", at(10))
    assert writer.written == [] and len(clock.pending) == 1
    writer.failing = False
    clock.tick(at(11), idle(0))
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(10), "auto")] and clock.pending == []


def test_pending_stretches_survive_a_crash(writer, tmp_path):
    store = tmp_path / "clock.json"
    first = ck.Clock(writer=writer, store=store)
    first.set_project(KITCHEN, "Oliver", at(0))
    writer.failing = True
    first.set_project(None, "Oliver", at(10))
    writer.failing = False
    second = ck.Clock(writer=writer, store=store)
    second.recover(at(60))
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(10), "auto")]


# --- settings ----------------------------------------------------------------------------------

def test_the_settings_come_from_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from core.settings import Settings
    settings = Settings()
    assert ck.ClockSettings.from_settings(settings) == ck.ClockSettings()
    settings.set("Time/pauseMinutes", 10)
    settings.set("Time/deadMan", False)
    settings.set("Time/roundStep", "15")
    assert ck.ClockSettings.from_settings(settings).pause == minutes(10)
    assert ck.ClockSettings.from_settings(settings).dead_man is False
    assert ck.rounding_from_settings(settings) == tl.Rounding(step=15)


def test_the_writer_writes_the_persons_file(tmp_path):
    write = ck.file_writer(language="de")
    stretch = tl.Stretch(day=date(2026, 11, 16), start=time(9, 0), duration=minutes(30), kind="auto")
    write(tmp_path, "Oliver", stretch)
    assert tl.read(tl.time_file(tmp_path, "Oliver")).stretches == [stretch]


def test_a_stretch_no_project_can_ever_take_is_dropped(clock):
    def refuse(project, person, stretch):
        raise ValueError("outside the projects")
    clock.writer = refuse
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.set_project(None, "Oliver", at(10))
    assert clock.pending == []


def test_when_the_clock_ends_the_stretch_closes_at_the_last_activity(clock, writer):
    clock.set_project(KITCHEN, "Oliver", at(0))
    clock.tick(at(20), idle(2))
    clock.pause_now()
    assert writer.stretches() == [(KITCHEN, time(9, 0), minutes(18), "auto")]
    assert clock.state == "paused"
