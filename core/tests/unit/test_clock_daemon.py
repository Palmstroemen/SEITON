"""seiton-clock running (daemon/clock_daemon.py) and started with its role (cli/seiton_clock.py):
each step reads the active project the top bar wrote, then the idle time; the launcher gives the
sandbox the role's folders from the drive, the clock's state and the active project (read only),
and nothing else. Built and looked at here; nothing is mounted or started."""

import importlib.util
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest

from core import clock as ck
from core import clock_sources as cs
from core import sandbox as sb

REPO = Path(__file__).resolve().parents[3]


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


daemon = _load("daemon/clock_daemon.py", "clock_daemon_under_test")
launcher = _load("cli/seiton_clock.py", "seiton_clock_under_test")


class Now:
    def __init__(self):
        self.value = datetime(2026, 11, 16, 9, 0)

    def __call__(self):
        return self.value


@pytest.fixture
def service(tmp_path):
    written = []
    clock = ck.Clock(writer=lambda p, person, s: written.append((p, person, s)), store=tmp_path / "c.json")
    now = Now()
    idle = {"value": timedelta(0)}
    active = tmp_path / "active-project.json"
    svc = daemon.ClockService(clock, active=active, idle=lambda: idle["value"], inhibited=lambda: False, now=now)
    return svc, written, now, idle, active


def test_a_step_follows_the_active_project(service):
    svc, written, now, _idle, active = service
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    assert svc.clock.state == "runs" and svc.clock.project == Path("/p/Küche")
    now.value += timedelta(minutes=20)
    cs.write_active(active, Path("/p/Huber"), "Oliver")
    svc.step()
    assert [(p, s.start, s.duration) for p, _o, s in written] == [(Path("/p/Küche"), time(9, 0), timedelta(minutes=20))]


def test_a_step_sees_the_pause(service):
    svc, written, now, idle, active = service
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    now.value += timedelta(minutes=16)
    idle["value"] = timedelta(minutes=6)
    svc.step()
    assert svc.clock.state == "paused" and written[0][2].duration == timedelta(minutes=10)


def test_without_an_idle_source_it_still_follows_the_project(service):
    svc, written, now, idle, active = service
    svc.idle = lambda: None
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    now.value += timedelta(minutes=30)
    svc.step()
    assert svc.clock.state == "runs"


