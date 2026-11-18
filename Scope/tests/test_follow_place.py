"""Scope stays on a place that is there (review 2026-11-18, X3): deleting the folder one stands
in (or a parent of it) goes to the parent; moving it goes along."""

import os
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, Q_ARG  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

sys.path.insert(0, str(REPO))
from core.brand import META_DIR, env_name  # noqa: E402
from core.scope_api import ScopeApi  # noqa: E402
from Scope.Scope import load_scope  # noqa: E402


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("SCOPE_START_DAEMON"), "0")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    root = tmp_path / "Dokumente"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# SEITON Project\n")
    (root / "Haus" / "Küche").mkdir(parents=True)
    (root / "Garten").mkdir()
    return root


def _settle(app, seconds=0.3):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.02)


@pytest.fixture
def scope(place):
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = load_scope(ScopeApi(str(place)), app)
    window = engine.rootObjects()[0]
    window._backend = engine._backend  # as Setup switches a setting: through Scope's backend
    _settle(app)
    yield window, app
    engine._backend.setLanguage("en")
    window.close()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def _call(window, name, *args):
    QMetaObject.invokeMethod(window, name, *[Q_ARG("QVariant", a) for a in args])


def test_deleting_the_folder_one_stands_in_goes_to_its_parent(scope, place):
    window, app = scope
    _call(window, "setCwp", str(place / "Haus" / "Küche"), "")
    _settle(app)
    assert window.property("cwp") == str(place / "Haus" / "Küche")
    _settle(app)
    _call(window, "performDeleteEntries", [str(place / "Haus")])
    _settle(app)
    assert not (place / "Haus").exists()
    assert window.property("cwp") == str(place)


def test_moving_the_folder_one_stands_in_goes_along(scope, place):
    window, app = scope
    _call(window, "setCwp", str(place / "Haus" / "Küche"), "")
    _settle(app)
    assert window.property("cwp") == str(place / "Haus" / "Küche")
    _settle(app)
    _call(window, "_performMove", [str(place / "Haus")], str(place / "Garten"))
    _settle(app)
    assert window.property("cwp") == str(place / "Garten" / "Haus" / "Küche")


def test_a_folder_dragged_moves_without_asking_unless_setup_says_so(scope, place):
    window, app = scope
    _call(window, "moveEntry", str(place / "Garten"), str(place / "Haus"))
    _settle(app)
    assert (place / "Haus" / "Garten").is_dir()  # moved, nobody asked
    assert window._backend.setSetting("General/askBeforeMove", True)
    _call(window, "moveEntry", str(place / "Haus" / "Garten"), str(place))
    _settle(app)
    assert (place / "Haus" / "Garten").is_dir()  # not yet: asked
    assert window.property("pendingMoveSources").toVariant() == [str(place / "Haus" / "Garten")]
