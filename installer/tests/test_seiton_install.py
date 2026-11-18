"""SEITON's installer (installer/seiton_install.py, started by install.sh): for one user, from the
git folder. System packages through the distribution's package manager, Python packages in a
venv of SEITON's own, launchers, the icon, the menu entry, the templates; on request SunTree at
login and Markdown previews in the file browsers. Everything it writes is listed, so uninstalling
takes exactly that and leaves settings and templates.

The tests never touch the real home: every place lies in tmp_path, commands are recorded, not run.
"""

import os
import stat
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from installer import seiton_install as inst  # noqa: E402


class Runner:
    """Records commands; creating the venv makes its python, a query answers from `installed`."""

    def __init__(self, installed=()):
        self.commands = []
        self.installed = set(installed)

    def __call__(self, command, quiet=False):
        self.commands.append([str(c) for c in command])
        if command[1:3] == ["-m", "venv"]:
            # As a real venv: its python and its pip (the path is the last argument).
            for name in ("python", "pip"):
                made = Path(command[-1]) / "bin" / name
                made.parent.mkdir(parents=True, exist_ok=True)
                made.write_text("")
        query = inst.QUERY.get(self.manager)
        if query and list(command[:len(query)]) == query:
            return 0 if command[-1] in self.installed else 1
        return 0

    manager = "apt"


@pytest.fixture
def places(tmp_path):
    env = {"HOME": str(tmp_path / "home"), "XDG_DATA_HOME": str(tmp_path / "data"),
           "XDG_CONFIG_HOME": str(tmp_path / "config")}
    return inst.Places.from_env(REPO, env)


def _install(places, runner=None, **options):
    runner = runner or Runner(installed=inst.PACKAGES["apt"])
    inst.install(places, inst.Options(**options), run=runner, ask=lambda question: False,
                 which=lambda name: "/usr/bin/apt-get" if name == "apt-get" else None)
    return runner


# --- the places ---------------------------------------------------------------------------

def test_the_places_follow_the_xdg_variables(places, tmp_path):
    assert places.venv == tmp_path / "data" / "seiton" / "venv"
    assert places.bin == tmp_path / "home" / ".local" / "bin"
    assert places.templates == tmp_path / "home" / ".seiton" / "Templates"
    assert places.applications == tmp_path / "data" / "applications"


# --- system packages ----------------------------------------------------------------------

@pytest.mark.parametrize("found, manager", [("apt-get", "apt"), ("dnf", "dnf"), ("zypper", "zypper"),
                                            ("pacman", "pacman"), (None, None)])
def test_the_package_manager_is_found(found, manager):
    assert inst.package_manager(lambda name: f"/usr/bin/{name}" if name == found else None) == manager


def test_every_manager_brings_fuse_2_qt_and_pdf_previews():
    for manager, packages in inst.PACKAGES.items():
        text = " ".join(packages)
        assert "fuse" in text, manager  # libfuse 2 for fusepy
        assert "cursor" in text, manager  # Qt's X11 plugin needs xcb-cursor
        assert "poppler" in text, manager  # pdftoppm: Scope's previews of PDFs
        assert "bubblewrap" in packages, manager  # the clock starts in its sandbox (bwrap)


def test_the_venv_gets_what_the_programs_import():
    """The venv sees no system packages: every library SEITON imports must be listed."""
    listed = (Path(inst.__file__).parent / "requirements.txt").read_text(encoding="utf-8").lower()
    for module, package in (("yaml", "pyyaml"), ("markdown_it", "markdown-it-py"), ("casbin", "casbin"),
                            ("pydantic", "pydantic"), ("PIL", "pillow"), ("fuse", "fusepy"),
                            ("tabulate", "tabulate"), ("PySide6", "pyside6")):
        assert package in listed, (module, package)


