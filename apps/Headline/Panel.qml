import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// The Headline's panel (apps/Scope/Designdocument Headline.md, 2): the same model as the line, as a
// list - the path to where one is, the standard folders, the perspectives, a row of buttons.
// Opened from the taskbar (above its button, upwards) or at the pointer, towards the room;
// a click outside closes it.
Window {
    id: panel
    objectName: "panel"
    property var view: ({})
    property var steps: []
    property var perspectives: []
    property var widgets: []
    property var theme: ({})
    property real embryoOpacity: 0.4
    // The line's counting (main.qml): a widget's counter to the second, as in the line.
    property var counted: null
    signal dropped(string payload, string path)  // something dropped onto one of its folders (H9)
    property int baseFont: 13
    readonly property int rowHeight: 28
    readonly property int panelWidth: 300

    flags: Qt.Popup | Qt.FramelessWindowHint
    color: theme.panel || "#202124"
    width: panelWidth
    // Cut to the room when too tall (popup_place), kept apart from the natural height.
    property int cutHeight: 0
    property var anchorRect: null  // where it was opened: placed there again when it changes
    height: cutHeight > 0 ? cutHeight : Math.min(content.implicitHeight + 16, maximumHeight)
    maximumHeight: Screen.desktopAvailableHeight * 0.8

    function refresh() {
        view = headline.view()
        // The path from the projects root: the way above it is in the line's dropdown only.
        steps = headline.climb().filter(function(step) { return !step.above })
        perspectives = headline.perspectives()
        widgets = headline.widgets()
    }
    // anchor: {x, y, width, height} on the screen (the applet's button), or null: the pointer.
    function openAt(anchor) {
        refresh()
        anchorRect = anchor || headline.pointerRect()
        place()
        show()
        raise()
        requestActivate()
    }

    // Towards the room from its anchor, cut to it when too tall; again whenever what it
    // shows changes while open, so it keeps growing away from the taskbar (review 2026-11-18, H3).
    function place() {
        if (!anchorRect) return
        // Laid out now, not later: its height decides where it goes (upwards above a taskbar).
        pathFlow.forceLayout()
        content.forceLayout()
        cutHeight = 0
        var placed = headline.placeDrop(anchorRect, width, Math.min(content.implicitHeight + 16, maximumHeight))
        x = placed.x
        y = placed.y
        cutHeight = placed.height !== undefined ? placed.height : 0
    }

    Connections {
        target: headline
        function onChanged() { if (panel.visible) { panel.refresh(); panel.place() } }
        function onWidgetsChanged() { if (panel.visible) { panel.widgets = headline.widgets(); panel.place() } }
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
                        batchSource: modelData.batch || ""
                        batchText: modelData.batchText || ""
                        projectBadge: !!modelData.project
                        smallProjectP: true  // a folder with a small P (2026-11-18)
                        label: modelData.name
                        style: "text"
                        compactHeight: panel.rowHeight - 4
                        fillColor: modelData.path === panel.view.cwd ? (panel.theme.smallButtonActiveBg || "#2c3a55")
                                                                      : (panel.theme.pill || "#2c3040")
                        strokeColor: panel.theme.pillBorder || "#3a3f52"
                        textColor: panel.theme.text || "#e6e6e6"
                        textSize: panel.baseFont
                        textBold: modelData.path === panel.view.cwd
                        allowDrops: true
                        onDropReceived: function(payload) { panel.dropped(payload, modelData.path) }
                        onActivate: headline.go(modelData.path)
                    }
                }
            }

            Heading { text: qsTr("Folders") }
            Repeater {  // the standard folders: born ones, and suggested ones pale
                model: panel.view.folders || []
                delegate: FolderItem {
                    objectName: "panelFolder"
                    hitAreaFullButton: true
                    width: content.width
                    label: modelData.name
                    style: "smallIcon"
                    centerName: true
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
                    // A click alone bears no embryo (Designdocument Headline.md, 3); a drop does.
                    allowDrops: true
                    onDropReceived: function(payload) { panel.dropped(payload, modelData.path) }
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
                    hitAreaFullButton: true
                    width: content.width
                    label: modelData.name
                    style: "smallIcon"
                    centerName: true
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

            Repeater {  // the widgets: what each shows, its answers, its last three, "More"
                model: panel.widgets
                delegate: Column {
                    id: widgetColumn
                    readonly property var entry: modelData
                    width: content.width
                    spacing: 2
                    Heading { text: widgetColumn.entry.name }
                    FolderItem {
                        objectName: "panelWidget"
                        hitAreaFullButton: true
                        width: content.width
                        label: widgetColumn.entry.counter && panel.counted ? panel.counted(widgetColumn.entry.counter)
                                                                           : widgetColumn.entry.text
                        style: "text"
                        compactHeight: panel.rowHeight
                        fillColor: widgetColumn.entry.state === "active" ? (panel.theme.smallButtonActiveBg || "#2c3a55")
                                                                        : (panel.theme.pill || "#2c3040")
                        strokeColor: widgetColumn.entry.state === "asking" ? (panel.theme.lensFrame || "#d97706")
                                                                          : (panel.theme.pillBorder || "#3a3f52")
                        textColor: panel.theme.text || "#e6e6e6"
                        textSize: panel.baseFont
                        onActivate: { headline.widgetOpen(widgetColumn.entry.id); panel.close() }
                    }
                    Text {
                        visible: !!widgetColumn.entry.question
                        text: widgetColumn.entry.question ? widgetColumn.entry.question.text : ""
                        color: panel.theme.text || "#e6e6e6"
                        font.pixelSize: panel.baseFont
                        wrapMode: Text.WordWrap
                        width: content.width
                    }
                    Row {
                        spacing: 4
                        Repeater {
                            model: widgetColumn.entry.question ? widgetColumn.entry.question.answers : []
                            delegate: FolderItem {
                                objectName: "panelWidgetAnswer"
                                label: modelData.label
                                style: "text"
                                compactHeight: panel.rowHeight
                                fillColor: panel.theme.smallButtonBg || "#2c3040"
                                strokeColor: panel.theme.lensFrame || "#d97706"
                                textColor: panel.theme.text || "#e6e6e6"
                                textSize: panel.baseFont
                                onActivate: headline.widgetTell(widgetColumn.entry.id, modelData.id)
                            }
                        }
                    }
                    Repeater {  // the last three; a click goes there
                        model: widgetColumn.entry.items.slice(0, 3)
                        delegate: FolderItem {
                            objectName: "panelWidgetItem"
                            hitAreaFullButton: true
                            width: content.width
                            label: modelData.text
                            style: "text"
                            compactHeight: panel.rowHeight - 2
                            fillColor: panel.theme.pill || "#2c3040"
                            strokeColor: panel.theme.pillBorder || "#3a3f52"
                            textColor: panel.theme.text || "#e6e6e6"
                            textSize: panel.baseFont
                            onActivate: headline.go(modelData.path)
                        }
                    }
                    FolderItem {  // all of them, to see and correct: the widget's own screen
                        objectName: "panelWidgetMore"
                        hitAreaFullButton: true
                        visible: widgetColumn.entry.items.length > 3
                        label: qsTr("More")
                        style: "text"
                        compactHeight: panel.rowHeight - 2
                        fillColor: panel.theme.smallButtonBg || "#2c3040"
                        strokeColor: panel.theme.smallButtonBorder || "#3a3f52"
                        textColor: panel.theme.smallButtonText || panel.theme.text || "#e6e6e6"
                        textSize: panel.baseFont
                        onActivate: { headline.widgetOpen(widgetColumn.entry.id); panel.close() }
                    }
                }
            }

            Tools {  // the buttons: setup, search, clipboard, time, light / dark
                topPadding: 8
                theme: panel.theme
                onUsed: panel.close()
            }
        }
    }
}
