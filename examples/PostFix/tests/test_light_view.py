"""The light rendering on screen (examples/PostFix/light_view.py): Qt lays a note out as the editor's page
would; the measured look itself is checked against the real editor by hand (Xephyr harness),
the behaviour here."""

import os

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

LONG = "# Lang\n\n" + "\n".join(f"Zeile {n}" for n in range(150))


@pytest.fixture
def view():
    app = QApplication.instance() or QApplication([])
    from examples.PostFix.light_view import LightBrowser

    browser = LightBrowser()
    browser.resize(500, 300)
    browser.show()
    app.processEvents()
    yield app, browser
    browser.deleteLater()


def test_a_note_opens_at_its_top_and_stays_there(view):
    app, browser = view
    browser.show_note(LONG)
    browser.setFocus()
    browser.ensureCursorVisible()  # what Qt does on focus and the like
    app.processEvents()
    assert browser.verticalScrollBar().value() == 0


def test_lines_and_scrolling_in_the_editors_terms(view):
    app, browser = view
    browser.show_note(LONG)
    browser.scroll_to_line(80, 12)
    line, offset = browser.top_line()
    assert line == 80 and abs(offset - 12) < 1


def test_laid_out_again_when_the_width_changes(view):
    app, browser = view
    long_line = "Wort " * 200
    browser.show_note(long_line)
    narrow = browser.document().size().height()
    browser.resize(900, 300)
    app.processEvents()
    assert browser.document().size().height() < narrow  # fewer lines when wider


def _block_with_picture(browser):
    block = browser.document().begin()
    while block.isValid():
        if "￼" in block.text():
            return block
        block = block.next()
    return None


def test_a_picture_alone_on_its_line_sits_in_the_middle(view):
    from PySide6.QtCore import Qt

    app, browser = view
    browser.show_note("Text\n\n![Bild|20](bild.png)\n\nEnde")
    block = _block_with_picture(browser)
    assert block is not None and block.blockFormat().alignment() & Qt.AlignHCenter


def test_a_picture_in_the_text_stays_where_the_text_is(view):
    from PySide6.QtCore import Qt

    app, browser = view
    browser.show_note("Ein Bild ![Bild|20](bild.png) im Text")
    block = _block_with_picture(browser)
    assert block is not None and not block.blockFormat().alignment() & Qt.AlignHCenter
