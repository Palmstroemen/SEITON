"""Where SunTree is and puts things ("docs/Prüfung 2026-11-18.md", ST3, ST4): its clipboard is
Scope's (next to "Projekte", else in the root project), made only when something goes there; a
start outside every root (the autostart gives the home folder) goes to the first root below,
as the Headline does."""

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(REPO))

from core.brand import META_DIR, env_name  # noqa: E402
from core.scope_api import ScopeApi, start_place  # noqa: E402
import SunTree.SunTree as T  # noqa: E402


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# SEITON Project\n")
    return path


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv(env_name("SCOPE_START_DAEMON"), "0")
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)


def _backend(place):
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    return T.SunTreeBackend(T.BackendAdapter(ScopeApi(str(place))), str(place))


def test_the_clipboard_is_scopes_and_comes_when_used(tmp_path):
    root = _project(tmp_path / "Dokumente" / "Projekte")
    studio = _project(root / "Musikstudio")
    backend = _backend(studio)
    assert backend.clipboardPath() == str(tmp_path / "Dokumente" / "Clipboard")  # next to Projekte
    assert not (tmp_path / "Dokumente" / "Clipboard").exists()  # not made at the start


def test_a_root_project_keeps_its_clipboard_inside(tmp_path):
    root = _project(tmp_path / "Tutorial")
    backend = _backend(root)
    assert backend.clipboardPath() == str(root / "Clipboard")


def test_a_start_outside_every_root_goes_to_the_first_root_below(tmp_path):
    home = tmp_path / "home"
    root = _project(home / "Dokumente")
    assert start_place(str(home)) == str(root)
    assert start_place(str(root / "Sub")) == str(root / "Sub")  # inside a root: as it is
    assert start_place(str(tmp_path / "leer")) == str(tmp_path / "leer")  # nothing below: as it is
