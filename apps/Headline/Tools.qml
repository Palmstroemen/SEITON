import QtQuick 2.15
import QtQuick.Controls 2.15

// The Headline's tools (apps/Scope/Designdocument Headline.md, 2): small buttons on top of the way
// up and in the panel, as M's tools in Scope (apps/Scope/CwdTools.qml). Setup opens the Headline's
// own settings; search and the clipboard open Scope where one is; time opens the time screen;
// light / dark switches at once.
Row {
    id: tools
    property var theme: ({})
    property int buttonSize: 26
    signal used()  // a tool was used: the dropdown or panel may close
    spacing: 3

    component Tool: Rectangle {
        id: tool
        property string iconName: ""
        property string tip: ""
        signal activate(bool ctrlPressed, bool shiftPressed)
        width: tools.buttonSize
        height: tools.buttonSize
        radius: 5
        color: area.containsMouse ? Qt.lighter(tools.theme.smallButtonBg || "#2c3040", 1.2) : (tools.theme.smallButtonBg || "#2c3040")
        border.color: tools.theme.smallButtonBorder || "#3a3f52"
        Image {
            anchors.centerIn: parent
            width: tools.buttonSize - 8
            height: width
            sourceSize.width: width
            sourceSize.height: height
            source: "image://theme/" + tool.iconName
        }
        MouseArea {
            id: area
            anchors.fill: parent
            hoverEnabled: true
            onClicked: tool.activate(false, false)
        }
        ToolTip.visible: area.containsMouse
        ToolTip.text: tool.tip
        ToolTip.delay: 400
    }

    Tool {
        objectName: "toolScope"
        iconName: "system-file-manager"
        tip: qsTr("Open in Scope")
        onActivate: { headline.openScope(""); tools.used() }
    }
    Tool {
        objectName: "toolSetup"
        iconName: "preferences-system"
        tip: qsTr("Setup")
        onActivate: { headline.openSetup(); tools.used() }
    }
    Tool {
        objectName: "toolSearch"
        iconName: "system-search"
        tip: qsTr("Search")
        onActivate: { headline.openScope("search"); tools.used() }
    }
    Tool {
        objectName: "toolClipboard"
        iconName: "edit-paste"
        tip: qsTr("Clipboard")
        onActivate: { headline.openScope("clipboard"); tools.used() }
    }
    Tool {
        objectName: "toolTime"
        iconName: "appointment-soon"
        tip: qsTr("Time tracking")
        onActivate: { headline.openTime(); tools.used() }
    }
    Tool {
        objectName: "toolTheme"
        iconName: "weather-clear-night"
        tip: qsTr("Light / dark")
        onActivate: headline.switchTheme()
    }
}
