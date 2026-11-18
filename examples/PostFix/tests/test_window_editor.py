"""PostFix windows with the one editor (the default; MYOS_POSTFIX_EDITOR=line brings back the
old one): the note being edited gets the CodeMirror editor, the others keep their rendering; what
is typed is saved as before (front matter kept, changes from outside merged), links open notes in
the same window."""

import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QApplication
from core.brand import env_name

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

NOTE = "---\nbackground_color: '#fff8b0'\n---\n# Lektion\n\nErster Absatz.\n\n[weiter](<Zweite.md>)\n"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("POSTFIX_EDITOR"), "codemirror")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    app = QApplication.instance() or QApplication([])
    from examples.PostFix import editor_host
    from examples.PostFix.main import PostFixWindow

    editor_host.forget_shared()  # every test starts as a PostFix that has not edited yet

    first = tmp_path / "Erste.md"
    first.write_text(NOTE, encoding="utf-8")
    (tmp_path / "Zweite.md").write_text("# Zweite\n\nDer zweite Text.\n", encoding="utf-8")
    windows = []

    def window(path):
        w = PostFixWindow(open_path=path, ui_language="en")
        w.show()
        windows.append(w)
        return w

    yield app, window, tmp_path, editor_host
    for w in windows:
        w.close()
    _wait(app, lambda: False, 0.2)


def _wait(app, condition, seconds=8):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def _js(app, host, code):
    result = {}
    host.view.page().runJavaScript(code, 0, lambda value: result.update(value=value))
    _wait(app, lambda: "value" in result)
    return result.get("value")


def _ready(app, host):
    assert _wait(app, lambda: host.ready, 20)
    _wait(app, lambda: False, 0.3)


