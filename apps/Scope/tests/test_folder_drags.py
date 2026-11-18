"""Dragging in Scope's folder rows ("docs/Prüfung 2026-11-18.md", F3, F6): a dragged folder
button goes back to its place when the drag ends; in the V view a file dropped on a folder of
the path goes into that folder, as in the H view (it went into the clipboard)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow  # noqa: F401  (the window as a QQuickWindow)
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _v(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _drag(window, start, end, steps=12):
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
    QTest.qWait(30)
    for s in range(1, steps + 1):
        QTest.mouseMove(window, QPoint(start.x() + (end.x() - start.x()) * s // steps,
                                       start.y() + (end.y() - start.y()) * s // steps))
        QTest.qWait(30)
    QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
    QTest.qWait(80)


def _centre(item):
    return item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()


@pytest.fixture
def scene(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    made = []

    def make(vertical):
        host = tmp_path / f"host{len(made)}.qml"
        host.write_text(
            f'import QtQuick 2.15\nimport QtQuick.Controls 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
            'ApplicationWindow { width: 900; height: 700; visible: true\n'
            '  property var log: []\n'
            '  FolderBrowser { objectName: "browser"; width: 400; height: 500\n'
            '    path: "/p/Projekte/Job/Sub"; pathDisplayPrefix: "/p/Projekte"; usePathBar: true; allowDrops: true\n'
            f'    verticalView: {str(vertical).lower()}; foldersShown: true; showModeToggle: false\n'
            '    showSearchToggle: false; showClipboardButton: false\n'
            '    folders: ["Aufträge", "Belege"]\n'
            '    childrenProvider: function(p) { return [] }\n'
            '    onMoveEntryRequested: function(s, t) { log = log.concat(["move " + s + " -> " + t]) }\n'
            '    onClipboardDropRequested: function(s) { log = log.concat(["clipboard " + s]) }\n'
            '  }\n'
            '  FolderItem { objectName: "src"; x: 600; y: 600; width: 120; label: "file.txt"\n'
            '    dragEnabled: true; dragPayload: "/x/file.txt" }\n'
            '}\n', encoding="utf-8")
        engine = QQmlApplicationEngine()
        engine.load(QUrl.fromLocalFile(str(host)))
        window = engine.rootObjects()[0]
        QTest.qWait(300)
        made.append((engine, window))
        return window

    yield make
    for _engine, window in made:
        window.close()


def _labelled(window, name):
    return next(i for i in _walk(window.contentItem())
                if i.property("label") == name and i.isVisible() and i.width() > 0)


def test_a_dragged_button_goes_back_to_its_place(scene):
    window = scene(vertical=False)
    src = next(i for i in _walk(window.contentItem()) if i.objectName() == "src")
    before = (src.x(), src.y())
    _drag(window, _centre(src), QPoint(300, 650))  # into nothing
    assert (src.x(), src.y()) == before


@pytest.mark.parametrize("target", ["Job", "Sub"])
def test_in_the_v_view_a_drop_on_the_path_goes_into_that_folder(scene, target):
    window = scene(vertical=True)
    src = next(i for i in _walk(window.contentItem()) if i.objectName() == "src")
    _drag(window, _centre(src), _centre(_labelled(window, target)))
    log = _v(window.property("log"))
    assert log and log[-1].startswith("move /x/file.txt -> ") and log[-1].endswith(target), log


def test_a_drop_on_a_virtual_folder_goes_to_the_sorted_folder(tmp_path):
    """"docs/Prüfung 2026-11-18.md", F4: a year group of a sorted folder is no folder yet; a
    drop there goes into the sorted folder (which files it), not to a path that is not there."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    host = tmp_path / "panel.qml"
    host.write_text(
        f'import QtQuick 2.15\nimport QtQuick.Controls 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'ApplicationWindow { width: 1000; height: 700; visible: true\n'
        '  property var log: []\n'
        '  ListModel { id: files\n'
        '    ListElement { name: "Real"; isDir: true; isEmbryo: false; isVirtual: false; path: "/x/Real" }\n'
        '    ListElement { name: "2025"; isDir: true; isEmbryo: false; isVirtual: true; path: "/x/2025" }\n'
        '  }\n'
        '  FilesPanel { width: 1000; height: 500; itemsModel: files; showFolders: true; currentPath: "/x"\n'
        '    onMoveEntriesRequested: function(p, t) { log = log.concat([p + " -> " + t]) } }\n'
        '  FolderItem { objectName: "src"; x: 600; y: 600; width: 120; label: "file.txt"\n'
        '    dragEnabled: true; dragPayload: "/y/file.txt" }\n'
        '}\n', encoding="utf-8")
    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(host)))
    window = engine.rootObjects()[0]
    QTest.qWait(300)
    try:
        src = next(i for i in _walk(window.contentItem()) if i.objectName() == "src")
        for label, target in (("2025", "/x"), ("Real", "/x/Real")):
            entry = next(i for i in _walk(window.contentItem())
                         if i.property("label") == label and i.property("itemPath") is not None)
            _drag(window, _centre(src), _centre(entry))
            assert _v(window.property("log"))[-1] == f"/y/file.txt -> {target}", _v(window.property("log"))
    finally:
        window.close()


def test_a_hover_still_waiting_does_not_win_over_the_files_panel(scene):
    """"docs/Prüfung 2026-11-18.md", F5: on the way down into the FilesPanel the pointer crosses
    the preview row; a hover still waiting there must not open another row after the panel
    took the folder."""
    from PySide6.QtCore import Q_ARG, QMetaObject

    window = scene(vertical=False)
    browser = next(i for i in _walk(window.contentItem()) if i.objectName() == "browser")
    QMetaObject.invokeMethod(browser, "updatePreviewFromHover", Q_ARG("QVariant", 1), Q_ARG("QVariant", "/p/Projekte/Job/Sub/Belege"),
                             Q_ARG("QVariant", None), Q_ARG("QVariant", "#ffffff"), Q_ARG("QVariant", 10),
                             Q_ARG("QVariant", 10), Q_ARG("QVariant", False))
    assert browser.property("previewHoverApplyScheduled") is True
    QMetaObject.invokeMethod(browser, "cancelPendingPreviewHover")
    assert browser.property("previewHoverApplyScheduled") is False
    QTest.qWait(400)  # longer than the hover delay: nothing applies any more
    assert browser.property("previewPendingPath") in ("", "/p/Projekte/Job/Sub/Belege")
    assert not browser.property("previewHoverApplyScheduled")
    main = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")
    flush = main[main.index("function flushFilesPreview"):main.index("function commitCTD")]
    assert flush.index("cancelPendingPreviewHover") < flush.index("highlightedPreviewPath")
