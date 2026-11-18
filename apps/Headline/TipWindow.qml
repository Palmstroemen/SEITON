import QtQuick 2.15
import QtQuick.Window 2.15

// A tooltip as a window of its own, below the line (2026-11-18): Qt Quick's ToolTip is a popup
// inside its window, and the line's window is only as high as the line - the bubble was cut
// off at the bottom. As the dropdowns (DropList.qml), it takes no clicks and no focus.
Window {
    id: tip
    objectName: "tipWindow"
    property var theme: ({})
    property int baseFont: 13
    property string text: ""
    property var pending: null  // {anchor, text}, shown after a short while
    property var band: null  // the line's window: the tip comes below it

    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
    color: theme.panel || "#202124"
    width: label.implicitWidth + 16
    height: label.implicitHeight + 10

    // Show text for anchor (an item in the line) after a short while; below the line, under
    // the anchor, kept on the screen.
    function ask(anchor, text) {
        if (!anchor || !text) { hide(); return }
        pending = { anchor: anchor, text: text }
        delay.restart()
    }
    function hide() {
        delay.stop()
        pending = null
        visible = false
    }
    function _show() {
        if (!pending) return
        tip.text = pending.text
        var at = pending.anchor.mapToGlobal(0, 0)
        var below = band ? band.y + band.height : at.y + pending.anchor.height
        var screen = tip.screen
        var right = screen ? screen.virtualX + screen.width : at.x + width
        tip.x = Math.max(screen ? screen.virtualX : 0, Math.min(at.x, right - width - 4))
        tip.y = below + 4
        visible = true
    }

    Timer { id: delay; interval: 400; onTriggered: tip._show() }

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: tip.theme.pillBorder || "#3a3f52"
        border.width: 1
    }
    Text {
        id: label
        x: 8
        y: 5
        text: tip.text
        color: tip.theme.text || "#e6e6e6"
        font.pixelSize: tip.baseFont
    }
}
