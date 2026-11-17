import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// The Headline's panel (Scope/Designdocument Headline.md, 2): the same model as the line, as a
// list - the path to where one is, the standard folders, the perspectives, a row of buttons.
// Opened from the taskbar (above its button, upwards) or at the pointer, towards the room;
// a click outside closes it.
Window {
    id: panel
    objectName: "panel"
    property var view: ({})
    property var steps: []
    property var perspectives: []
    property var theme: ({})
    property real embryoOpacity: 0.4
    property int baseFont: 13
    readonly property int rowHeight: 28
    readonly property int panelWidth: 300

    flags: Qt.Popup | Qt.FramelessWindowHint
    color: theme.panel || "#202124"
    width: panelWidth
    height: Math.min(content.implicitHeight + 16, maximumHeight)
    maximumHeight: Screen.desktopAvailableHeight * 0.8

    function refresh() {
        view = headline.view()
        steps = headline.climb()
        perspectives = headline.perspectives()
    }
    // anchor: {x, y, width, height} on the screen (the applet's button), or null: the pointer.
    function openAt(anchor) {
        refresh()
        // Laid out now, not later: its height decides where it goes (upwards above a taskbar).
        pathFlow.forceLayout()
        content.forceLayout()
        var rect = anchor || headline.pointerRect()
        var placed = headline.placeDrop(rect, width, Math.min(content.implicitHeight + 16, maximumHeight))
        x = placed.x
        y = placed.y
        show()
        raise()
        requestActivate()
    }

    Connections {
        target: headline
        function onChanged() { if (panel.visible) panel.refresh() }
    }

    component Heading: Text {
        color: panel.theme.textMuted || panel.theme.setupMuted || "#9aa0ad"
        font.pixelSize: panel.baseFont - 1
        font.bold: true
        topPadding: 6
    }

    Flickable {
        anchors.fill: parent
        anchors.margins: 8
        contentHeight: content.implicitHeight
        clip: true

        Column {
            id: content
            width: parent.width
            spacing: 4

            Flow {  // the path to where one is, each part a step
                id: pathFlow
                width: parent.width
                spacing: 2
                Repeater {
                    model: panel.steps
                    delegate: FolderItem {
                        objectName: "panelPath"
                        label: modelData.name
                        style: "text"
                        compactHeight: panel.rowHeight - 4
                        fillColor: modelData.path === panel.view.cwd ? (panel.theme.smallButtonActiveBg || "#2c3a55")
                                                                      : (panel.theme.pill || "#2c3040")
                        strokeColor: panel.theme.pillBorder || "#3a3f52"
                        textColor: panel.theme.text || "#e6e6e6"
                        textSize: panel.baseFont
                        textBold: modelData.path === panel.view.cwd
                        onActivate: headline.go(modelData.path)
                    }
                }
            }

            Heading { text: qsTr("Folders") }
            Repeater {  // the standard folders: born ones, and suggested ones pale
                model: panel.view.folders || []
                delegate: FolderItem {
                    objectName: "panelFolder"
                    width: content.width
                    label: modelData.name
                    style: "smallIcon"
                    compactHeight: panel.rowHeight
                    iconSource: "image://theme/folder"
                    iconSourceHover: "image://theme/folder#active"
                    batchSource: modelData.batch || ""
                    batchText: modelData.batchText || ""
                    opacity: modelData.embryo ? panel.embryoOpacity : 1.0
                    fillColor: panel.theme.pill || "#2c3040"
                    strokeColor: panel.theme.pillBorder || "#3a3f52"
                    textColor: panel.theme.text || "#e6e6e6"
                    textSize: panel.baseFont
                    // A click alone bears no embryo (Designdocument Headline.md, 3).
                    onActivate: if (!modelData.embryo) headline.go(modelData.path)
                }
            }

            Heading {
                text: qsTr("Perspectives")
                visible: panel.perspectives.length > 0
            }
            Repeater {  // a click puts the lens on there, on the one worn takes it off
                model: panel.perspectives
                delegate: FolderItem {
                    objectName: "panelPerspective"
                    width: content.width
                    label: modelData.name
                    style: "smallIcon"
                    compactHeight: panel.rowHeight
                    iconSource: "image://theme/folder-saved-search"
                    fillColor: panel.theme.pill || "#2c3040"
                    strokeColor: modelData.active ? (panel.theme.lensFrame || "#d97706") : (panel.theme.pillBorder || "#3a3f52")
                    textColor: panel.theme.text || "#e6e6e6"
                    textSize: panel.baseFont
                    textBold: modelData.active
                    onActivate: headline.wear(modelData.lens)
                }
            }

            Row {  // the buttons
                topPadding: 8
                spacing: 4
                FolderItem {
                    objectName: "panelOpenScope"
                    label: qsTr("Open in Scope")
                    style: "text"
                    compactHeight: panel.rowHeight
                    fillColor: panel.theme.smallButtonBg || "#2c3040"
                    strokeColor: panel.theme.smallButtonBorder || "#3a3f52"
                    textColor: panel.theme.smallButtonText || panel.theme.text || "#e6e6e6"
                    textSize: panel.baseFont
                    onActivate: { headline.openScope(); panel.close() }
                }
            }
        }
    }
}
