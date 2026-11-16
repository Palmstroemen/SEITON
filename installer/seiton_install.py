#!/usr/bin/env python3
"""SEITON's installer, for one user, from this git folder (install.sh starts it).

    ./install.sh                 install or update (after git pull: the same again)
    ./install.sh --suntree       also SunTree at login (Ctrl+Alt+Space)
    ./install.sh --thumbnailer   also Markdown previews in the file browsers
    ./install.sh --yes           ask nothing: system packages yes, extras only as given
    ./install.sh --uninstall     take away what it wrote; settings and templates stay

What it does:
1. System packages through the distribution's package manager (apt, dnf, zypper, pacman):
   libfuse 2 for the lens, Qt's xcb-cursor, pdftoppm, xdg-utils. Only the missing ones, after
   asking, with sudo.
2. Python packages in a venv of SEITON's own (~/.local/share/seiton/venv): newer distributions
   refuse pip in the system (PEP 668), and SEITON keeps its own Qt version.
3. Launchers in ~/.local/bin (seiton, the CLI tools, seiton-postfix), the icon, the menu entry,
   the emblems.
4. The templates to ~/.seiton/Templates; a template one has already is kept.
5. On request SunTree at login and Markdown previews in the file browsers.

Everything written outside the venv is listed in ~/.local/share/seiton/installed.txt; uninstalling
takes exactly that, the venv, and SunTree's login entry.

Standard library only: it runs before the venv exists.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Mapping, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.brand import CONFIG_DIR, META_DIR, NAME, file_name  # noqa: E402

APP_ID = CONFIG_DIR  # seiton: the menu entry, the icon, the main launcher

# What SEITON needs from the system, per package manager.
PACKAGES = {
    "apt": ["python3-venv", "fuse3", "libfuse2", "libxcb-cursor0", "poppler-utils", "xdg-utils"],
    "dnf": ["python3", "fuse", "fuse-libs", "xcb-util-cursor", "poppler-utils", "xdg-utils"],
    "zypper": ["python3", "fuse", "libfuse2", "libxcb-cursor0", "poppler-tools", "xdg-utils"],
    "pacman": ["python", "fuse2", "xcb-util-cursor", "poppler", "xdg-utils"],
}
# The program that tells the manager, the query whether a package is there, the install command.
FINDS = (("apt-get", "apt"), ("dnf", "dnf"), ("zypper", "zypper"), ("pacman", "pacman"))
QUERY = {"apt": ["dpkg", "-s"], "dnf": ["rpm", "-q"], "zypper": ["rpm", "-q"], "pacman": ["pacman", "-Q"]}
INSTALL = {
    "apt": ["sudo", "apt-get", "install", "-y"],
    "dnf": ["sudo", "dnf", "install", "-y"],
    "zypper": ["sudo", "zypper", "--non-interactive", "install"],
    "pacman": ["sudo", "pacman", "-S", "--needed", "--noconfirm"],
}
# The CLI tools that get a launcher of the same name (cli/<name>.py).
CLI_TOOLS = ("myls", "myproject", "mytag", "myedit", "myfilter", "myacl", "myexport", "myimport")

Run = Callable[..., int]
Ask = Callable[[str], bool]
Which = Callable[[str], Optional[str]]


@dataclass(frozen=True)
class Places:
    repo: Path
    home: Path
    data: Path  # XDG_DATA_HOME
    config: Path  # SEITON's settings folder, below XDG_CONFIG_HOME

    @classmethod
    def from_env(cls, repo: Path = REPO, env: Mapping[str, str] = os.environ) -> "Places":
        home = Path(env.get("HOME") or Path.home())
        data = Path(env.get("XDG_DATA_HOME") or home / ".local" / "share")
        config = Path(env.get("XDG_CONFIG_HOME") or home / ".config") / CONFIG_DIR
        return cls(Path(repo), home, data, config)

    @property
    def own(self) -> Path:
        return self.data / CONFIG_DIR

    @property
    def venv(self) -> Path:
        return self.own / "venv"

    @property
    def python(self) -> Path:
        return self.venv / "bin" / "python"

    @property
    def manifest(self) -> Path:
        return self.own / "installed.txt"

    @property
    def bin(self) -> Path:
        return self.home / ".local" / "bin"

    @property
    def applications(self) -> Path:
        return self.data / "applications"

    @property
    def hicolor(self) -> Path:
        return self.data / "icons" / "hicolor"

    @property
    def templates(self) -> Path:
        return self.home / META_DIR / "Templates"


@dataclass(frozen=True)
class Options:
    suntree: bool = False
    thumbnailer: bool = False
    system_packages: bool = True


def run_command(command: List, quiet: bool = False) -> int:
    out = subprocess.DEVNULL if quiet else None
    try:
        return subprocess.run([str(c) for c in command], stdout=out, stderr=out, check=False).returncode
    except FileNotFoundError:
        return 127


def ask_user(question: str) -> bool:
    try:
        return input(f"{question} [y/N] ").strip().lower() in {"y", "yes", "j", "ja"}
    except EOFError:
        return False


def package_manager(which: Which = shutil.which) -> Optional[str]:
    for program, manager in FINDS:
        if which(program):
            return manager
    return None


def missing_packages(manager: str, run: Run) -> List[str]:
    return [p for p in PACKAGES[manager] if run([*QUERY[manager], p], quiet=True) != 0]


class Written:
    """What the installer writes outside the venv, for the manifest."""

    def __init__(self) -> None:
        self.paths: List[Path] = []

    def text(self, path: Path, content: str, executable: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if executable:
            path.chmod(0o755)
        self.paths.append(path)

    def copy(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        self.paths.append(target)


def _quoted(path: Path) -> str:
    text = str(path)
    # Security: launchers and desktop entries are run; refuse what plain quoting cannot hold.
    if any(c in text for c in '"`$\\\n'):
        raise ValueError(f"not a plain path: {text!r}")
    return f'"{text}"'


def _launcher(places: Places, script: Path) -> str:
    return f'#!/bin/sh\n# {NAME} (installer/seiton_install.py)\nexec {_quoted(places.python)} {_quoted(script)} "$@"\n'


def system_packages(places: Places, options: Options, run: Run, ask: Ask, which: Which) -> None:
    if not options.system_packages:
        return
    manager = package_manager(which)
    if manager is None:
        print(f"No known package manager. {NAME} needs: libfuse 2, xcb-cursor, poppler (pdftoppm), xdg-utils, python3 venv.")
        return
    missing = missing_packages(manager, run)
    if not missing:
        return
    command = [*INSTALL[manager], *missing]
    if ask(f"Missing system packages: {' '.join(missing)}\nInstall them now? ({' '.join(command)})"):
        if run(command) != 0:
            print("Installing the system packages failed; continuing, some parts may not work.")
    else:
        print(f"Not installed. Later: {' '.join(command)}")


def python_packages(places: Places, run: Run) -> None:
    if not places.python.exists():
        if run([sys.executable, "-m", "venv", str(places.venv)]) != 0:
            raise SystemExit(f"Could not make the venv {places.venv} (python3-venv missing?)")
    run([str(places.python), "-m", "pip", "install", "--upgrade", "pip"])
    if run([str(places.python), "-m", "pip", "install", "-r", str(places.repo / "installer" / "requirements.txt")]) != 0:
        raise SystemExit("Installing the Python packages failed.")


def launchers(places: Places, written: Written) -> None:
    written.text(places.bin / APP_ID, _launcher(places, places.repo / "Scope" / "Scope.py"), executable=True)
    for tool in CLI_TOOLS:
        script = places.repo / "cli" / f"{tool}.py"
        if script.is_file():
            written.text(places.bin / tool, _launcher(places, script), executable=True)
    postfix = places.repo / "PostFix" / "cli.py"
    if postfix.is_file():  # "postfix" alone is a mail server's command
        written.text(places.bin / file_name("postfix"), _launcher(places, postfix), executable=True)


def icons(places: Places, written: Written, run: Run) -> None:
    written.copy(places.repo / "assets" / "brand" / file_name("icon.svg"),
                 places.hicolor / "scalable" / "apps" / f"{APP_ID}.svg")
    for folder in ("emblems", "emblems-light"):
        for emblem in sorted((places.repo / "assets" / "icons" / folder).glob("emblem-seiton-*.svg")):
            written.copy(emblem, places.hicolor / "scalable" / "emblems" / emblem.name)
    if shutil.which("gtk-update-icon-cache"):
        run(["gtk-update-icon-cache", "-q", "-t", str(places.hicolor)], quiet=True)


def menu_entry(places: Places, written: Written, run: Run) -> None:
    written.text(places.applications / f"{APP_ID}.desktop", (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={NAME}\n"
        "GenericName=Project file browser\n"
        "Comment=A place for everything, everything in its place\n"
        f"Exec={_quoted(places.bin / APP_ID)} %f\n"
        f"Icon={APP_ID}\n"
        "Terminal=false\n"
        "Categories=Utility;FileManager;\n"
        "MimeType=inode/directory;\n"))
    if shutil.which("update-desktop-database"):
        run(["update-desktop-database", "-q", str(places.applications)], quiet=True)


def templates(places: Places) -> None:
    """The shipped templates, each one only when one has none of that name (it is one's own)."""
    source = places.repo / "templates"
    for template in sorted(p for p in source.iterdir() if p.is_dir()):
        target = places.templates / template.name
        if target.exists():
            continue
        shutil.copytree(template, target, ignore=shutil.ignore_patterns(".gitkeep"))


def suntree(places: Places, run: Run) -> None:
    run([str(places.python), str(places.repo / "SunTree" / "install_autostart.py"), str(places.home)])


def thumbnailer(places: Places, written: Written) -> None:
    template = (places.repo / "installer" / file_name("md.thumbnailer")).read_text(encoding="utf-8")
    python = str(places.python)
    entry = (template.replace("TryExec=python3", f"TryExec={python}")
             .replace("Exec=python3 ", f"Exec={python} ")
             .replace("__REPO_ROOT__", str(places.repo)))
    written.text(places.data / "thumbnailers" / file_name("md.thumbnailer"), entry)


def _write_manifest(places: Places, written: Written) -> None:
    before = _read_manifest(places)
    paths = list(dict.fromkeys([*before, *(str(p) for p in written.paths)]))
    places.manifest.parent.mkdir(parents=True, exist_ok=True)
    places.manifest.write_text("".join(f"{p}\n" for p in paths), encoding="utf-8")


def _read_manifest(places: Places) -> List[str]:
    if not places.manifest.is_file():
        return []
    return [line for line in places.manifest.read_text(encoding="utf-8").splitlines() if line]


def install(places: Places, options: Options, run: Run = run_command, ask: Ask = ask_user,
            which: Which = shutil.which) -> None:
    written = Written()
    print(f"{NAME}: system packages ...")
    system_packages(places, options, run, ask, which)
    print(f"{NAME}: Python packages in {places.venv} ...")
    python_packages(places, run)
    print(f"{NAME}: launchers, icon, menu entry ...")
    launchers(places, written)
    icons(places, written, run)
    menu_entry(places, written, run)
    templates(places)
    if options.suntree:
        suntree(places, run)
    if options.thumbnailer:
        thumbnailer(places, written)
    _write_manifest(places, written)
    print(f"\n{NAME} is installed. Start it from the menu or with: {places.bin / APP_ID}")
    if str(places.bin) not in os.environ.get("PATH", "").split(os.pathsep):
        print(f"(Add {places.bin} to PATH to start it and the CLI tools by name.)")


def uninstall(places: Places, run: Run = run_command) -> None:
    for line in _read_manifest(places):
        path = Path(line)
        if path.is_file() or path.is_symlink():
            path.unlink()
    if places.python.exists():
        run([str(places.python), str(places.repo / "SunTree" / "install_autostart.py"), "--remove"], quiet=True)
    shutil.rmtree(places.venv, ignore_errors=True)
    places.manifest.unlink(missing_ok=True)
    print(f"{NAME} is uninstalled. Settings ({places.config}) and templates ({places.templates}) stay.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=f"Install {NAME} for this user.")
    parser.add_argument("--suntree", action="store_true", help="SunTree at login (Ctrl+Alt+Space)")
    parser.add_argument("--thumbnailer", action="store_true", help="Markdown previews in the file browsers")
    parser.add_argument("--no-system-packages", action="store_true", help="leave the system packages alone")
    parser.add_argument("--yes", action="store_true", help="ask nothing")
    parser.add_argument("--uninstall", action="store_true", help="take away what was installed")
    args = parser.parse_args(argv)
    places = Places.from_env()
    if args.uninstall:
        uninstall(places)
        return 0
    ask = (lambda question: True) if args.yes else ask_user
    suntree_wanted = args.suntree or (not args.yes and ask_user("Also SunTree, the folder fan, at login (Ctrl+Alt+Space)?"))
    previews_wanted = args.thumbnailer or (not args.yes and ask_user("Also Markdown previews in the system's file browsers?"))
    install(places, Options(suntree=suntree_wanted, thumbnailer=previews_wanted,
                            system_packages=not args.no_system_packages), ask=ask)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
