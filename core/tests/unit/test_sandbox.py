"""A program with a role in its sandbox (core/sandbox.py, core/role_drive.py; "Designdocument
Time.md" 7.2): SEITON mounts a drive of the program's own, without fallback, whose every access
the role and the person's ACLs must both allow, and starts the program with bubblewrap. Inside
it sees, of the projects, only what its role names; no home, no X11, a cleared environment.
The command is built and looked at here, not run."""

from pathlib import Path

import pytest

from core import programs as pg
from core import role_drive as rd
from core import sandbox as sb
from core.brand import META_DIR

CLOCK = pg.role_for("seiton-clock", pg.parse(pg.DEFAULT))


@pytest.fixture
def place(tmp_path):
    return sb.Place(home=Path("/home/anna"), runtime=Path("/run/user/1000"),
                    dbus="unix:path=/run/user/1000/bus", keep=[Path("/home/anna/SEITON")],
                    hide=[tmp_path, tmp_path / "not there"])


def _pairs(command, option):
    return [(command[i + 1], command[i + 2]) for i, part in enumerate(command) if part == option]


def test_the_sandbox_shuts_out_what_the_program_does_not_need(place):
    command = sb.command(["python3", "-m", "daemon.clock_daemon"], place=place, binds=[])
    assert command[0] == "bwrap"
    for option in ("--unshare-all", "--die-with-parent", "--new-session", "--clearenv", "--as-pid-1"):
        assert option in command
    tmpfs = [command[i + 1] for i, part in enumerate(command) if part == "--tmpfs"]
    assert {"/home/anna", "/run/user/1000", "/tmp", str(place.hide[0])} <= set(tmpfs)
    assert str(place.hide[1]) not in tmpfs
    assert command[-3:] == ["python3", "-m", "daemon.clock_daemon"]


def test_no_x11_and_no_display(place):
    command = sb.command(["true"], place=place, binds=[])
    text = " ".join(command)
    assert "X11" not in text and "DISPLAY" not in text and "WAYLAND" not in text
    assert "/tmp" in [command[i + 1] for i, part in enumerate(command) if part == "--tmpfs"]  # hides /tmp/.X11-unix


def test_the_session_bus_comes_along(place):
    command = sb.command(["true"], place=place, binds=[])
    assert ("/run/user/1000/bus", "/run/user/1000/bus") in _pairs(command, "--ro-bind")
    assert ("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus") in _pairs(command, "--setenv")


def test_an_abstract_bus_cannot_come_along(place):
    place = sb.Place(home=place.home, runtime=place.runtime, dbus="unix:abstract=/tmp/dbus-x", keep=[], hide=[])
    command = sb.command(["true"], place=place, binds=[])
    assert "DBUS_SESSION_BUS_ADDRESS" not in command


def test_the_code_is_read_only_after_the_home_is_hidden(place):
    command = sb.command(["true"], place=place, binds=[])
    home_hidden = command.index("/home/anna")
    code = _pairs(command, "--ro-bind").index(("/home/anna/SEITON", "/home/anna/SEITON"))
    assert code >= 0 and command.index("/home/anna/SEITON") > home_hidden


def test_the_roles_folders_from_its_drive(tmp_path):
    binds = sb.role_binds(CLOCK, mount=Path("/run/user/1000/seiton/drives/seiton-clock"))
    assert binds == [sb.Bind(Path("/run/user/1000/seiton/drives/seiton-clock/0_Admin/Zeitaufwand"),
                             sb.INSIDE / "0_Admin" / "Zeitaufwand", writable=True)]
    viewer = pg.Role("Bildbetrachter", "eog", [("/9_Dokumentation/92_Bilder", frozenset({"read"}))])
    assert not sb.role_binds(viewer, mount=Path("/m"))[0].writable


