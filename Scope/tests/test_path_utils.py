"""Paths in Scope (Scope/js/PathUtils.js), run in Qt's JS engine."""

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QJSEngine

PATH_UTILS_JS = Path(__file__).resolve().parents[1] / "js" / "PathUtils.js"


@pytest.fixture(scope="module")
def js():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841
    engine = QJSEngine()
    result = engine.evaluate(PATH_UTILS_JS.read_text(encoding="utf-8").replace(".pragma library", ""))
    assert not result.isError(), result.toString()

    def call(name, *args):
        value = engine.globalObject().property(name).call([engine.toScriptValue(a) for a in args])
        assert not value.isError(), value.toString()
        return value.toVariant()

    yield call


@pytest.mark.parametrize("place, removed, after", [
    ("/p/Haus/Küche", ["/p/Haus/Küche"], "/p/Haus"),           # the place itself
    ("/p/Haus/Küche/Herd", ["/p/Haus"], "/p"),                  # a parent of it
    ("/p/Haus/Küche", ["/p/Haus/Küchenplan.md"], "/p/Haus/Küche"),  # a name that only begins alike
    ("/p/Haus", ["/p/Haus/Küche", "/p/Garten"], "/p/Haus"),      # others
    ("/p/Haus/Küche", [], "/p/Haus/Küche"),
])
def test_the_place_after_a_removal(js, place, removed, after):
    # X3 (review 2026-11-18): deleting the folder one stands in left Scope, the session, the
    # Headline and the clock on a path that was gone.
    assert js("placeAfterRemoval", place, removed) == after


@pytest.mark.parametrize("place, moves, after", [
    ("/p/Haus/Küche", [{"source": "/p/Haus", "destination": "/p/Wohnen/Haus"}], "/p/Wohnen/Haus/Küche"),
    ("/p/Haus", [{"source": "/p/Haus", "destination": "/p/Heim"}], "/p/Heim"),        # renamed
    ("/p/Hausbau", [{"source": "/p/Haus", "destination": "/p/Heim"}], "/p/Hausbau"),
    ("/p/Haus", [], "/p/Haus"),
])
def test_the_place_after_a_move(js, place, moves, after):
    assert js("placeAfterMove", place, moves) == after
