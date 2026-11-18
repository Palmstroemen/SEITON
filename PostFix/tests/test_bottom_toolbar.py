"""The bottom toolbar offers only what is wired ("docs/Prüfung 2026-11-18.md", PF14): no "Send
to" (every target opened the note in its default program), "Open in" only Obsidian, and printing
only to PDF and real printers. The note's path reaches Obsidian encoded."""

import os

import pytest
from PySide6.QtWidgets import QApplication, QLabel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def toolbar(monkeypatch):
    QApplication.instance() or QApplication([])
    from PostFix.ui_panels import BottomToolbar

    bar = BottomToolbar()
    bar._desktop_index, bar._printers, bar._runtime_resources_loaded = {}, [], True  # no lpstat
    yield bar
    bar.deleteLater()


def _offered(bar, action):
    button = next(b for b in bar._primary_buttons if b._flyout_label == action)
    bar.show_flyout(action, button)
    labels = []
    for i in range(bar.flyout_layout.count()):
        widget = bar.flyout_layout.itemAt(i).widget()
        labels += [label.text() for label in widget.findChildren(QLabel) if label.text()]
    return labels


def test_only_wired_targets_are_offered(toolbar):
    assert [b._flyout_label for b in toolbar._primary_buttons] == ["open_in", "print"]
    assert _offered(toolbar, "open_in") == ["Obsidian"]
    assert _offered(toolbar, "print") == ["PDF"]  # no printer set up: no placeholder printer


def test_the_path_reaches_obsidian_encoded():
    from PostFix.main import obsidian_uri

    assert obsidian_uri("/home/a/Notizen & Ideen/#1.md") == \
        "obsidian://open?path=%2Fhome%2Fa%2FNotizen%20%26%20Ideen%2F%231.md"