def test_only_missing_packages_are_installed_after_asking(places):
    runner = Runner(installed=[p for p in inst.PACKAGES["apt"] if p != "libfuse2"])
    asked = []
    inst.install(places, inst.Options(), run=runner, ask=lambda q: asked.append(q) or True,
                 which=lambda name: "/usr/bin/apt-get" if name == "apt-get" else None)
    install_line = [c for c in runner.commands if c[:3] == ["sudo", "apt-get", "install"]]
    assert install_line == [["sudo", "apt-get", "install", "-y", "libfuse2"]]
    assert any("libfuse2" in q for q in asked)


def test_without_consent_no_sudo(places):
    runner = Runner(installed=[])
    _install(places, runner)
    assert not any(c[0] == "sudo" for c in runner.commands)


# --- python in a venv of its own ------------------------------------------------------------

def test_python_packages_go_into_seitons_own_venv(places):
    runner = _install(places)
    python = str(places.venv / "bin" / "python")
    assert [sys.executable, "-m", "venv", "--clear", str(places.venv)] in runner.commands
    assert [python, "-m", "pip", "install", "-r", str(REPO / "installer" / "requirements.txt")] in runner.commands


def _requirements(name):
    lines = (REPO / "installer" / name).read_text(encoding="utf-8").splitlines()
    return [line.split("#")[0].strip() for line in lines if line.split("#")[0].strip()]


def test_nothing_needs_a_compiler():
    # pynput asks for evdev on Linux, which is only source and needs gcc and kernel headers
    # (Ubuntu 24.04 container, 2026-11-16). SunTree uses pynput's X11 way, which needs
    # python-xlib only: so pynput comes without its own dependencies, these given by hand.
    assert not any(line.startswith("pynput") for line in _requirements("requirements.txt"))
    plain = _requirements("requirements-nodeps.txt")
    assert any(line.startswith("pynput") for line in plain)
    assert not any(line.startswith("evdev") for line in plain + _requirements("requirements.txt"))
    given = _requirements("requirements.txt")
    assert any(line.startswith("python-xlib") for line in given) and any(line.startswith("six") for line in given)


def test_the_packages_without_dependencies_come_after_the_others(places):
    runner = _install(places)
    python = str(places.venv / "bin" / "python")
    with_deps = [python, "-m", "pip", "install", "-r", str(REPO / "installer" / "requirements.txt")]
    plain = [python, "-m", "pip", "install", "--no-deps", "-r", str(REPO / "installer" / "requirements-nodeps.txt")]
    assert with_deps in runner.commands and plain in runner.commands
    assert runner.commands.index(with_deps) < runner.commands.index(plain)


def test_qt_is_pinned_to_one_minor_version():
    lines = (REPO / "installer" / "requirements.txt").read_text(encoding="utf-8").splitlines()
    qt = [line for line in lines if line.startswith("PySide6")]
    assert qt and ">=" in qt[0] and ",<" in qt[0]


# --- launchers, icon, menu ------------------------------------------------------------------

def test_the_launcher_starts_scope_with_the_venv(places):
    _install(places)
    launcher = places.bin / "seiton"
    text = launcher.read_text(encoding="utf-8")
    assert str(places.venv / "bin" / "python") in text and str(REPO / "Scope" / "Scope.py") in text
    assert launcher.stat().st_mode & stat.S_IXUSR


def test_the_cli_tools_and_postfix_get_launchers(places):
    _install(places)
    for name in ("myls", "myproject", "mytag", "myacl"):
        assert str(REPO / "cli" / f"{name}.py") in (places.bin / name).read_text(encoding="utf-8")
    # "postfix" is a mail server's command: ours carries the name
    assert str(REPO / "PostFix" / "cli.py") in (places.bin / "seiton-postfix").read_text(encoding="utf-8")
    assert not (places.bin / "postfix").exists()


def test_the_icon_is_the_box(places):
    _install(places)
    icon = places.data / "icons" / "hicolor" / "scalable" / "apps" / "seiton.svg"
    assert icon.read_bytes() == (REPO / "assets" / "brand" / "seiton-icon.svg").read_bytes()