def test_the_launcher_gives_the_sandbox_the_role_state_and_active_project(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    from core.settings import Settings
    place = sb.Place(home=tmp_path / "home", runtime=tmp_path / "run", dbus="unix:path=/run/user/1000/bus")
    mount = launcher.drive_place(str(tmp_path / "run"))
    command = launcher.sandboxed(tmp_path / "Projekte", python="/usr/bin/python3", settings=Settings(),
                                 mount=mount, place=place)
    pairs = {(command[i], command[i + 1], command[i + 2]) for i in range(len(command) - 2)}
    assert ("--bind", str(mount / "0_Admin" / "Zeitaufwand"), str(sb.INSIDE / "0_Admin" / "Zeitaufwand")) in pairs
    assert ("--bind", str(tmp_path / "state" / "seiton"), str(sb.INSIDE / "state")) in pairs
    assert ("--ro-bind", str(tmp_path / "run" / "seiton"), str(sb.INSIDE / "run")) in pairs
    # the drive itself lies apart from the folder the sandbox gets
    assert tmp_path / "run" / "seiton" not in mount.parents
    program = command[command.index("--") + 1:]
    assert program[:2] == ["/usr/bin/python3", str(REPO / "daemon" / "clock_daemon.py")]
    assert program[program.index("--drive") + 1] == str(sb.INSIDE / "0_Admin" / "Zeitaufwand")
    assert program[program.index("--pause") + 1] == "5.0"


def test_the_settings_reach_the_clock(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from core.settings import Settings
    settings = Settings()
    settings.set("Time/autoResume", False)
    settings.set("Time/pauseMinutes", 8)
    args = launcher.clock_arguments(settings)
    assert "--no-resume" in args and args[args.index("--pause") + 1] == "8.0"


def test_the_launcher_sees_when_it_may_not_mount(tmp_path):
    """A process with no_new_privs (started from a sandboxed tool) cannot run the setuid
    fusermount: the launcher says so before it tries."""
    status = tmp_path / "status"
    status.write_text("Name:\tpython3\nNoNewPrivs:\t1\nSeccomp:\t0\n")
    assert launcher.no_new_privs(status) is True
    status.write_text("Name:\tpython3\nNoNewPrivs:\t0\n")
    assert launcher.no_new_privs(status) is False
    assert launcher.no_new_privs(tmp_path / "missing") is False


def test_the_launcher_stops_with_a_clear_sentence_under_no_new_privs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(launcher, "no_new_privs", lambda *a: True)
    monkeypatch.setattr(launcher.shutil, "which", lambda name: "/usr/bin/" + name)
    started = []
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: started.append(a))
    monkeypatch.setattr(launcher, "Settings", lambda: None)
    assert launcher.run(tmp_path, sandbox=True) == 1
    assert started == []
    assert "no_new_privs" in capsys.readouterr().err


# --- the clock as the Headline's widget (core/clock_widget.py; Designdocument Headline.md, 3a) -

@pytest.fixture
def widget_service(tmp_path):
    from core import clock_widget as cw

    ledger = cw.Ledger(tmp_path / "ledger.json")
    clock = ck.Clock(writer=cw.counting(lambda p, person, s: None, ledger), store=tmp_path / "c.json")
    now = Now()
    active = tmp_path / "active-project.json"
    widget = daemon.Widget(folder=tmp_path / "seiton-clock", ledger=ledger, language="de")
    svc = daemon.ClockService(clock, active=active, idle=lambda: timedelta(0), inhibited=lambda: False,
                              now=now, widget=widget)
    return svc, now, active, tmp_path / "seiton-clock"


def _view(folder):
    import json
    return json.loads((folder / "view.json").read_text(encoding="utf-8"))


def test_every_step_writes_the_view(widget_service):
    svc, now, active, folder = widget_service
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    now.value += timedelta(minutes=15)
    svc.step()
    view = _view(folder)
    assert view["text"] == "Küche · 0:15" and view["state"] == "active"
    assert view["items"][0]["path"] == "/p/Küche"  # worked on last


def test_a_dropped_command_is_obeyed_at_once(widget_service):
    svc, now, active, folder = widget_service
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    (folder / "commands").mkdir(parents=True, exist_ok=True)
    (folder / "commands" / "1-stop").write_text("")
    assert svc.listen() is True
    assert svc.clock.state == "stopped" and _view(folder)["state"] == "calm"
    assert svc.listen() is False  # taken once


def test_the_sandbox_may_write_the_widgets_folder_and_nothing_more(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    from core.settings import Settings
    place = sb.Place(home=tmp_path / "home", runtime=tmp_path / "run", dbus="unix:path=/run/user/1000/bus")
    mount = launcher.drive_place(str(tmp_path / "run"))
    command = launcher.sandboxed(tmp_path / "Projekte", python="/usr/bin/python3", settings=Settings(),
                                 mount=mount, place=place)
    pairs = {(command[i], command[i + 1], command[i + 2]) for i in range(len(command) - 2)}
    assert ("--bind", str(tmp_path / "run" / "seiton-clock"), str(sb.INSIDE / "widget")) in pairs
    program = command[command.index("--") + 1:]
    assert program[program.index("--widget") + 1] == str(sb.INSIDE / "widget")


def test_what_the_recent_list_shows_reaches_the_clock(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from core.settings import Settings
    args = launcher.clock_arguments(Settings())
    assert args[args.index("--recent") + 1] == "total"
    Settings().set("Time/recentShows", "week")
    args = launcher.clock_arguments(Settings())
    assert args[args.index("--recent") + 1] == "week"
