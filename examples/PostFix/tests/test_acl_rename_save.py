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
    from examples.PostFix.main import PostFixWindow

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


def test_a_note_that_is_no_utf8_opens_read_only(tmp_path, window, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", PF6: PostFix crashed on such a note. It opens to be read,
    and is never written over (its bytes would change)."""
    monkeypatch.setenv(env_name("POSTFIX_EDITOR"), "line")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    note = tmp_path / "Alt.md"
    raw = "# Überschrift\n\nÄltere Notiz.\n".encode("latin-1")
    note.write_bytes(raw)
    w = window(note)
    assert "ltere Notiz" in w.editor.get_markdown()
    w.editor.load_markdown(w.editor.get_markdown() + "Neu.\n")
    w._has_local_changes = True
    assert not w._save_current_document()
    assert note.read_bytes() == raw


def test_tags_reach_the_project_when_the_note_is_left_not_while_typing(tmp_path, window, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", PF4: a tag half typed ("#dring") stayed in Tags.md."""
    monkeypatch.setenv(env_name("POSTFIX_EDITOR"), "line")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tmp_path / "P"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# Project\n")
    (root / META_DIR / "Tags.md").write_text("# Tags\n#alt\n")
    note = root / "Notiz.md"
    note.write_text("# Notiz\n")
    w = window(note)
    for _ in range(5):
        QApplication.processEvents()
    w.editor.load_markdown("# Notiz\n\n#dring")
    w._on_editor_tags_changed(["dring"])
    w._has_local_changes = True
    assert w._save_current_document()
    assert "dring" not in (root / META_DIR / "Tags.md").read_text()
    w.editor.load_markdown("# Notiz\n\n#dringend\n")
    w._on_editor_tags_changed(["dringend"])
    w._has_local_changes = True
    w.close()
    tags = (root / META_DIR / "Tags.md").read_text()
    assert "dringend" in tags and "dring\n" not in tags.replace("dringend", "")


def test_printing_leaves_out_the_front_matter(tmp_path, window, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", PF8."""
    monkeypatch.setenv(env_name("POSTFIX_EDITOR"), "line")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    note = tmp_path / "Brief.md"
    note.write_text("---\nwindow_x_permille: 78\n---\n# Brief\n\nText.\n")
    html = window(note)._printable_html()
    assert "Brief" in html and "window_x_permille" not in html


def test_tags_in_code_and_numbers_are_no_tags():
    """"docs/Prüfung 2026-11-18.md", PF9: as in Obsidian."""
    QApplication.instance() or QApplication([])
    from examples.PostFix.smart_editor import SmartEditor

    body = ("Echter #tag und #zwei.\n\n```c\n#include <stdio.h>\n```\n\nInline `#pragma once` hier.\n"
            "Issue #123 und #2026_plan.\n~~~\n#define X\n~~~\n")
    assert SmartEditor().extract_tags(body) == ["tag", "zwei", "2026_plan"]