def test_the_menu_entry(places):
    _install(places)
    entry = (places.applications / "seiton.desktop").read_text(encoding="utf-8")
    assert "Name=SEITON\n" in entry and "Icon=seiton\n" in entry
    assert f'Exec="{places.bin / "seiton"}" %f\n' in entry
    assert "Type=Application\n" in entry


def test_scope_names_its_menu_entry():
    # So the taskbar finds the entry and its icon (Wayland asks the app for it).
    assert "app.setDesktopFileName(CONFIG_DIR)" in (REPO / "Scope" / "Scope.py").read_text(encoding="utf-8")
    assert inst.APP_ID == "seiton"


def test_the_emblems_are_installed(places):
    _install(places)
    emblems = places.data / "icons" / "hicolor" / "scalable" / "emblems"
    assert list(emblems.glob("emblem-seiton-*.svg"))


# --- templates ------------------------------------------------------------------------------

def test_the_templates_come_along_without_gitkeep(places):
    _install(places)
    standard = places.templates / "Standard"
    assert (standard / "4_Finanz" / "44_Rechnungen" / "Eingang").is_dir()
    assert (standard / ".seiton" / "ACLs.md").is_file()
    assert not list(places.templates.rglob(".gitkeep"))
    assert {p.name for p in places.templates.iterdir()} == {"Standard", "Person", "Firma", "Development"}


def test_a_template_one_has_is_kept(places):
    own = places.templates / "Standard"
    own.mkdir(parents=True)
    (own / "Mine.md").write_text("mine")
    _install(places)
    assert [p.name for p in own.iterdir()] == ["Mine.md"]


def test_the_shipped_templates_are_clean():
    templates = REPO / "templates"
    assert not list(templates.rglob("ACLs-history")) and not list(templates.rglob(".TagsHere.json"))
    for note in templates.rglob("*.md"):
        text = note.read_text(encoding="utf-8")
        assert not text.startswith("---"), note  # no window place of PostFix
        assert "# Users" not in text, note  # no test people
    for folder in [p for p in templates.rglob("*") if p.is_dir()]:
        names = [p.name for p in folder.iterdir()]
        assert names, folder  # git keeps no empty folder
        assert ".gitkeep" not in names or names == [".gitkeep"], folder


# --- extras ---------------------------------------------------------------------------------

def test_no_extras_unless_asked(places):
    runner = _install(places)
    assert not any("install_autostart.py" in " ".join(c) for c in runner.commands)
    assert not (places.data / "thumbnailers").exists()


def test_suntree_at_login(places):
    runner = _install(places, suntree=True)
    python = str(places.venv / "bin" / "python")
    assert [python, str(REPO / "SunTree" / "install_autostart.py"), str(places.home)] in runner.commands


def test_markdown_previews_in_the_file_browsers(places):
    former = places.data / "thumbnailers" / "myos-markdown.thumbnailer"
    former.parent.mkdir(parents=True)
    former.write_text("[Thumbnailer Entry]\n")  # the same under the former name: would render twice
    _install(places, thumbnailer=True)
    entry = (places.data / "thumbnailers" / "seiton-md.thumbnailer").read_text(encoding="utf-8")
    python = str(places.venv / "bin" / "python")
    # Quoted: the file browsers split Exec like a shell, a path with spaces broke apart (I10).
    assert f'Exec="{python}" "{REPO / "scripts" / "seiton_md_thumbnailer.py"}" %i %o %s' in entry
    assert f"TryExec={python}" in entry and "__REPO_ROOT__" not in entry
    assert not former.exists()


# --- the Headline (Scope/Designdocument Headline.md) ---------------------------------------

def _install_on_cinnamon(places, **options):
    runner = Runner(installed=inst.PACKAGES["apt"])
    found = {"apt-get": "/usr/bin/apt-get", "cinnamon": "/usr/bin/cinnamon"}
    inst.install(places, inst.Options(**options), run=runner, ask=lambda question: False,
                 which=found.get)
    return runner


