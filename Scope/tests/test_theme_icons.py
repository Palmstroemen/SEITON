"""Scope's folder icons follow the system theme (image://theme/...): projects too, unless a
project chooses an icon of its own (Desk.md "projectIcon"); a project shows itself by its
colour and the P badge, not by an icon of Scope's own."""

from pathlib import Path

SCOPE_DIR = Path(__file__).resolve().parents[1]
MAIN = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")
SETUP = (SCOPE_DIR / "SetupPage.qml").read_text(encoding="utf-8")
SCOPE_PY = (SCOPE_DIR / "Scope.py").read_text(encoding="utf-8")


def test_projects_without_an_own_icon_get_the_themes_folder():
    body = MAIN[MAIN.index("function projectIconForPath(path)"):]
    body = body[:body.index("\n    }\n")]
    # No icon of Scope's own: "" lets FolderBrowser fall back to image://theme/folder.
    assert "Theme/icons" not in body and "Fallback" not in body
    assert "Theme/icons/project.svg" not in MAIN
    assert not (SCOPE_DIR / "Theme" / "icons" / "project.svg").exists()


def test_the_setup_examples_show_the_themes_folder():
    assert "Theme/icons/folder.svg" not in SETUP
    assert SETUP.count('iconSource: "image://theme/folder"') == 3
