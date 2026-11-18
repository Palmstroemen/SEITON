"""Widgets in the Headline (apps/Headline/widgets.py; apps/Scope/Designdocument Headline.md, 3a): other
programs - the time tracking first - put themselves in. A widget registers with a small file,
shows what its view file says, is told by command files, and opens its own screen. Missing,
broken or stale, it shows nothing."""

import json
import os
import time
from pathlib import Path

import pytest

from apps.Headline import widgets


@pytest.fixture
def clock(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    folder = tmp_path / "run" / "seiton-clock"
    folder.mkdir(parents=True)
    registered = widgets.widgets_dir()
    registered.mkdir(parents=True)
    (registered / "clock.json").write_text(json.dumps({
        "name": "Time", "folder": str(folder), "open": ["seiton-time"],
        "commands": ["start", "stop"], "staleAfter": 60}))
    return folder


def _view(folder, **view):
    (folder / "view.json").write_text(json.dumps(view))


def test_a_registered_widget_shows_its_view(clock):
    _view(clock, text="Küche · 2:15", state="active", tooltip="Since 9:00")
    [shown] = widgets.shown()
    assert shown["id"] == "clock" and shown["name"] == "Time"
    assert shown["text"] == "Küche · 2:15" and shown["state"] == "active" and shown["tooltip"] == "Since 9:00"


def test_no_view_or_a_broken_one_shows_nothing(clock):
    assert widgets.shown() == []
    (clock / "view.json").write_text("{not json")
    assert widgets.shown() == []


def test_a_stale_view_shows_nothing(clock):
    _view(clock, text="Küche · 2:15", state="active")
    old = time.time() - 120
    os.utime(clock / "view.json", (old, old))
    assert widgets.shown() == []


def test_a_question_with_its_answers(clock):
    _view(clock, text="Küche · 2:15", state="asking",
          question={"text": "Still working on Küche?", "answers": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}]})
    [shown] = widgets.shown()
    assert shown["question"]["text"] == "Still working on Küche?"
    assert [a["id"] for a in shown["question"]["answers"]] == ["yes", "no"]


def test_a_short_list_of_recent_ones(clock, tmp_path):
    items = [{"text": f"Projekt {i} · 0:{i}0", "path": str(tmp_path / f"P{i}")} for i in range(5)]
    _view(clock, text="x", state="calm", items=items)
    [shown] = widgets.shown()
    assert len(shown["items"]) == 5 and shown["items"][0]["path"] == str(tmp_path / "P0")


@pytest.mark.parametrize("view", [
    {"text": 5, "state": "calm"},
    {"text": "x", "state": "shouting"},
    {"text": "x" * 500, "state": "calm"},
])
def test_what_does_not_fit_the_shape_is_refused(clock, view):
    _view(clock, **view)
    assert widgets.shown() == []


def test_list_entries_must_be_real_paths(clock):
    _view(clock, text="x", state="calm", items=[{"text": "a", "path": "relative/x"}, {"text": "b", "path": "/abs"}])
    [shown] = widgets.shown()
    assert [i["text"] for i in shown["items"]] == ["b"]


def test_an_answer_is_dropped_as_a_command_file(clock):
    _view(clock, text="x", state="asking", question={"text": "?", "answers": [{"id": "yes", "label": "Yes"}]})
    assert widgets.tell("clock", "yes")
    assert [p.name.split("-", 1)[1] for p in (clock / "commands").iterdir()] == ["yes"]


def test_a_declared_command_too(clock):
    _view(clock, text="x", state="calm")
    assert widgets.tell("clock", "stop")


def test_nothing_else_is_told(clock):
    _view(clock, text="x", state="calm")
    assert not widgets.tell("clock", "rm -rf")
    assert not widgets.tell("clock", "yes")  # no question asks it
    assert not widgets.tell("nobody", "start")
    assert not (clock / "commands").exists()


def test_a_click_opens_its_own_screen(clock):
    _view(clock, text="x", state="calm")
    started = []
    assert widgets.open_screen("clock", start=started.append)
    assert started == [["seiton-time"]]


@pytest.mark.parametrize("registration", [
    {"name": "Time", "folder": "relative", "open": ["x"]},
    {"name": "Time", "folder": "/tmp/x", "open": "not a list"},
    {"name": 3, "folder": "/tmp/x", "open": ["x"]},
])
def test_a_broken_registration_is_left_out(tmp_path, monkeypatch, registration):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    widgets.widgets_dir().mkdir(parents=True)
    (widgets.widgets_dir() / "w.json").write_text(json.dumps(registration))
    assert widgets.registered() == {}


def test_a_counter_the_headline_counts_on(clock):
    _view(clock, text="Küche · 2:15", state="active", counter={"prefix": "Küche · ", "since": 1000.5})
    [shown] = widgets.shown()
    assert shown["counter"] == {"prefix": "Küche · ", "since": 1000.5}


@pytest.mark.parametrize("counter", [{"prefix": 5, "since": 1}, {"prefix": "x", "since": "1"},
                                     {"prefix": "x" * 200, "since": 1}, "running"])
