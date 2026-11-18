import QtQuick 2.15

// The dial on Now (2026-11-18; TimeDial: Controls has a Dial): today's time in the active project as a stopwatch. One turn is an
// hour: a green wedge from the top grows with the hour under way, the full hours stand in the
// middle; while the clock counts, a thin seconds hand runs - one sees at a glance that it counts.
// Standing, the wedge is grey and the hand gone.
Item {
    id: dial
    objectName: "nowDial"
    property var theme: ({})
    property real todaySeconds: 0   // as the clock's view says it
    property real since: 0          // while it counts: where today's time would be naught
    property string label: ""       // under the time ("heute")
    property bool stopped: false    // stopped by hand: said under it, in red
    property string stoppedText: ""
    readonly property bool running: since > 0
    property real now: Date.now() / 1000
    readonly property real seconds: running ? Math.max(0, now - since) : todaySeconds
    readonly property real wedgeAngle: (seconds % 3600) / 3600 * 360
    readonly property color wedgeColor: running ? "#3fae5f" : (theme.setupMuted || "#9aa0ad")

    implicitWidth: 200
    implicitHeight: 200

    Timer {
        interval: 1000
        repeat: true
        running: dial.running && dial.visible
        triggeredOnStart: true
        onTriggered: dial.now = Date.now() / 1000
    }
    onSecondsChanged: face.requestPaint()
    onRunningChanged: face.requestPaint()

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
            if (dial.wedgeAngle > 0) {  // the hour under way
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
            if (dial.running) {  // the seconds hand
                var s = top + (Math.floor(dial.seconds) % 60) * Math.PI / 30
                g.strokeStyle = "#e2402b"
                g.lineWidth = 2
                g.lineCap = "round"
                g.beginPath()
                g.moveTo(cx, cy)
                g.lineTo(cx + Math.cos(s) * (r - 10), cy + Math.sin(s) * (r - 10))
                g.stroke()
                g.beginPath()
                g.arc(cx, cy, 4, 0, 2 * Math.PI)
                g.fillStyle = "#e2402b"
                g.fill()
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