def test_the_headline_gets_a_launcher(places):
    _install(places)
    launcher = places.bin / "seiton-headline"
    assert launcher.is_file() and os.access(launcher, os.X_OK)
    assert str(REPO / "Headline" / "Headline.py") in launcher.read_text(encoding="utf-8")


def test_a_menu_entry_opens_the_panel_to_pin_to_any_taskbar(places):
    _install(places)
    entry = (places.applications / "seiton-headline.desktop").read_text(encoding="utf-8")
    assert f"Exec={inst._quoted(places.bin / 'seiton-headline')} --panel" in entry and "Icon=seiton" in entry


def test_on_cinnamon_the_applet_comes_along(places):
    _install_on_cinnamon(places)
    applet = places.data / "cinnamon" / "applets" / "seiton-headline@seiton"
    script = (applet / "applet.js").read_text(encoding="utf-8")
    assert f'const LAUNCHER = "{places.bin / "seiton-headline"}";' in script and "__LAUNCHER__" not in script
    assert (applet / "metadata.json").is_file() and (applet / "icon.svg").is_file()


def test_without_cinnamon_no_applet(places):
    _install(places)
    assert not (places.data / "cinnamon").exists()


def test_the_headline_at_login_only_when_asked(places):
    _install(places)
    login = places.config.parent / "autostart" / "seiton-headline.desktop"
    assert not login.exists()
    _install(places, headline=True)
    assert f"Exec={inst._quoted(places.bin / 'seiton-headline')}\n" in login.read_text(encoding="utf-8")


def test_uninstall_takes_the_headline_away(places):
    _install_on_cinnamon(places, headline=True)
    inst.uninstall(places, run=Runner())
    assert not (places.bin / "seiton-headline").exists()
    assert not (places.data / "cinnamon" / "applets" / "seiton-headline@seiton" / "applet.js").exists()
    assert not (places.config.parent / "autostart" / "seiton-headline.desktop").exists()


def test_the_applet_is_valid_javascript():
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("no node to check the syntax")
    script = REPO / "Headline" / "cinnamon" / "seiton-headline@seiton" / "applet.js"
    assert subprocess.run([node, "--check", str(script)], capture_output=True).returncode == 0


# --- the time tracking (Designdocument Time.md; Headline.md, 3a) ----------------------------

def test_the_time_screen_and_the_clock_get_launchers(places):
    _install(places)
    for name, script in (("seiton-time", "Time/TimeScreen.py"), ("seiton-clock", "cli/seiton_clock.py")):
        launcher = places.bin / name
        assert launcher.is_file() and os.access(launcher, os.X_OK)
        assert str(REPO / script) in launcher.read_text(encoding="utf-8")


def test_the_clock_registers_as_the_headlines_widget(places, monkeypatch):
    import json
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/4711")
    _install(places)
    registration = json.loads((places.config / "headline" / "widgets" / "clock.json").read_text(encoding="utf-8"))
    assert registration["folder"] == "/run/user/4711/seiton-clock"
    assert registration["open"] == [str(places.bin / "seiton-time")]
    assert set(registration["commands"]) == {"start", "stop"}


def test_the_clock_at_login_only_when_asked(places):
    login = places.config.parent / "autostart" / "seiton-clock.desktop"
    _install(places)
    assert not login.exists()
    _install(places, clock=True)
    assert f"Exec={inst._quoted(places.bin / 'seiton-clock')}\n" in login.read_text(encoding="utf-8")
    inst.uninstall(places, run=Runner())
    assert not login.exists()


def test_the_clock_at_login_brings_the_headline(places):
    # O1 (review 2026-11-18): the clock learns the active project from the Headline only.
    _install(places, clock=True)
    assert (places.config.parent / "autostart" / "seiton-headline.desktop").is_file()


