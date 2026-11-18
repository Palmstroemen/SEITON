import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// The Headline's own settings (2026-11-18: a program of its own, SEITON's master - not a tab
// of Scope's Setup any more): where it sits, how it sits there, light or dark. What is
// SEITON-wide beyond that stays in Scope's Setup for now ("More settings in Scope").
Window {
    id: settingsWindow
    objectName: "headlineSettings"
    property var theme: ({})
    property int baseFont: 13
    property string place: "top"
    property string dock: "keep"
    property bool dark: true

    flags: Qt.Dialog | Qt.WindowStaysOnTopHint
    title: qsTr("Headline - Settings")
    color: theme.panel || "#202124"
    width: 440
    height: content.implicitHeight + 32

    function read() {
        place = String(headline.setting("Headline/place"))
        dock = String(headline.setting("Headline/dock"))
        dark = headline.setting("General/darkTheme") === true
    }
    function openCentered() {
        read()
        x = Screen.virtualX + (Screen.width - width) / 2
        y = Screen.virtualY + (Screen.height - height) / 3
        show()
        raise()
        requestActivate()
    }
    function keep(key, value) {
        if (headline.setSetting(key, value)) read()
    }

    component Heading: Text {
        color: settingsWindow.theme.textMuted || settingsWindow.theme.setupMuted || "#9aa0ad"
        font.pixelSize: settingsWindow.baseFont - 1
        font.bold: true
        topPadding: 6
    }
    component Choices: Row {
        id: choices
        property string prefix: ""   // objectName prefix: <prefix>_<value>
        property var options: []     // [{ value, label }]
        property string current: ""
        signal chosen(string value)
        spacing: 3
        Repeater {
            model: choices.options
            delegate: FolderItem {
                objectName: choices.prefix + "_" + modelData.value
                readonly property bool on: choices.current === modelData.value
                label: modelData.label
                style: "text"
                compactHeight: 28
                fillColor: on ? (settingsWindow.theme.smallButtonActiveBg || "#2c3a55") : (settingsWindow.theme.pill || "#2c3040")
                strokeColor: on ? (settingsWindow.theme.smallButtonActiveBorder || "#4a5675") : (settingsWindow.theme.pillBorder || "#3a3f52")
                textColor: settingsWindow.theme.text || "#e6e6e6"
                textSize: settingsWindow.baseFont
                textBold: on
                onActivate: choices.chosen(modelData.value)
            }
        }
    }

    Column {
        id: content
        x: 16
        y: 16
        width: settingsWindow.width - 32
        spacing: 8

        Heading { text: qsTr("Where") }
        Choices {
            // A line at the top edge, or a panel from the taskbar (as the start menu).
            prefix: "settingsPlace"
            options: [{ value: "top", label: qsTr("Top edge") }, { value: "taskbar", label: qsTr("From the taskbar") }]
            current: settingsWindow.place
            onChosen: function(value) { settingsWindow.keep("Headline/place", value) }
        }
        Heading { text: qsTr("At the top edge"); visible: settingsWindow.place === "top" }
        Choices {
            visible: settingsWindow.place === "top"
            // As a taskbar can: always there, keeping its room, or hiding itself until the
            // pointer touches the edge.
            prefix: "settingsDock"
            options: [{ value: "keep", label: qsTr("Always there") }, { value: "hide", label: qsTr("Hides itself") }]
            current: settingsWindow.dock
            onChosen: function(value) { settingsWindow.keep("Headline/dock", value) }
        }
        Text {
            visible: settingsWindow.place === "top"
            width: parent.width
            text: settingsWindow.dock === "keep" ? qsTr("Windows stop below the line.")
                                                 : qsTr("The line comes when the pointer touches the top edge.")
            color: settingsWindow.theme.textMuted || settingsWindow.theme.setupMuted || "#9aa0ad"
            font.pixelSize: settingsWindow.baseFont - 1
            wrapMode: Text.WordWrap
        }
        Heading { text: qsTr("Look") }
        Choices {
            // SEITON's look: Scope and SunTree follow it.
            prefix: "settingsLook"
            options: [{ value: "light", label: qsTr("Light") }, { value: "dark", label: qsTr("Dark") }]
            current: settingsWindow.dark ? "dark" : "light"
            onChosen: function(value) { settingsWindow.keep("General/darkTheme", value === "dark") }
        }
        Item { width: 1; height: 8 }
        Row {
            spacing: 6
            anchors.right: parent.right
            FolderItem {
                objectName: "settingsMoreInScope"
                label: qsTr("More settings in Scope")
                style: "text"
                compactHeight: 28
                fillColor: settingsWindow.theme.smallButtonBg || "#2c3040"
                strokeColor: settingsWindow.theme.pillBorder || "#3a3f52"
                textColor: settingsWindow.theme.text || "#e6e6e6"
                textSize: settingsWindow.baseFont
                onActivate: { headline.openScope("setup"); settingsWindow.close() }
            }
            FolderItem {
                objectName: "settingsDone"
                label: qsTr("Done")
                style: "text"
                compactHeight: 28
                fillColor: settingsWindow.theme.smallButtonActiveBg || "#2c3a55"
                strokeColor: settingsWindow.theme.smallButtonActiveBorder || "#4a5675"
                textColor: settingsWindow.theme.text || "#e6e6e6"
                textSize: settingsWindow.baseFont
                onActivate: settingsWindow.close()
            }
        }
    }
}
