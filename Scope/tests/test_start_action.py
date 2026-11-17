"""Scope started with a task (Scope.py --setup | --search | --clipboard): the Headline's buttons
open Scope where one is, on its back, with the search field, or in the clipboard
(Scope/Designdocument Headline.md, 2)."""

import os
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, QObject  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

sys.path.insert(0, str(REPO))
from core.brand import META_DIR  # noqa: E402
from core.scope_api import ScopeApi  # noqa: E402
from Scope.Scope import load_scope, start_action  # noqa: E402


@pytest.mark.parametrize("args, action", [
    (["/x"], ""), (["/x", "--setup"], "setup"), (["--search", "/x"], "search"),
    (["/x", "--clipboard"], "clipboard"), (["/x", "--nonsense"], ""),
])
def test_the_task_from_the_command_line(args, action):
    assert start_action(args) == action


@pytest.fixture
def place(tmp_path):
    root = tmp_path / "Dokumente"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# SEITON Project\n")
    return root


def _start(place, action):
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = load_scope(ScopeApi(str(place)), app, action=action)
    window = engine.rootObjects()[0]
    end = time.monotonic() + 1.5
    while time.monotonic() < end:  # the flip takes 0.9 s
        app.processEvents()
        time.sleep(0.02)
    return engine, window, app


def _gone(engine, window, app):
    engine._backend.setLanguage("en")
    window.close()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def test_setup_opens_on_the_back(place):
    engine, window, app = _start(place, "setup")
    try:
        assert window.property("setupShown") is True
    finally:
        _gone(engine, window, app)


def test_search_opens_the_search_field(place):
    engine, window, app = _start(place, "search")
    try:
        assert window.findChild(QObject, "templatesBrowserRoot").property("searchActive") is True
    finally:
        _gone(engine, window, app)


def test_without_a_task_neither(place):
    engine, window, app = _start(place, "")
    try:
        assert window.property("setupShown") is False
    finally:
        _gone(engine, window, app)
