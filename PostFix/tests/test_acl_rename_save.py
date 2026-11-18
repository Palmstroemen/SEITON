"""PostFix and the ACLs of the open note ("docs/Prüfung 2026-11-18.md", PF2): renaming takes
the note's rules along (as Scope does) and is refused where rules wait for the new name; with
enforcement on, a note the person may only read is neither renamed nor saved."""

import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from core.brand import META_DIR, env_name

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: *\n\n"
    "## Team\n- /Arbeit/: read, write\n- /Arbeit/Geheim.md: none\n- /Lesen/: read\n\n"
    "# Users\nAnna: Admin\nKarl: Team\n"
)


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("POSTFIX_EDITOR"), "line")  # the rules, not the editor page
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for key in (env_name("ACL_MODE"), env_name("ACL_BACKEND")):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(env_name("ACL_USER"), "anna")
    root = tmp_path / "Firma"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# Project\n")
    (root / META_DIR / "ACLs.md").write_text(ACLS)
    for folder in ("Arbeit", "Lesen"):
        (root / folder).mkdir()
    (root / "Arbeit" / "Geheim.md").write_text("# Geheim\n\nText.\n")
    (root / "Lesen" / "Info.md").write_text("# Info\n\nText.\n")
    return root


@pytest.fixture
def window():
    QApplication.instance() or QApplication([])
    from PostFix.main import PostFixWindow

    made = []

    def make(path):
        w = PostFixWindow(open_path=path, ui_language="en")
        made.append(w)
        return w

    yield make
    for w in made:
        w._has_local_changes = False
        w.close()


def _rename(w, name):
    w.file_name_edit.setText(name)
    w.on_filename_edit_finished()


def test_renaming_takes_the_rules_along(project, window):
    w = window(project / "Arbeit" / "Geheim.md")
    _rename(w, "Vertraulich")
    assert (project / "Arbeit" / "Vertraulich.md").exists()
    rules = (project / META_DIR / "ACLs.md").read_text()
    assert "- /Arbeit/Vertraulich.md: none\n" in rules and "Geheim.md" not in rules


def test_renaming_onto_waiting_rules_is_refused(project, window):
    w = window(project / "Arbeit" / "Geheim.md")
    (project / META_DIR / "ACLs.md").write_text(ACLS.replace("- /Lesen/: read\n", "- /Lesen/: read\n- /Arbeit/Offen.md: read\n"))
    _rename(w, "Offen")
    assert (project / "Arbeit" / "Geheim.md").exists() and not (project / "Arbeit" / "Offen.md").exists()


def test_with_enforcement_a_reader_neither_renames_nor_saves(project, window, monkeypatch):
    monkeypatch.setenv(env_name("ACL_MODE"), "enforce")
    monkeypatch.setenv(env_name("ACL_USER"), "karl")
    note = project / "Lesen" / "Info.md"
    w = window(note)
    for _ in range(5):
        QApplication.processEvents()  # the ACL context comes after the first paint
    assert w.file_name_edit.isReadOnly()
    _rename(w, "Anders")
    assert note.exists() and not (project / "Lesen" / "Anders.md").exists()
    w.editor.load_markdown("# Info\n\nGeändert.\n")
    w._has_local_changes = True
    assert not w._save_current_document()
    assert "Geändert." not in note.read_text()
