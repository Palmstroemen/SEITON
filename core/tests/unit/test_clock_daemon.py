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


def _run(svc, now, minutes, idle=None, idle_from=None):
    """Steps every 15 seconds, as the daemon makes them (a longer gap is a sleep, Z1);
    idle_from: the minute of the last input, from then on the idle time grows."""
    start = now.value
    for k in range(1, int(minutes * 4) + 1):
        now.value = start + timedelta(seconds=15 * k)
        if idle is not None and idle_from is not None:
            idle["value"] = max(timedelta(0), now.value - (start + timedelta(minutes=idle_from)))
        svc.step()


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
    _run(svc, now, 20 - 0.25)
    now.value += timedelta(seconds=15)
    cs.write_active(active, Path("/p/Huber"), "Oliver")
    svc.step()
    assert [(p, s.start, s.duration) for p, _o, s in written] == [(Path("/p/Küche"), time(9, 0), timedelta(minutes=20))]


def test_a_step_sees_the_pause(service):
    svc, written, now, idle, active = service
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    _run(svc, now, 16, idle=idle, idle_from=10)
    assert svc.clock.state == "paused" and written[0][2].duration == timedelta(minutes=10)


def test_without_an_idle_source_it_still_follows_the_project(service):
    svc, written, now, idle, active = service
    svc.idle = lambda: None
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    _run(svc, now, 30)
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
    _run(svc, now, 15)
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


# --- started at login or from the time screen (step 2a, part 4) --------------------------------

def test_without_a_root_it_takes_the_first_below_the_home(tmp_path):
    from core.brand import META_DIR
    (tmp_path / "Dokumente" / META_DIR).mkdir(parents=True)
    (tmp_path / "Dokumente" / META_DIR / "Project.md").write_text("x")
    assert launcher.default_root(tmp_path) == tmp_path / "Dokumente"
    assert launcher.default_root(tmp_path / "Dokumente") is None  # nothing below a root itself


def test_the_start_without_a_root_runs_on_the_found_one(tmp_path, monkeypatch):
    found = tmp_path / "Dokumente"
    monkeypatch.setattr(launcher, "default_root", lambda home=None: found)
    started = []
    monkeypatch.setattr(launcher, "run", lambda root, sandbox=True: started.append((root, sandbox)) or 0)
    monkeypatch.setattr(launcher, "hold_lock", lambda folder: object())
    assert launcher.main([]) == 0
    assert started == [(found, True)]


def test_without_any_root_it_says_so(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "default_root", lambda home=None: None)
    monkeypatch.setattr(launcher, "hold_lock", lambda folder: object())
    assert launcher.main([]) == 1
    assert "--projects-root" in capsys.readouterr().err


def test_one_clock_per_user(tmp_path):
    first = launcher.hold_lock(tmp_path / "seiton-clock")
    assert first is not None
    assert launcher.hold_lock(tmp_path / "seiton-clock") is None  # a second start ends
    first.close()
    assert launcher.hold_lock(tmp_path / "seiton-clock") is not None


def test_a_second_start_ends_quietly(monkeypatch):
    monkeypatch.setattr(launcher, "hold_lock", lambda folder: None)
    monkeypatch.setattr(launcher, "run", lambda *a, **k: pytest.fail("started twice"))
    assert launcher.main(["--projects-root", "/tmp"]) == 0


def test_a_switch_right_after_waking_does_not_count_the_night(service):
    # Z1 (review 2026-11-18): the step after a sleep sees another active project.
    svc, written, now, _idle, active = service
    cs.write_active(active, Path("/p/Küche"), "Oliver")
    svc.step()
    _run(svc, now, 10)
    now.value += timedelta(hours=14)
    cs.write_active(active, Path("/p/Huber"), "Oliver")
    svc.step()
    assert [(p, s.duration) for p, _o, s in written] == [(Path("/p/Küche"), timedelta(minutes=10))]
    assert svc.clock.project == Path("/p/Huber") and svc.clock.state == "runs"


def test_a_project_in_another_root_is_not_counted(tmp_path):
    # Z5 (review 2026-11-18): its time could not be written and was dropped after the pause.
    clock = ck.Clock(writer=lambda *a: None, store=tmp_path / "c.json")
    now = Now()
    active = tmp_path / "active-project.json"
    svc = daemon.ClockService(clock, active=active, idle=lambda: timedelta(0), inhibited=lambda: False,
                              now=now, projects_root=Path("/home/o/Dokumente"))
    cs.write_active(active, Path("/home/o/Projekte/Garten"), "Oliver")
    svc.step()
    assert svc.clock.state == "stands" and svc.clock.project is None
    cs.write_active(active, Path("/home/o/Dokumente/Küche"), "Oliver")
    svc.step()
    assert svc.clock.state == "runs" and svc.clock.project == Path("/home/o/Dokumente/Küche")


def test_the_clock_runs_on_time_with_its_zone():
    # Z9: naive local time made the night of the clock change an hour long or short.
    import inspect
    now = inspect.signature(daemon.ClockService).parameters["now"].default
    assert now().tzinfo is not None


def test_through_the_drive_it_writes_only_the_persons_file(tmp_path):
    # Z6: the drive lets the person write {Self}.md, no helper file beside it.
    from datetime import date
    root = tmp_path / "Dokumente"
    drive = tmp_path / "drive"
    folder = drive / "Projekte" / "Küche"
    folder.mkdir(parents=True)
    (folder / "Oliver.md").write_text("", encoding="utf-8")
    writer, _spent = daemon.drive_writers(drive, root, language="de")
    stretch = ck.tl.Stretch(day=date(2026, 11, 16), start=time(9, 0), duration=timedelta(minutes=30), kind="auto")
    folder.chmod(0o555)
    try:
        writer(root / "Küche", "Oliver", stretch)
    finally:
        folder.chmod(0o755)
    assert ck.tl.read(folder / "Oliver.md").stretches == [stretch]