def test_typing_in_the_editor_is_saved_with_the_front_matter(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    assert host.owner() is w.editor
    _js(app, host, "(h => h.view.dispatch({changes: {from: h.view.state.doc.length, insert: 'Neu getippt.\\n'},"
                   " userEvent: 'input'}))(window.host)")
    assert _wait(app, lambda: "Neu getippt." in (folder / "Erste.md").read_text(encoding="utf-8"))
    saved = (folder / "Erste.md").read_text(encoding="utf-8")
    assert saved.startswith("---\n") and "background_color" in saved and "Erster Absatz." in saved


def test_a_change_from_outside_shows_in_the_editor(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    (folder / "Erste.md").write_text(NOTE.replace("Erster Absatz.", "Von außen."), encoding="utf-8")
    assert _wait(app, lambda: "Von außen." in (_js(app, host, f"window.host.getDoc({str((folder / 'Erste.md').resolve())!r})") or ""))


def test_the_editor_moves_to_the_note_being_edited(setup):
    app, window, folder, editor_host = setup
    first, second = window(folder / "Erste.md"), window(folder / "Zweite.md")
    host = editor_host.shared()
    first._take_editor()
    _ready(app, host)
    first._take_editor()  # checked right away: activation events must not move it in between
    assert host.owner() is first.editor and first.editor.preview_suspended()
    second._take_editor()
    assert host.owner() is second.editor
    assert not first.editor.preview_suspended()  # the first shows its rendering again
    assert second.editor.preview_suspended()


def test_a_link_opens_the_note_in_the_same_window(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    w.follow_link("Zweite.md")
    _wait(app, lambda: False, 0.3)
    assert Path(w.editor.current_path) == (folder / "Zweite.md")
    assert "Der zweite Text." in w.editor.get_markdown()
    assert _wait(app, lambda: "Der zweite Text." in (_js(app, host, f"window.host.getDoc({str((folder / 'Zweite.md').resolve())!r})") or ""))


def test_without_the_switch_postfix_edits_in_the_editor(setup, monkeypatch):
    app, window, folder, editor_host = setup
    monkeypatch.delenv(env_name("POSTFIX_EDITOR"))
    w = window(folder / "Erste.md")
    w._take_editor()
    assert w.editor.preview_suspended()


def test_the_line_editor_is_still_there_when_asked_for(setup, monkeypatch):
    app, window, folder, editor_host = setup
    monkeypatch.setenv(env_name("POSTFIX_EDITOR"), "line")
    w = window(folder / "Erste.md")
    w._take_editor()
    assert not w.editor.preview_suspended()


def _point_of(w, text):
    """Where text shows in the note's light rendering (viewport coordinates)."""
    preview = w.editor.preview
    cursor = preview.document().find(text.replace(" ", " \u200b"))  # spaces carry a zero-width break
    assert not cursor.isNull(), text
    cursor.setPosition(cursor.selectionStart() + 2)
    return preview.cursorRect(cursor).center()


def _click(widget, point):
    for kind in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
        QApplication.sendEvent(widget, QMouseEvent(kind, QPointF(point), QPointF(widget.mapToGlobal(point)),
                                                  Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))


def test_reading_a_note_never_loads_the_editor(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w.activateWindow()
    _wait(app, lambda: False, 0.3)
    w.changeEvent(QEvent(QEvent.ActivationChange))
    assert editor_host._shared is None  # no browser page for reading
    shown = w.editor.preview.document().toPlainText().replace("\u200b", "")
    assert "Erster Absatz." in shown and "#" not in shown and "](" not in shown  # the editor's look


def test_a_click_into_the_text_loads_the_editor_with_the_cursor_there(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    _click(w.editor.preview.viewport(), _point_of(w, "Erster Absatz."))
    host = editor_host._shared
    assert host is not None and host.owner() is w.editor
    _ready(app, host)
    line = "window.host.view.state.doc.lineAt(window.host.view.state.selection.main.head).text"
    assert _wait(app, lambda: _js(app, host, line) == "Erster Absatz.")


def test_typing_into_the_rendering_goes_into_the_note_at_its_end(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    QApplication.sendEvent(w.editor.preview, QKeyEvent(QEvent.KeyPress, Qt.Key_X, Qt.NoModifier, "X"))
    assert editor_host._shared is not None and editor_host._shared.owner() is w.editor
    _ready(app, editor_host._shared)
    # The note's last line break stays (PF7), so its end is a new line.
    ok = _wait(app, lambda: (folder / "Erste.md").read_text(encoding="utf-8").rstrip("\n").endswith("Zweite.md>)\nX"))
    assert ok, repr((folder / "Erste.md").read_text(encoding="utf-8")[-60:])


def test_a_link_in_the_rendering_opens_the_note_without_the_editor(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    _click(w.editor.preview.viewport(), _point_of(w, "weiter"))
    _wait(app, lambda: False, 0.2)
    assert Path(w.editor.current_path) == folder / "Zweite.md"
    assert editor_host._shared is None


def test_once_loaded_the_editor_follows_the_activated_note(setup):
    app, window, folder, editor_host = setup
    first, second = window(folder / "Erste.md"), window(folder / "Zweite.md")
    second.changeEvent(QEvent(QEvent.ActivationChange))
    assert editor_host._shared is None  # nothing edited yet
    _click(first.editor.preview.viewport(), _point_of(first, "Erster Absatz."))
    _ready(app, editor_host._shared)
    second._take_editor()
    assert editor_host._shared.owner() is second.editor


def test_the_rendering_takes_over_where_the_editor_was_scrolled(setup):
    app, window, folder, editor_host = setup
    long = "# Lang\n\n" + "\n".join(f"Zeile {n}" for n in range(200)) + "\n"
    (folder / "Lang.md").write_text(long, encoding="utf-8")
    first, second = window(folder / "Lang.md"), window(folder / "Zweite.md")
    first.resize(500, 400)
    first._take_editor()
    host = editor_host._shared
    _ready(app, host)
    first._take_editor()  # activation events of the second window must not have moved it
    _js(app, host, "window.host.view.dispatch({effects: PostFixEditor.scrollToLine(window.host.view, 120)})")
    assert _wait(app, lambda: (host.top_of(first._editor_key()) or (0,))[0] >= 118)
    second._take_editor()  # the editor leaves: the rendering shows the same lines
    line, _offset = first.editor.preview.top_line()
    assert abs(line - host.top_of(first._editor_key())[0]) <= 1


def test_typing_after_renaming_the_note_goes_into_the_renamed_file(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    w.file_name_edit.setText("Umbenannt")
    w.on_filename_edit_finished()
    renamed = folder / "Umbenannt.md"
    assert renamed.exists() and not (folder / "Erste.md").exists()
    _js(app, host, "(h => h.view.dispatch({changes: {from: h.view.state.doc.length, insert: 'Danach getippt.\\n'},"
                   " userEvent: 'input'}))(window.host)")
    assert _wait(app, lambda: "Danach getippt." in renamed.read_text(encoding="utf-8"))


def test_closing_without_a_place_to_save_asks_first(setup, monkeypatch):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    asked = []
    monkeypatch.setattr(w, "_may_close_unsaved", lambda: asked.append(True) or False)
    (folder / "Erste.md").chmod(0o444)
    folder.chmod(0o555)  # neither the note nor a copy beside it can be written
    try:
        w._has_local_changes = True
        w.close()
        assert asked and w.isVisible()  # not closed: the text is still there
    finally:
        folder.chmod(0o755)
        (folder / "Erste.md").chmod(0o644)


def _type_at_end(app, host, text):
    _js(app, host, "(h => h.view.dispatch({changes: {from: h.view.state.doc.length, insert: %r},"
                   " userEvent: 'input'}))(window.host)" % text)


def test_a_colour_changed_in_the_sidebar_stays_when_one_types_on(setup):
    """"docs/Prüfung 2026-11-18.md", PF5: the next keystroke set the old colour back."""
    app, window, folder, editor_host = setup
    note = folder / "Farbe.md"
    note.write_text("# Farbe\n\nrot: #ff0000\n", encoding="utf-8")
    w = window(note)
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    w._on_color_definition_change("rot", "#ff0000", "#00ff00")
    assert "rot: #00ff00" in note.read_text(encoding="utf-8")
    _wait(app, lambda: False, 0.3)
    _type_at_end(app, host, "Weiter.\n")
    assert _wait(app, lambda: "Weiter." in note.read_text(encoding="utf-8"))
    assert "rot: #00ff00" in note.read_text(encoding="utf-8")


def test_typing_goes_on_after_a_click_on_a_tag(setup):
    app, window, folder, editor_host = setup
    note = folder / "Tags.md"
    note.write_text("# Tags\n\nEin #wichtig Satz.\n", encoding="utf-8")
    w = window(note)
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    w.activateWindow()
    host.view.setFocus()
    app.processEvents()
    w._on_tag_search("wichtig")
    app.processEvents()
    assert host.owner() is w.editor and host.view.isVisible()
    # Keys keep going to the editor: neither the rendering under it nor the old overlay takes them.
    assert QApplication.focusWidget() not in (w.editor.preview, w.editor.focus_edit)
    assert not w.editor.focus_edit.isVisible()
    _type_at_end(app, host, "Danach.\n")
    assert _wait(app, lambda: "Danach." in note.read_text(encoding="utf-8"))


def test_colour_buttons_of_the_line_editor_are_not_offered(setup):
    # Text colour and highlighter work only in the old line editor ("docs/Prüfung
    # 2026-11-18.md", PF13): with the one editor a click opened the picker and did nothing.
    app, window, tmp_path, _ = setup
    w = window(tmp_path / "Erste.md")
    assert w.btn_text_color.isHidden() and w.btn_highlight.isHidden()
    assert not w.btn_bg_color.isHidden()  # the note's colour stays
