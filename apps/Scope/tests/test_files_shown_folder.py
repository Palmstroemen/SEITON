"""The FilesPanel shows the folder it shows, not the CWD ("docs/Prüfung 2026-11-18.md", S1,
S2): Scope as Scope.py loads it, the CWD at the project, a subfolder shown (a click in the rows,
the preview, a lens). Its full list arrives (with tags), and the tag filter filters it."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication  # noqa: E402

sys.path.insert(0, str(REPO))
from core.scope_api import ScopeApi  # noqa: E402
from core.tags import write_tags  # noqa: E402
from apps.Scope.Scope import close_scope, load_scope  # noqa: E402


@pytest.fixture
def scope(tmp_path):
    root = tmp_path / "Dokumente"
    (root / ".seiton").mkdir(parents=True)
    (root / ".seiton" / "Project.md").write_text("# SEITON Project\n", encoding="utf-8")
    (root / "Oben.md").write_text("oben\n")
    write_tags(root / "Oben.md", {"wichtig": None})
    sub = root / "Unten"
    sub.mkdir()
    (sub / "Brief.md").write_text("brief\n")
    (sub / "Notiz.md").write_text("notiz\n")
    write_tags(sub / "Brief.md", {"wichtig": None})
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = load_scope(ScopeApi(str(root)), app)
    window = engine.rootObjects()[0]
    app.processEvents()
    yield app, window, root, sub
    close_scope(engine, app)


def _wait(app, condition, seconds=8):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.02)
    return False


def _list(value):
    value = value.toVariant() if hasattr(value, "toVariant") else value
    return [e.toVariant() if hasattr(e, "toVariant") else e for e in (value or [])]


def _entries(window):
    return _list(window.property("fileItemsAll"))


def _show(window, folder):
    """As a click in the rows does: the FilesPanel shows folder, the CWD stays."""
    from PySide6.QtCore import QMetaObject

    window.setProperty("committedCTDPath", str(folder))
    QMetaObject.invokeMethod(window, "updateFiles")


def _by_name(window):
    return {e["name"]: e for e in _entries(window)}


def test_a_shown_subfolder_gets_its_full_list(scope):
    app, window, root, sub = scope
    _show(window, sub)
    assert _wait(app, lambda: (_by_name(window).get("Brief.md") or {}).get("tags") == ["wichtig"]), _by_name(window)


def test_the_tag_filter_filters_the_shown_folder(scope):
    app, window, root, sub = scope
    _show(window, sub)
    _wait(app, lambda: "Notiz.md" in _by_name(window))
    window.setProperty("selectedTags", ["wichtig"])
    app.processEvents()
    names = sorted(e["name"] for e in _list(window.property("fileItemsRaw")))
    assert names == ["Brief.md"], names


def _dialog(window, kind):
    from PySide6.QtCore import QObject

    return next(o for o in window.findChildren(QObject) if o.metaObject().className().startswith(kind))


def test_moving_into_a_new_folder_makes_it_in_the_shown_folder(scope):
    """"docs/Prüfung 2026-11-18.md", S4: the new folder came into the CWD."""
    from PySide6.QtCore import QMetaObject

    app, window, root, sub = scope
    _show(window, sub)
    _wait(app, lambda: "Notiz.md" in _by_name(window))
    window.setProperty("pendingFolderBatchSources", [str(sub / "Notiz.md")])
    window.setProperty("pendingFolderBatchName", "Sammlung")
    dialog = _dialog(window, "MoveSelectedFoldersDialog")
    QMetaObject.invokeMethod(dialog, "open")
    app.processEvents()
    QMetaObject.invokeMethod(dialog, "accept")
    assert _wait(app, lambda: (sub / "Sammlung" / "Notiz.md").exists())
    assert not (root / "Sammlung").exists()