def test_uninstall_takes_the_registration_away(places):
    _install(places)
    inst.uninstall(places, run=Runner())
    assert not (places.config / "headline" / "widgets" / "clock.json").exists()
    assert not (places.bin / "seiton-time").exists() and not (places.bin / "seiton-clock").exists()


# --- uninstalling ---------------------------------------------------------------------------

def test_uninstall_takes_what_it_wrote_and_keeps_settings_and_templates(places):
    _install(places, thumbnailer=True)
    places.config.mkdir(parents=True, exist_ok=True)
    (places.config / "seiton.conf").write_text("[General]\n")
    runner = Runner()
    inst.uninstall(places, run=runner)
    assert not (places.bin / "seiton").exists() and not (places.applications / "seiton.desktop").exists()
    assert not (places.data / "thumbnailers" / "seiton-md.thumbnailer").exists()
    assert not places.venv.exists() and not places.manifest.exists()
    assert (places.templates / "Standard").is_dir() and (places.config / "seiton.conf").exists()
    assert any("--remove" in c for c in runner.commands)  # SunTree's login entry, if any


def test_uninstall_takes_nothing_it_did_not_write(places):
    _install(places)
    stranger = places.bin / "something-else"
    stranger.write_text("not ours")
    inst.uninstall(places, run=Runner())
    assert stranger.exists()


# --- the entry --------------------------------------------------------------------------------

def test_install_sh_hands_over_to_the_installer():
    text = (REPO / "install.sh").read_text(encoding="utf-8")
    assert "installer/seiton_install.py" in text and "myos_core" not in text
    assert os.access(REPO / "install.sh", os.X_OK)


def test_the_settings_under_the_former_name_come_over_first(places):
    """"docs/Prüfung 2026-11-18.md", D5/P2: the installer made ~/.config/seiton before the old
    settings could move there."""
    from core import brand

    old = places.config.parent / brand.LEGACY_CONFIG_DIRS[0]
    old.mkdir(parents=True)
    (old / "Identity.md").write_text("Names: Oliver\n", encoding="utf-8")
    _install(places)
    assert (places.config / "Identity.md").read_text(encoding="utf-8") == "Names: Oliver\n"
    assert not old.exists()


def test_a_half_made_venv_is_made_anew(places):
    """"docs/Prüfung 2026-11-18.md", I3: a venv without pip (python3-venv was missing at the
    first run) stopped every later run."""
    (places.venv / "bin").mkdir(parents=True)
    places.python.write_text("")  # bin/python, but no pip
    runner = _install(places)
    made = [c for c in runner.commands if c[1:3] == ["-m", "venv"]]
    assert made and "--clear" in made[0]


def test_libfuse2_under_its_new_debian_name_counts():
    """"docs/Prüfung 2026-11-18.md", I12: Ubuntu 24.04, Mint 22, Debian 13 call it libfuse2t64."""
    runner = Runner(installed=[p for p in inst.PACKAGES["apt"] if p != "libfuse2"] + ["libfuse2t64"])
    assert "libfuse2" not in inst.missing_packages("apt", runner)
    assert "libfuse2" in inst.missing_packages("apt", Runner(installed=[]))


def test_an_update_does_not_ask_again_for_what_starts_at_login(places, monkeypatch, capsys):
    """"docs/Prüfung 2026-11-18.md", I6: answering N at an update left it starting anyway."""
    entry = places.config.parent / "autostart" / f"{inst.HEADLINE}.desktop"
    entry.parent.mkdir(parents=True)
    entry.write_text("[Desktop Entry]\n")
    asked = []
    assert inst.wanted_at_login(False, "Also the Headline at login?", entry,
                                ask=lambda q: asked.append(q) or False) is True
    assert asked == [] and str(entry) in capsys.readouterr().out
    entry.unlink()
    assert inst.wanted_at_login(False, "Also the Headline at login?", entry,
                                ask=lambda q: asked.append(q) or False) is False
    assert asked == ["Also the Headline at login?"]
