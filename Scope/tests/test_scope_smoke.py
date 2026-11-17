"""Scope starts without QML errors: loaded as Scope.py loads it (with its backend, on a project of
its own), offscreen, without touching the real configuration (conftest.py)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

sys.path.insert(0, str(REPO))
from core.scope_api import ScopeApi  # noqa: E402
from Scope.Scope import load_scope  # noqa: E402


LAYOUT_LOOP = "Detected recursive rearrange"


@pytest.fixture(scope="module")
def started(tmp_path_factory):
    """What QML says about its own files while Scope starts, once for this module."""
    root = tmp_path_factory.mktemp("place") / "Dokumente"
    (root / ".seiton").mkdir(parents=True)
    (root / ".seiton" / "Project.md").write_text("# SEITON Project\n", encoding="utf-8")
    (root / "1_Info").mkdir()
    messages = []

    def handler(kind, _context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg) \
                and "file://" in message:
            messages.append(message)

    previous = qInstallMessageHandler(handler)
    try:
        app = QGuiApplication.instance() or QGuiApplication([])
        engine = load_scope(ScopeApi(str(root)), app)
        app.processEvents()
    finally:
        qInstallMessageHandler(previous)
    yield engine, messages
    # Leave nothing behind for the tests after this one: Scope started in German and installed
    # its translator into the application (they would all run in German), and its window.
    engine._backend.setLanguage("en")
    for window in engine.rootObjects():
        window.close()
    engine.deleteLater()
    app.processEvents()


def test_scope_starts_without_qml_errors(started):
    engine, messages = started
    assert engine.rootObjects(), "QML failed to load"
    errors = [m for m in messages if LAYOUT_LOOP not in m]
    assert not errors, "\n".join(errors)


@pytest.mark.xfail(strict=True, reason=(
    "FolderBrowser.qml, top row: the path bar's and the folders' widths are worked out from the "
    "row's own width (horizontalPathHostMaxWidth), so Qt's layout runs in a loop and gives up "
    "after two rounds. Harmless, but real; the row should share out its width itself."))
def test_the_top_row_has_no_layout_loop(started):
    _engine, messages = started
    assert not [m for m in messages if LAYOUT_LOOP in m]
