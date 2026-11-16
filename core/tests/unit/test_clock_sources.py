"""What the clock is told by the system (core/clock_sources.py, "Designdocument Time.md" 4.2,
4.3): the idle time (how long no input came, never which input), whether a program keeps the
screensaver away (a video), and the active project, which the top bar writes into a small file.
The commands are recorded, not run: the tests do not touch the desktop."""

from datetime import timedelta
from pathlib import Path

import pytest

from core import clock_sources as cs


class Bus:
    """Answers gdbus calls from a table: (dest, method) -> output, or missing (an error)."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def __call__(self, command):
        self.calls.append(command)
        dest = command[command.index("--dest") + 1]
        method = command[command.index("--method") + 1]
        answer = self.answers.get((dest, method))
        if answer is None:
            return 1, ""
        return 0, answer


# --- reading gdbus ---------------------------------------------------------------------------

@pytest.mark.parametrize("output, value", [
    ("(uint64 19195,)\n", 19195), ("(uint32 5,)", 5), ("(false,)", False), ("(true,)", True),
])
def test_gdbus_answers_are_read(output, value):
    assert cs.gdbus_value(output) == value


def test_an_answer_one_cannot_read_is_none():
    assert cs.gdbus_value("Error: org.freedesktop.DBus.Error.ServiceUnknown") is None


# --- idle time -------------------------------------------------------------------------------

def test_cinnamons_idle_monitor_counts_milliseconds():
    bus = Bus({("org.cinnamon.Muffin.IdleMonitor", "org.cinnamon.Muffin.IdleMonitor.GetIdletime"): "(uint64 19195,)"})
    assert cs.MUFFIN.idle(bus) == timedelta(milliseconds=19195)


def test_the_freedesktop_screensaver_counts_seconds():
    bus = Bus({("org.freedesktop.ScreenSaver", "org.freedesktop.ScreenSaver.GetSessionIdleTime"): "(uint32 42,)"})
    assert cs.FREEDESKTOP.idle(bus) == timedelta(seconds=42)


def test_a_service_that_is_not_there_gives_no_idle_time():
    assert cs.MUTTER.idle(Bus({})) is None


def test_the_first_source_that_answers_is_kept():
    bus = Bus({("org.freedesktop.ScreenSaver", "org.freedesktop.ScreenSaver.GetSessionIdleTime"): "(uint32 3,)"})
    idle = cs.IdleTime([cs.MUTTER, cs.MUFFIN, cs.FREEDESKTOP], run=bus)
    assert idle() == timedelta(seconds=3)
    bus.calls.clear()
    assert idle() == timedelta(seconds=3)
    assert len(bus.calls) == 1  # no more asking the others


def test_when_no_source_answers_the_idle_time_is_unknown():
    assert cs.IdleTime([cs.MUTTER, cs.MUFFIN], run=Bus({}))() is None


def test_the_order_follows_the_desktop():
    assert cs.idle_sources("X-Cinnamon", "x11")[0] is cs.MUFFIN
    assert cs.idle_sources("GNOME", "wayland")[0] is cs.MUTTER
    assert cs.idle_sources("KDE", "wayland")[0] is cs.FREEDESKTOP
    assert cs.X11 in cs.idle_sources("XFCE", "x11")
    assert cs.X11 not in cs.idle_sources("GNOME", "wayland")


def test_x11_without_its_library_gives_no_idle_time():
    assert cs.X11Idle(load=lambda name: None).idle(None) is None


# --- a video ---------------------------------------------------------------------------------

def test_the_session_manager_says_whether_idle_is_inhibited():
    method = ("org.gnome.SessionManager", "org.gnome.SessionManager.IsInhibited")
    assert cs.Inhibited(run=Bus({method: "(true,)"}))() is True
    bus = Bus({method: "(false,)"})
    assert cs.Inhibited(run=bus)() is False
    assert bus.calls[0][-1] == "8"  # the flag "idle"


def test_kde_tells_it_by_power_management():
    method = ("org.freedesktop.PowerManagement", "org.freedesktop.PowerManagement.Inhibit.HasInhibit")
    assert cs.Inhibited(run=Bus({method: "(true,)"}))() is True


def test_without_any_answer_nothing_is_inhibited():
    assert cs.Inhibited(run=Bus({}))() is False


# --- the active project ----------------------------------------------------------------------

def test_the_top_bar_writes_the_active_project_and_the_clock_reads_it(tmp_path):
    place = tmp_path / "active-project.json"
    cs.write_active(place, Path("/p/Küche"), "Oliver")
    assert cs.read_active(place) == (Path("/p/Küche"), "Oliver")
    cs.write_active(place, None, "")
    assert cs.read_active(place) == (None, "")


@pytest.mark.parametrize("text", [None, "", "{", '{"project": 3}', '["x"]'])
def test_no_or_a_broken_file_is_no_project(tmp_path, text):
    place = tmp_path / "active-project.json"
    if text is not None:
        place.write_text(text)
    assert cs.read_active(place) == (None, "")


def test_the_file_lies_in_the_runtime_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    assert cs.active_file() == tmp_path / "seiton" / "active-project.json"