def test_a_broken_counter_is_left_out(clock, counter):
    _view(clock, text="Küche · 2:15", state="active", counter=counter)
    [shown] = widgets.shown()
    assert shown["counter"] is None and shown["text"] == "Küche · 2:15"


def test_seconds_shown():
    assert widgets.counted({"prefix": "Küche · ", "since": 1000.0}, now=1000.0 + 2 * 3600 + 15 * 60 + 7) == "Küche · 2:15:07"
    assert widgets.counted({"prefix": "", "since": 1000.0}, now=999.0) == "0:00:00"


# --- its project once (2026-11-18): the project already stands at the left of the line ---------

def test_in_its_project_a_widget_shows_its_short_text(clock):
    _view(clock, text="Küche · 2:15", state="active", project="/p/Küche", short="2:15",
          counter={"prefix": "Küche · ", "shortPrefix": "", "since": 1000.5})
    [shown] = widgets.shown(here="/p/Küche")
    assert shown["text"] == "2:15" and shown["counter"]["prefix"] == ""
    assert shown["tooltip"] == "Küche"  # which project, on hovering


def test_elsewhere_it_names_its_project(clock):
    _view(clock, text="Küche · 2:15", state="active", project="/p/Küche", short="2:15",
          counter={"prefix": "Küche · ", "shortPrefix": "", "since": 1000.5})
    [shown] = widgets.shown(here="/p/Auto")
    assert shown["text"] == "Küche · 2:15" and shown["counter"]["prefix"] == "Küche · "
    [shown] = widgets.shown()
    assert shown["text"] == "Küche · 2:15"


def test_its_own_tooltip_stays_as_it_is(clock):
    _view(clock, text="Küche · 0:15 · gestoppt", state="calm", project="/p/Küche", short="0:15 · gestoppt",
          tooltip="Küche: stopped by hand.")
    [shown] = widgets.shown(here="/p/Küche")
    assert shown["text"] == "0:15 · gestoppt" and shown["tooltip"] == "Küche: stopped by hand."


@pytest.mark.parametrize("project", ["Küche", 5, None])
def test_a_project_that_is_no_path_keeps_the_long_text(clock, project):
    _view(clock, text="Küche · 2:15", state="active", project=project, short="2:15")
    [shown] = widgets.shown(here="Küche")
    assert shown["text"] == "Küche · 2:15"


# --- an icon in the CWD's tab instead of a button (2026-11-18) ---------------------------------

def test_a_widget_may_show_as_a_known_icon(clock):
    _view(clock, text="Küche · 2:15", state="active", icon="stopwatch")
    [shown] = widgets.shown()
    assert shown["icon"] == "stopwatch" and shown["warn"] is False


@pytest.mark.parametrize("icon", ["rocket", "../x", 5, None])
def test_an_unknown_icon_is_none(clock, icon):
    _view(clock, text="Küche · 2:15", state="active", icon=icon)
    [shown] = widgets.shown()
    assert shown["icon"] == ""


def test_a_widget_may_warn(clock):
    _view(clock, text="Küche · 0:15", state="calm", icon="stopwatch", warn=True)
    assert widgets.shown()[0]["warn"] is True
    _view(clock, text="Küche · 0:15", state="calm", icon="stopwatch", warn="yes")
    assert widgets.shown()[0]["warn"] is False


def test_in_its_project_the_short_tooltip(clock):
    _view(clock, text="Küche · 2:15", state="active", project="/p/Küche", short="2:15",
          tooltip="Küche: heute 2:15 h", shortTooltip="heute 2:15 h")
    assert widgets.shown(here="/p/Küche")[0]["tooltip"] == "heute 2:15 h"
    assert widgets.shown(here="/p/Auto")[0]["tooltip"] == "Küche: heute 2:15 h"


# --- off: registered with an icon, but no view (no clock runs) (2026-11-18) ---------------------

def _register_icon(clock, icon="stopwatch"):
    registration = json.loads((widgets.widgets_dir() / "clock.json").read_text())
    registration["icon"] = icon
    (widgets.widgets_dir() / "clock.json").write_text(json.dumps(registration))


def test_without_a_view_a_widget_with_an_icon_shows_off(clock):
    _register_icon(clock)
    [shown] = widgets.shown()
    assert shown["state"] == "off" and shown["icon"] == "stopwatch" and shown["id"] == "clock"
    assert shown["question"] is None and shown["counter"] is None and shown["warn"] is False


def test_a_stale_view_too(clock):
    _register_icon(clock)
    _view(clock, text="Küche · 2:15", state="active", icon="stopwatch")
    old = time.time() - 120
    os.utime(clock / "view.json", (old, old))
    assert widgets.shown()[0]["state"] == "off"


def test_without_an_icon_nothing_as_before(clock):
    assert widgets.shown() == []


def test_an_unknown_icon_in_the_registration_is_none(clock):
    _register_icon(clock, icon="rocket")
    assert widgets.shown() == []


def test_with_a_view_it_shows_the_view(clock):
    _register_icon(clock)
    _view(clock, text="Küche · 2:15", state="active", icon="stopwatch")
    assert widgets.shown()[0]["state"] == "active"
