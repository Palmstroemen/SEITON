"""The files panel asks for more entries until the view is full, also when the first chunk
fits without scrolling ("docs/Prüfung 2026-11-18.md", F2): a big panel showed only 160 of
400 entries, with no scroll bar and no hint."""

import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


def test_a_big_panel_loads_until_it_is_full_or_all_are_there(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    qml = tmp_path / "host.qml"
    # As main.qml: 400 entries, handed over in chunks of 20 when the panel asks for more.
    qml.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'Item { id: host; width: 2560; height: 1400\n'
        '  property int total: 400\n'
        '  property int given: 0\n'
        '  ListModel { id: files }\n'
        '  function more() { var end = Math.min(total, given + 20)\n'
        '    for (var i = given; i < end; i++) files.append({name: "f" + i + ".txt", isDir: false, isEmbryo: false,\n'
        '      isVirtual: false, path: "/x/f" + i + ".txt"})\n'
        '    given = end }\n'
        '  FilesPanel { objectName: "panel"; anchors.fill: parent; itemsModel: files; currentPath: "/x"\n'
        '    onRequestMore: host.more() }\n'
        '  Component.onCompleted: more()\n'
        '}\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    root = view.rootObject()
    grid = next(i for i in _walk(root) if i.objectName() == "filesGrid")

    def settled():
        # Either everything is there, or the view is full and scrolling asks for the rest.
        return root.property("given") == 400 or grid.property("contentHeight") > grid.property("height")

    for _ in range(100):  # each chunk waits for a frame
        if settled():
            break
        QTest.qWait(50)
    given = root.property("given")
    view.close()
    assert given > 160, given  # more than the first chunks of main.qml
    assert given == 400 or grid.property("contentHeight") > grid.property("height"), given


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)
