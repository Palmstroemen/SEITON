import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// A dropdown or a cascade of the Headline: a small window of its own, so the line's edge does
// not cut it off, placed towards the room (Headline/popup_place.py).
Window {
    id: list
    property var entries: []          // [{name, path, ...}]
    property var theme: ({})
    property int rowHeight: 28
    property int baseFont: 13
    property string currentPath: ""   // marked in the list
    signal chosen(string path)
    signal hovered(Item item, var entry)

    // Not a popup: on X11 a second popup (the cascade) takes every click, and one could never
    // click back in the way up. A tool tip window takes no clicks from the others; the line
    // closes it when the pointer has left (main.qml, popupCloser).
    flags: Qt.ToolTip | Qt.FramelessWindowHint
    property bool pointerInside: false
    HoverHandler { onHoveredChanged: list.pointerInside = hovered }
    color: theme.panel || "#202124"
    width: Math.max(160, column.implicitWidth + 8)
    height: column.implicitHeight + 8

    function _rectOf(item) {
        var p = item.mapToGlobal(0, 0)
        return {x: Math.round(p.x), y: Math.round(p.y), width: Math.round(item.width), height: Math.round(item.height)}
    }
    function _put(placed) {
        x = placed.x
        y = placed.y
        if (placed.height !== undefined) height = placed.height
        show()
        raise()
    }
    // band: the window the anchor sits in; the dropdown opens from its edge, not the anchor's.
    function dropBelow(anchor, band) {
        var rect = _rectOf(anchor)
        if (band) { rect.y = band.y; rect.height = band.height }
        _put(headline.placeDrop(rect, width, height))
    }
    function besides(anchor) { _put(headline.placeSide(_rectOf(anchor), width, height)) }

    Flickable {
        anchors.fill: parent
        anchors.margins: 4
        contentHeight: column.implicitHeight
        clip: true
        Column {
            id: column
            spacing: 2
            Repeater {
                id: rows
                model: list.entries
                delegate: FolderItem {
                    objectName: "dropRow"
                    hitAreaFullButton: true  // a menu row: the whole row takes the click
                    width: Math.max(implicitWidth, column.width)
                    label: modelData.name
                    style: "smallIcon"
                    compactHeight: list.rowHeight
                    iconSource: "image://theme/folder"
                    iconSourceHover: "image://theme/folder#active"
                    fillColor: list.theme.pill || "#2c3040"
                    strokeColor: modelData.path === list.currentPath ? (list.theme.accentSecondary || "#6cabcd")
                                                                     : (list.theme.pillBorder || "#3a3f52")
                    textColor: list.theme.text || "#e6e6e6"
                    textSize: list.baseFont
                    onActivate: list.chosen(modelData.path)
                    onHoverActiveChanged: if (hoverActive) list.hovered(this, modelData)
                }
            }
        }
    }
}
