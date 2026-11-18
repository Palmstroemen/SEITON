import QtQuick 2.15

// A widget as an icon in the CWD's tab (apps/Headline/widgets.py, icon): drawn here, in the
// line's colours. While the widget is active it beats like a heart - the line is mostly hidden,
// one sees it counting when it comes; calm it is pale; warn (the clock stopped by hand) it is
// red and struck through. Its text is the tooltip; a click opens its own screen (2026-11-18).
Item {
    id: icon
    objectName: "widgetIcon"
    property string kind: "stopwatch"
    property string widgetId: ""
    property bool beating: false
    property bool warn: false
    property bool off: false  // registered, but not running (no view): greyed, a click opens it
    property string tip: ""
    property color color: "#e6e6e6"
    readonly property color warnColor: "#e5484d"
    signal opened(string widgetId)
    // Its tooltip, shown by the line in a window of its own (TipWindow.qml).
    signal tipWanted(var anchor, string text)
    signal tipGone()

    width: 16
    height: 16
    opacity: off ? 0.3 : (beating || warn ? 1.0 : 0.45)

    function open() { tipGone(); opened(widgetId) }
    function showTip() { tipWanted(icon, tip) }
    function hideTip() { tipGone() }

    Canvas {
        id: face
        anchors.fill: parent
        property color ink: icon.warn ? icon.warnColor : icon.color
        onInkChanged: requestPaint()
        onPaint: {
            var g = getContext("2d")
            g.reset()
            var w = width, h = height
            var r = Math.min(w, h) * 0.36
            var cx = w / 2, cy = h * 0.58
            g.strokeStyle = ink
            g.fillStyle = ink
            g.lineWidth = Math.max(1.4, w * 0.1)
            g.lineCap = "round"
            g.beginPath()  // the body
            g.arc(cx, cy, r, 0, 2 * Math.PI)
            g.stroke()
            g.fillRect(cx - w * 0.1, cy - r - h * 0.2, w * 0.2, h * 0.1)  // the crown
            g.beginPath()  // the hand
            g.moveTo(cx, cy)
            g.lineTo(cx + r * 0.45, cy - r * 0.6)
            g.stroke()
            if (icon.warn) {  // stopped by hand: struck through
                g.beginPath()
                g.moveTo(w * 0.08, h * 0.92)
                g.lineTo(w * 0.92, h * 0.12)
                g.stroke()
            }
        }
        Component.onCompleted: requestPaint()
        Connections {
            target: icon
            function onWarnChanged() { face.requestPaint() }
        }
    }

    // A heartbeat: two short beats, then rest.
    SequentialAnimation {
        running: icon.beating && icon.visible
        loops: Animation.Infinite
        onRunningChanged: if (!running) face.scale = 1
        NumberAnimation { target: face; property: "scale"; to: 1.22; duration: 90; easing.type: Easing.OutQuad }
        NumberAnimation { target: face; property: "scale"; to: 1.0; duration: 120; easing.type: Easing.InQuad }
        NumberAnimation { target: face; property: "scale"; to: 1.14; duration: 90; easing.type: Easing.OutQuad }
        NumberAnimation { target: face; property: "scale"; to: 1.0; duration: 140; easing.type: Easing.InQuad }
        PauseAnimation { duration: 760 }
    }

    MouseArea {  // over the tab's own: a click here opens the widget's screen, not the CWD
        anchors.fill: parent
        anchors.margins: -4
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: icon.open()
        onContainsMouseChanged: containsMouse ? icon.showTip() : icon.hideTip()
    }
}
