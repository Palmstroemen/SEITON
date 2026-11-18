import QtQuick 2.15

// The dial on Now (2026-11-18; TimeDial: Controls has a Dial). It only shows whether the clock
// runs: while it counts, a green wedge grows round once a minute (no hand: 2026-11-19);
// standing, it stays where it was, grey. Today's time stands in
// the middle as h:mm h.
Item {
    id: dial
    objectName: "nowDial"
    property var theme: ({})
    property real todaySeconds: 0   // as the clock's view says it
    property real since: 0          // while it counts: where today's time would be naught
    property string label: ""       // under the time ("heute")
    property bool stopped: false    // stopped by hand: said under it, in red
    property string stoppedText: ""
    property bool running: since > 0  // the screen may say so at once, on a click
    property real now: Date.now() / 1000
    readonly property real seconds: running && since > 0 ? Math.max(0, now - since) : todaySeconds
    // The wedge is no measure, only a sign that it runs: it begins at the top and goes on with
    // the real time, a turn a minute; stopped it stays, started again it goes on from there -
    // not from the clock's seconds (it began anew "at 57 seconds", 2026-11-18).
    property real phaseBase: 0   // the angle it went on from
    property real phaseStart: 0  // when
    property real lastAngle: 0   // where it stood when the clock stopped
    readonly property real liveAngle: running ? (phaseBase + Math.max(0, now - phaseStart) * 6) % 360 : lastAngle
    readonly property real wedgeAngle: liveAngle
    function _goOn() {
        phaseBase = lastAngle
        phaseStart = Date.now() / 1000
        now = phaseStart
    }
    Component.onCompleted: if (running) _goOn()
    readonly property color wedgeColor: running ? "#3fae5f" : (theme.setupMuted || "#9aa0ad")

    implicitWidth: 200
    implicitHeight: 200

    Timer {
        interval: 250  // the wedge goes on smoothly
        repeat: true
        running: dial.running && dial.visible
        triggeredOnStart: true
        onTriggered: dial.now = Date.now() / 1000
    }
    onSecondsChanged: face.requestPaint()
    onLiveAngleChanged: {
        if (running) lastAngle = liveAngle
        face.requestPaint()
    }
    onRunningChanged: {
        if (running) _goOn()
        face.requestPaint()
    }

    Canvas {
        id: face
        anchors.fill: parent
        onPaint: {
            var g = getContext("2d")
            g.reset()
            var cx = width / 2, cy = height / 2
            var r = Math.min(width, height) / 2 - 4
            var top = -Math.PI / 2
            g.beginPath()  // the face
            g.arc(cx, cy, r, 0, 2 * Math.PI)
            g.fillStyle = dial.theme.panel || "#1b1d24"
            g.fill()
            g.lineWidth = 3
            g.strokeStyle = dial.theme.pillBorder || "#3a3f52"
            g.stroke()
            if (dial.wedgeAngle > 0) {  // the minute under way
                g.beginPath()
                g.moveTo(cx, cy)
                g.arc(cx, cy, r - 6, top, top + dial.wedgeAngle * Math.PI / 180)
                g.closePath()
                g.fillStyle = dial.wedgeColor
                g.globalAlpha = 0.75
                g.fill()
                g.globalAlpha = 1
            }
            g.strokeStyle = dial.theme.text || "#e6e6e6"  // the twelve marks
            for (var i = 0; i < 12; i++) {
                var a = top + i * Math.PI / 6
                g.lineWidth = i % 3 === 0 ? 3 : 1.5
                g.beginPath()
                g.moveTo(cx + Math.cos(a) * (r - 2), cy + Math.sin(a) * (r - 2))
                g.lineTo(cx + Math.cos(a) * (r - (i % 3 === 0 ? 12 : 8)), cy + Math.sin(a) * (r - (i % 3 === 0 ? 12 : 8)))
                g.stroke()
            }
        }
    }

    Column {  // the time today, h:mm, in the middle
        anchors.centerIn: parent
        anchors.verticalCenterOffset: dial.height * 0.18
        Text {
            objectName: "dialTime"
            anchors.horizontalCenter: parent.horizontalCenter
            text: Math.floor(dial.seconds / 3600) + ":" + ("0" + Math.floor(dial.seconds % 3600 / 60)).slice(-2) + " h"
            color: dial.theme.text || "#e6e6e6"
            font.pixelSize: 22
            font.bold: true
            style: Text.Outline
            styleColor: dial.theme.panel || "#1b1d24"
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: dial.label
            color: dial.theme.setupMuted || "#9aa0ad"
            font.pixelSize: 12
        }
        Text {
            objectName: "dialStopped"
            anchors.horizontalCenter: parent.horizontalCenter
            visible: dial.stopped
            text: dial.stoppedText
            color: "#e5484d"
            font.pixelSize: 13
            font.bold: true
        }
    }
}
