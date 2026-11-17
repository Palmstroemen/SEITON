import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// The time screen (core/Dokumentation/Designdocument Time.md, 5): Now, Entries, Overview and
// the time tracking's settings. Its model is Time/model.py (timeScreen).
ApplicationWindow {
    id: root
    objectName: "timeScreen"
    title: qsTr("Time")
    width: 640
    height: 520
    visible: true
    property var theme: timeScreen.colorScheme()
    property var nowView: timeScreen.now()
    property var rows: timeScreen.entries("")
    property string period: "month"
    property var overviewView: timeScreen.overview("", period, "")
    readonly property int baseFont: 13
    color: theme.bg || "#0f1014"
    palette.window: theme.bg || "#0f1014"
    palette.windowText: theme.text || "#e6e6e6"
    palette.text: theme.text || "#e6e6e6"
    palette.base: theme.panel || "#1b1d24"
    palette.button: theme.smallButtonBg || "#2c3040"
    palette.buttonText: theme.smallButtonText || theme.text || "#e6e6e6"

    function refresh() {
        nowView = timeScreen.now()
        rows = timeScreen.entries("")
        overviewView = timeScreen.overview("", period, "")
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

    header: TabBar {
        id: tabs
        TabButton { objectName: "tabNow"; text: qsTr("Now") }
        TabButton { objectName: "tabEntries"; text: qsTr("Entries") }
        TabButton { objectName: "tabOverview"; text: qsTr("Overview") }
        TabButton { objectName: "tabSettings"; text: qsTr("Settings") }
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
            Label2 {
                objectName: "nowText"
                visible: root.nowView.clockRuns
                text: root.nowView.text
            }
            Muted {
                objectName: "clockNotRunning"
                visible: !root.nowView.clockRuns
                text: qsTr("The clock is not running.")
            }
            RowLayout {
                spacing: 8
                Button {
                    objectName: "startButton"
                    text: qsTr("Start")
                    enabled: root.nowView.clockRuns && root.nowView.state !== "active"
                    onClicked: timeScreen.start()
                }
                Button {
                    objectName: "stopButton"
                    text: qsTr("Stop")
                    enabled: root.nowView.clockRuns && root.nowView.state !== "calm"
                    onClicked: timeScreen.stop()
                }
                Button {
                    objectName: "startClockButton"
                    visible: !root.nowView.clockRuns
                    text: qsTr("Start the clock")
                    onClicked: timeScreen.startClock()
                }
            }
            Item { Layout.fillHeight: true }
        }

        ColumnLayout {  // Entries: one's own rows of the active project, newest first
            spacing: 8
            RowLayout {  // Add what was done away from the computer
                spacing: 6
                TextField { id: addDay; objectName: "addDay"; text: timeScreen.today(); Layout.preferredWidth: 110 }
                TextField { id: addDuration; objectName: "addDuration"; placeholderText: qsTr("1:30"); Layout.preferredWidth: 70 }
                TextField { id: addNote; objectName: "addNote"; placeholderText: qsTr("What"); Layout.fillWidth: true }
                Button {
                    objectName: "addButton"
                    text: qsTr("Add")
                    onClicked: {
                        var minutes = timeScreen.parseMinutes(addDuration.text)
                        if (timeScreen.add({ day: addDay.text, start: "", minutes: minutes, note: addNote.text }, "")) {
                            addDuration.text = ""
                            addNote.text = ""
                        }
                    }
                }
            }
            Muted { visible: root.rows.length === 0; text: qsTr("No entries yet.") }
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
                            if (timeScreen.change(entry.row, changed, "")) entry.editing = false
                        }
                    }
                    Button {
                        text: qsTr("Delete")
                        onClicked: timeScreen.remove(entry.row, "")
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
                text: qsTr("The cloud left %n conflict copies; they are counted apart.", "", root.overviewView.conflicts)
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
