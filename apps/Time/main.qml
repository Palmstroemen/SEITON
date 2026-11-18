import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// The time screen (core/Dokumentation/Designdocument Time.md, 5): Now, Entries, Overview and
// the time tracking's settings. Its model is apps/Time/model.py (timeScreen).
ApplicationWindow {
    id: root
    objectName: "timeScreen"
    title: qsTr("Time")
    width: 640
    height: 520
    visible: true
    property var theme: timeScreen.colorScheme()
    property var nowView: timeScreen.now()
    // The project Entries and Overview show and Add writes to: the active one preselected, or
    // any chosen one; choosing moves neither the clock nor the Headline (Design 4.4, 5; Z7).
    property var projectChoices: timeScreen.projects()
    property string project: ""   // "" : the active project
    property var rows: timeScreen.entries(project)
    property int unreadableRows: timeScreen.unreadable(project)
    property string period: "month"
    property var overviewView: timeScreen.overview(project, period, "")
    readonly property int baseFont: 13
    color: theme.bg || "#0f1014"
    palette.window: theme.bg || "#0f1014"
    palette.windowText: theme.text || "#e6e6e6"
    palette.text: theme.text || "#e6e6e6"
    palette.base: theme.panel || "#1b1d24"
    palette.button: theme.smallButtonBg || "#2c3040"
    palette.buttonText: theme.smallButtonText || theme.text || "#e6e6e6"

    // "9:30" or "09:30" as the file writes it; empty: without a beginning.
    function startText(text) {
        var match = String(text || "").trim().match(/^(\d{1,2}):(\d{2})$/)
        return match ? ("0" + match[1]).slice(-2) + ":" + match[2] : ""
    }
    // A click on Start or Stop answers at once (2026-11-18): the dial runs or stands as wished
    // until the clock's view says the same, or for a few seconds at most.
    property string wish: ""
    onWishChanged: if (wish) wishTimer.restart()
    Timer { id: wishTimer; interval: 5000; onTriggered: root.wish = "" }
    function refresh() {
        nowView = timeScreen.now()
        if ((wish === "start" && nowView.since > 0) || (wish === "stop" && !(nowView.since > 0))) wish = ""
        rows = timeScreen.entries(project)
        unreadableRows = timeScreen.unreadable(project)
        overviewView = timeScreen.overview(project, period, "")
    }
    Connections {
        target: timeScreen
        function onChanged() { root.refresh() }
    }

    component Label2: Text {
        color: root.theme.text || "#e6e6e6"
        font.pixelSize: root.baseFont
    }
    component Muted: Text {
        color: root.theme.setupMuted || "#9aa0ad"
        font.pixelSize: root.baseFont - 1
        wrapMode: Text.WordWrap
    }

    header: ColumnLayout {
        spacing: 0
        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { objectName: "tabNow"; text: qsTr("Now") }
            TabButton { objectName: "tabEntries"; text: qsTr("Entries") }
            TabButton { objectName: "tabOverview"; text: qsTr("Overview") }
            TabButton { objectName: "tabSettings"; text: qsTr("Settings") }
        }
        RowLayout {  // which project Entries and Overview are about
            visible: tabs.currentIndex === 1 || tabs.currentIndex === 2
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.topMargin: 8
            spacing: 8
            Label2 { text: qsTr("Project") }
            ComboBox {
                objectName: "projectChoice"
                Layout.preferredWidth: 280
                textRole: "name"
                valueRole: "path"
                model: root.projectChoices
                onActivated: { root.project = currentIndex === 0 ? "" : currentValue; root.refresh() }
                // The list anew when it opens (not on every refresh, which would undo the choice).
                popup.onAboutToShow: {
                    var kept = root.project
                    root.projectChoices = timeScreen.projects()
                    currentIndex = kept === "" ? 0 : Math.max(0, indexOfValue(kept))
                }
            }
            Muted {
                visible: root.projectChoices.length === 0
                text: qsTr("No project: open one in the Headline, or work in one first.")
            }
        }
    }

    StackLayout {
        anchors.fill: parent
        anchors.margins: 16
        currentIndex: tabs.currentIndex

        ColumnLayout {  // Now: the active project, the clock, Start / Stop
            spacing: 10
            Label2 {
                objectName: "nowProject"
                text: root.nowView.projectName || qsTr("No active project")
                font.pixelSize: root.baseFont + 6
                font.bold: true
            }
            Column {  // in the middle of the page (the column is only as wide as its widest)
                Layout.preferredWidth: root.width - 32
                spacing: 10
                Row {  // first: for whom it counts - the system's picture and the name in the project
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 8
                    Rectangle {
                        width: 32
                        height: 32
                        radius: 16
                        color: root.theme.smallButtonBg || "#2c3040"
                        clip: true
                        Image {
                            objectName: "nowPicture"
                            anchors.fill: parent
                            source: root.nowView.picture || ""
                            visible: source != ""
                            fillMode: Image.PreserveAspectCrop
                            sourceSize.width: 64
                            sourceSize.height: 64
                        }
                        Text {  // without a picture: the first letter
                            anchors.centerIn: parent
                            visible: !(root.nowView.picture || "")
                            text: String(root.nowView.person || "?").charAt(0).toUpperCase()
                            color: root.theme.text || "#e6e6e6"
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }
                    Label2 {
                        objectName: "nowPerson"
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.nowView.person || ""
                    }
                }
                Row {  // Stop and Start, evenly, above the dial
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 12
                    readonly property real buttonWidth: Math.max(startButton.implicitWidth, stopButton.implicitWidth, 90)
                    Button {
                        id: stopButton
                        objectName: "stopButton"
                        width: parent.buttonWidth
                        text: qsTr("Stop")
                        // Also in a pause: a lunch break can become "stopped" (Z8).
                        enabled: root.nowView.clockRuns && root.nowView.clock !== "stopped" && root.nowView.clock !== "stands"
                        onClicked: { root.wish = "stop"; timeScreen.stop() }
                    }
                    Button {
                        id: startButton
                        objectName: "startButton"
                        width: parent.buttonWidth
                        text: qsTr("Start")
                        enabled: root.nowView.clockRuns && root.nowView.state !== "active"
                        onClicked: { root.wish = "start"; timeScreen.start() }
                    }
                }
                Muted {
                    objectName: "clockNotRunning"
                    anchors.horizontalCenter: parent.horizontalCenter
                    visible: !root.nowView.clockRuns
                    text: qsTr("The clock is not running.")
                }
                Button {
                    objectName: "startClockButton"
                    anchors.horizontalCenter: parent.horizontalCenter
                    visible: !root.nowView.clockRuns
                    text: qsTr("Start the clock")
                    onClicked: timeScreen.startClock()
                }
                TimeDial {  // today's time as a stopwatch (TimeDial.qml)
                    anchors.horizontalCenter: parent.horizontalCenter
                    theme: root.theme
                    todaySeconds: root.nowView.todaySeconds || 0
                    since: root.nowView.since || 0
                    running: root.wish === "start" || (root.wish !== "stop" && (root.nowView.since || 0) > 0)
                    label: qsTr("today")
                    // Stopped by hand, said in the dial: else one forgets it (Z8).
                    stopped: root.nowView.clock === "stopped"
                    stoppedText: qsTr("stopped")
                }
            }
            Item { Layout.fillHeight: true }
        }

        ColumnLayout {  // Entries: one's own rows of the active project, newest first
            spacing: 8
            RowLayout {  // Add what was done away from the computer
                spacing: 6
                TextField { id: addDay; objectName: "addDay"; text: timeScreen.today(); Layout.preferredWidth: 110 }
                TextField { id: addStart; objectName: "addStart"; placeholderText: qsTr("From"); Layout.preferredWidth: 70 }
                TextField { id: addDuration; objectName: "addDuration"; placeholderText: qsTr("1:30"); Layout.preferredWidth: 70 }
                TextField { id: addNote; objectName: "addNote"; placeholderText: qsTr("What"); Layout.fillWidth: true }
                Button {
                    objectName: "addButton"
                    text: qsTr("Add")
                    onClicked: {
                        var minutes = timeScreen.parseMinutes(addDuration.text)
                        if (timeScreen.add({ day: addDay.text, start: root.startText(addStart.text), minutes: minutes,
                                             note: addNote.text }, root.project)) {
                            addStart.text = ""
                            addDuration.text = ""
                            addNote.text = ""
                        }
                    }
                }
            }
            Muted { visible: root.rows.length === 0; text: qsTr("No entries yet.") }
            Muted {  // rows written by hand that could not be read stay in the file (Z11)
                objectName: "unreadableRows"
                visible: root.unreadableRows > 0
                text: qsTr("%n rows of the time files could not be read; they are not counted and stay as they are.", "", root.unreadableRows)
                Layout.fillWidth: true
            }
            ListView {
                objectName: "entryList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 2
                model: root.rows
                delegate: RowLayout {
                    id: entry
                    objectName: "entryRow"
                    width: ListView.view.width
                    spacing: 8
                    property bool editing: false
                    readonly property var row: modelData
                    Label2 { text: entry.row.day; Layout.preferredWidth: 90 }
                    Label2 { text: entry.row.start || "–"; Layout.preferredWidth: 45 }
                    Label2 {
                        visible: !entry.editing
                        text: Math.floor(entry.row.minutes / 60) + ":" + ("0" + entry.row.minutes % 60).slice(-2)
                        Layout.preferredWidth: 45
                    }
                    TextField {
                        id: editDuration
                        visible: entry.editing
                        text: Math.floor(entry.row.minutes / 60) + ":" + ("0" + entry.row.minutes % 60).slice(-2)
                        Layout.preferredWidth: 60
                    }
                    Muted { text: entry.row.kind; Layout.preferredWidth: 80 }
                    Label2 { visible: !entry.editing; text: entry.row.note; Layout.fillWidth: true; elide: Text.ElideRight }
                    TextField { id: editNote; visible: entry.editing; text: entry.row.note; Layout.fillWidth: true }
                    Button {
                        text: entry.editing ? qsTr("Save") : qsTr("Correct")
                        onClicked: {
                            if (!entry.editing) { entry.editing = true; return }
                            var changed = Object.assign({}, entry.row)
                            changed.minutes = timeScreen.parseMinutes(editDuration.text)
                            changed.note = editNote.text
                            if (timeScreen.change(entry.row, changed, root.project)) entry.editing = false
                        }
                    }
                    Button {
                        text: qsTr("Delete")
                        onClicked: timeScreen.remove(entry.row, root.project)
                    }
                }
            }
        }

        ColumnLayout {  // Overview: the project with its children, by period
            spacing: 8
            RowLayout {
                spacing: 6
                Repeater {
                    model: [{ value: "today", label: qsTr("Today") }, { value: "week", label: qsTr("This week") },
                            { value: "month", label: qsTr("This month") }, { value: "all", label: qsTr("All") }]
                    delegate: Button {
                        objectName: "period_" + modelData.value
                        text: modelData.label
                        checkable: true
                        checked: root.period === modelData.value
                        onClicked: { root.period = modelData.value; root.refresh() }
                    }
                }
            }
            Label2 {
                objectName: "overviewTotal"
                text: qsTr("In all: %1").arg(root.overviewView.total)
                font.bold: true
            }
            Muted {
                visible: root.overviewView.conflicts > 0
                text: qsTr("The cloud left %n conflict copies; they are not counted.", "", root.overviewView.conflicts)
            }
            Muted {
                visible: root.overviewView.unreadable > 0
                text: qsTr("%n rows of the time files could not be read; they are not counted and stay as they are.", "", root.overviewView.unreadable)
                Layout.fillWidth: true
            }
            Muted { text: qsTr("By project") }
            Repeater {
                model: root.overviewView.byProject
                delegate: Label2 { objectName: "overviewProject"; text: modelData.name + "  " + modelData.time }
            }
            Muted { text: qsTr("By person") }
            Repeater {
                model: root.overviewView.byPerson
                delegate: Label2 { objectName: "overviewPerson"; text: modelData.name + "  " + modelData.time }
            }
            Item { Layout.fillHeight: true }
        }

        ColumnLayout {  // the time tracking's settings
            spacing: 8
            RowLayout {
                Label2 { text: qsTr("Pause after (minutes)") }
                SpinBox {
                    objectName: "pauseMinutes"
                    from: 1; to: 60
                    value: Number(timeScreen.setting("Time/pauseMinutes"))
                    onValueModified: timeScreen.setSetting("Time/pauseMinutes", value)
                }
            }
            CheckBox {
                text: qsTr("Resume at the next input")
                checked: !!timeScreen.setting("Time/autoResume")
                onToggled: timeScreen.setSetting("Time/autoResume", checked)
            }
            CheckBox {
                text: qsTr("Ask while a video runs")
                checked: !!timeScreen.setting("Time/deadMan")
                onToggled: timeScreen.setSetting("Time/deadMan", checked)
            }
            RowLayout {
                Label2 { text: qsTr("Round to") }
                ComboBox {
                    objectName: "roundStep"
                    model: ["0", "5", "10", "15", "30"]
                    displayText: currentText === "0" ? qsTr("not at all") : qsTr("%1 minutes").arg(currentText)
                    currentIndex: Math.max(0, model.indexOf(String(timeScreen.setting("Time/roundStep"))))
                    onActivated: { timeScreen.setSetting("Time/roundStep", currentText); root.refresh() }
                }
                ComboBox {  // up or to the nearest (Design 4.4; Z7)
                    objectName: "roundMode"
                    textRole: "label"
                    valueRole: "value"
                    model: [{ value: "up", label: qsTr("up") }, { value: "nearest", label: qsTr("to the nearest") }]
                    Component.onCompleted: currentIndex = indexOfValue(String(timeScreen.setting("Time/roundMode")))
                    onActivated: { timeScreen.setSetting("Time/roundMode", currentValue); root.refresh() }
                }
                ComboBox {  // each stretch, or per day
                    objectName: "roundPer"
                    textRole: "label"
                    valueRole: "value"
                    model: [{ value: "stretch", label: qsTr("each stretch") }, { value: "day", label: qsTr("per day") }]
                    Component.onCompleted: currentIndex = indexOfValue(String(timeScreen.setting("Time/roundPer")))
                    onActivated: { timeScreen.setSetting("Time/roundPer", currentValue); root.refresh() }
                }
            }
            RowLayout {
                Label2 { text: qsTr("Beside the projects worked on last") }
                ComboBox {
                    objectName: "recentShows"
                    textRole: "label"
                    valueRole: "value"
                    model: [{ value: "total", label: qsTr("the time in all") }, { value: "week", label: qsTr("this week") },
                            { value: "today", label: qsTr("today") }]
                    Component.onCompleted: currentIndex = indexOfValue(String(timeScreen.setting("Time/recentShows")))
                    onActivated: timeScreen.setSetting("Time/recentShows", currentValue)
                }
            }
            Muted { text: qsTr("The clock takes changes when it starts anew.") }
            Item { Layout.fillHeight: true }
        }
    }
}
