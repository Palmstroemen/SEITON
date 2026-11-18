import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// A dropdown or a cascade of the Headline: a small window of its own, so the line's edge does
// not cut it off, placed towards the room (apps/Headline/popup_place.py).
Window {
    id: list
    property var entries: []          // [{name, path, ...}]
    property var theme: ({})
    property int rowHeight: 28
    property int baseFont: 13
    property string currentPath: ""   // marked in the list
    property bool showTools: false    // the Headline's tools on top (the way up, as M's tools)
    signal chosen(string path)
    signal dropped(string payload, string path)  // something dropped onto a row's folder (H9)
    signal hovered(Item item, var entry)

    // Not a popup: on X11 a second popup (the cascade) takes every click, and one could never
    // click back in the way up. A tool tip window takes no clicks from the others; the line
    // closes it when the pointer has left (main.qml, popupCloser).
    flags: Qt.ToolTip | Qt.FramelessWindowHint
    property bool pointerInside: false
    HoverHandler { onHoveredChanged: list.pointerInside = hovered }
    color: theme.panel || "#202124"
    width: Math.max(160, column.implicitWidth + 8)
    // Cut to the room when too tall (popup_place); kept apart so a short list after a cut
    // one is as tall as it is again (review 2026-11-18, H2).
    property int cutHeight: 0
    height: cutHeight > 0 ? cutHeight : column.implicitHeight + 8

    function _rectOf(item) {
        var p = item.mapToGlobal(0, 0)
        return {x: Math.round(p.x), y: Math.round(p.y), width: Math.round(item.width), height: Math.round(item.height)}
    }
    // The size as it is now: new entries are laid out first, not the list before them.
    function _natural() {
        cutHeight = 0
        column.forceLayout()
        return column.implicitHeight + 8
    }
    function _put(placed) {
        x = placed.x
        y = placed.y
        cutHeight = placed.height !== undefined ? placed.height : 0
        show()
        raise()
    }
    // band: the window the anchor sits in; the dropdown opens from its edge, not the anchor's.
    function dropBelow(anchor, band) {
        var rect = _rectOf(anchor)
        if (band) { rect.y = band.y; rect.height = band.height }
        var natural = _natural()
        _put(headline.placeDrop(rect, width, natural))
    }
    function besides(anchor) {
        var natural = _natural()
        _put(headline.placeSide(_rectOf(anchor), width, natural))
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 4
        contentHeight: column.implicitHeight
        clip: true
        Column {
            id: column
            spacing: 2
            Tools {
                visible: list.showTools
                theme: list.theme
                onUsed: list.close()
            }
            Repeater {
                id: rows
                model: list.entries
                delegate: FolderItem {
                    objectName: "dropRow"
                    hitAreaFullButton: true  // a menu row: the whole row takes the click
                    // Badges as in Scope's rows: a folder's own, the P of a project.
                    batchSource: modelData.batch || ""
                    batchText: modelData.batchText || ""
                    projectBadge: !!modelData.project
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
                    allowDrops: true
                    onDropReceived: function(payload) { list.dropped(payload, modelData.path) }
                    onActivate: list.chosen(modelData.path)
                    onHoverActiveChanged: if (hoverActive) list.hovered(this, modelData)
                }
            }
        }
    }
}