def test_binds_are_given_in_order(place):
    binds = [sb.Bind(Path("/m/0_Admin/Zeitaufwand"), sb.INSIDE / "0_Admin" / "Zeitaufwand", True),
             sb.Bind(Path("/s"), sb.INSIDE / "state", True), sb.Bind(Path("/r"), sb.INSIDE / "run", False)]
    command = sb.command(["true"], place=place, binds=binds)
    assert ("/m/0_Admin/Zeitaufwand", str(sb.INSIDE / "0_Admin" / "Zeitaufwand")) in _pairs(command, "--bind")
    assert ("/r", str(sb.INSIDE / "run")) in _pairs(command, "--ro-bind")
    assert command.index("/m/0_Admin/Zeitaufwand") > command.index("/tmp")  # after /tmp is a tmpfs


# --- the drive of the program: role and ACLs ------------------------------------------------

def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# Project\n")
    return path


def test_the_drive_asks_the_role_and_the_acls(tmp_path):
    root = tmp_path / "Projekte"
    huber = _project(root / "Huber")
    asked = []

    def acls(action, path):
        asked.append((action, path))
        return path.name != "Ben.md"

    may = rd.role_may(CLOCK, root, acls)
    assert may(huber / "0_Admin" / "Zeitaufwand" / "Anna.md", "write")
    assert not may(huber / "0_Admin" / "Zeitaufwand" / "Ben.md", "write")  # the ACLs say no
    assert not may(huber / "0_Admin" / "01_Ziele", "read")  # the role says no
    assert ("read", huber / "0_Admin" / "01_Ziele") not in asked  # the role asked first


def test_the_clock_reaches_a_project_through_its_drive(tmp_path):
    root = tmp_path / "Projekte"
    write = rd.drive_writer(sb.INSIDE / "0_Admin" / "Zeitaufwand", root, language="de", add=lambda *a, **k: a)
    path, person, _stretch = write(root / "Firma" / "7_Arbeit" / "Kunde Huber", "Anna", "stretch")
    assert path == sb.INSIDE / "0_Admin" / "Zeitaufwand" / "Projekte" / "Firma" / "7_Arbeit" / "Kunde Huber" / "Anna.md"
    with pytest.raises(ValueError):  # never writable: the clock drops it, it does not wait
        write(tmp_path / "elsewhere", "Anna", "stretch")
    with pytest.raises(ValueError):
        write(root / "Firma", "../Ben", "stretch")


def test_a_projects_root_inside_the_code_stays_hidden(tmp_path):
    code = tmp_path / "SEITON"
    projects = code / "SEITON_Test" / "Projekte"
    projects.mkdir(parents=True)
    place = sb.Place(home=tmp_path, runtime=Path("/run/user/1000"), dbus="", keep=[code], hide=[projects])
    command = sb.command(["true"], place=place, binds=[])
    assert command.index(str(projects)) > command.index(str(code))  # the tmpfs comes after the code


def test_the_launcher_learns_the_programs_pid(place):
    command = sb.command(["true"], place=place, binds=[], info_fd=7)
    assert command[command.index("--info-fd") + 1] == "7"
    assert command.index("--info-fd") < command.index("--")


def test_the_code_inside_the_projects_root_comes_back(tmp_path):
    # The Dell (2026-11-17): the repository lies in ~/Dokumente/SEITON, inside the projects root
    # ~/Dokumente the clock must not see - hidden after the code, it hid the clock's own program.
    projects = tmp_path / "Dokumente"
    code = projects / "SEITON"
    code.mkdir(parents=True)
    place = sb.Place(home=tmp_path, runtime=Path("/run/user/1000"), dbus="", keep=[code], hide=[projects])
    args = sb.command(["python3", "x.py"], place=place, binds=[])
    hidden = args.index(str(projects))
    kept = max(i for i, a in enumerate(args) if a == str(code) and args[i - 1] == "--ro-bind")
    assert args[hidden - 1] == "--tmpfs" and hidden < kept  # the root hidden first, the code back over it
