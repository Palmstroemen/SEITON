"""Renaming a folder in place ("docs/Prüfung 2026-11-18.md", F9): it ends with Enter (also the
keypad's) or Escape. Drops on folders: test_folder_drags.py, test_folder_drop_targets.py.
Offscreen, temporary QML hosts only."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


def _items(window):
    return window.findChildren(QQuickItem)


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


@pytest.fixture
def host(tmp_path):
    engines = []

    def load(body):
        qml = tmp_path / "host.qml"
        qml.write_text(f'import QtQuick 2.15\nimport QtQuick.Controls 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
                       f'ApplicationWindow {{ width: 900; height: 400; visible: true\n{body}\n}}\n', encoding="utf-8")
        engine = QQmlApplicationEngine()
        engine.load(QUrl.fromLocalFile(str(qml)))
        assert engine.rootObjects()
        engines.append(engine)
        QTest.qWait(300)
        return engine.rootObjects()[0]

    yield load
    for engine in engines:
        for window in engine.rootObjects():
            window.close()


@pytest.mark.parametrize("key", [Qt.Key_Return, Qt.Key_Enter])
def test_renaming_in_place_ends_with_enter(host, key):
    window = host(
        '  property var accepted: []\n'
        '  property int canceled: 0\n'
        '  FolderItem { objectName: "item"; x: 40; y: 40; label: "Alt"; renameText: "Alt"; style: "smallIcon"\n'
        '    width: 240; height: 32\n'
        '    onRenameAccepted: function(name) { accepted = accepted.concat([name]) }\n'
        '    onRenameCanceled: canceled += 1 }\n')
    item = next(i for i in _items(window) if i.objectName() == "item")
    window.requestActivate()
    item.setProperty("renaming", True)
    QTest.qWait(50)

    for char in "Neu":  # keyClicks takes widgets only
        QTest.keyClick(window, char)  # the old name is selected: typing replaces it
    QTest.keyClick(window, key)

    assert _variant(window.property("accepted")) == ["Neu"]
    assert window.property("canceled") == 0


def test_escape_cancels_renaming_in_place(host):
    window = host(
        '  property var accepted: []\n'
        '  property int canceled: 0\n'
        '  FolderItem { objectName: "item"; x: 40; y: 40; label: "Alt"; renameText: "Alt"; style: "smallIcon"\n'
        '    width: 240; height: 32\n'
        '    onRenameAccepted: function(name) { accepted = accepted.concat([name]) }\n'
        '    onRenameCanceled: canceled += 1 }\n')
    item = next(i for i in _items(window) if i.objectName() == "item")
    window.requestActivate()
    item.setProperty("renaming", True)
    QTest.qWait(50)

    for char in "Neu":  # keyClicks takes widgets only
        QTest.keyClick(window, char)
    QTest.keyClick(window, Qt.Key_Escape)

    assert window.property("canceled") == 1 and _variant(window.property("accepted")) == []
