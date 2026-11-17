import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// The Headline's line (Scope/Designdocument Headline.md, 2): the CWD with its cascade to climb,
// the standard folders there, as many as fit, the rest behind ». At the top edge as a dock
// (Headline/x11_dock.py): always there, or a thin edge that opens when the pointer comes.
Window {
    id: line
    objectName: "headlineLine"
    property var view: headline.view()
    property var theme: headline.colorScheme()
    property real embryoOpacity: headline.embryoOpacity()
    readonly property int lineHeight: 30
    readonly property int baseFont: 13
    readonly property var folders: view.folders || []
    // How many folders fit beside the CWD and the » (worked out from their widths).
    property int shownCount: folders.length
    // Always there ("keep") or hiding itself ("hide"), as set in Setup (tab Headline).
    property string dockMode: headline.dockMode()
    readonly property int edgeHeight: 2
    property bool pointerInside: false
    readonly property bool popupOpen: climbList.visible || cascade.visible || moreList.visible
    readonly property bool expanded: dockMode === "keep" || pointerInside || popupOpen

    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    x: Screen.virtualX
    y: Screen.virtualY
    width: Screen.width
    height: expanded ? lineHeight : edgeHeight
    // From the taskbar (Setup) there is no line, only the panel.
    property string placeMode: headline.placeMode()
    visible: placeMode === "top"
    color: theme.bg || "#0f1014"
    title: "Headline"

    function refresh() {
        view = headline.view()
        Qt.callLater(fit)
    }
    function fit() {
        var room = line.width - cwdButton.width - moreButton.implicitWidth - 3 * row.spacing - 8
        var used = 0
        var count = 0
        for (var i = 0; i < folderRepeater.count; i++) {
            var item = folderRepeater.itemAt(i)
            if (!item) break
            used += item.implicitWidth + row.spacing
            if (used > room) break
            count++
        }
        shownCount = count
    }
    onWidthChanged: Qt.callLater(fit)
    onFoldersChanged: Qt.callLater(fit)
    Component.onCompleted: Qt.callLater(fit)

    Connections {
        target: headline
        function onChanged() { line.refresh() }
        function onDockChanged() {
            line.dockMode = headline.dockMode()
            line.placeMode = headline.placeMode()
        }
        function onPanelRequested(anchor) {
            panelWindow.theme = line.theme
            panelWindow.embryoOpacity = line.embryoOpacity
            panelWindow.openAt(anchor)
        }
    }

    // The pointer at the edge opens the line at once; it goes about 0.5 s after the pointer
    // left, not while a dropdown of it is open.
    function pointerEntered() {
        collapseTimer.stop()
        pointerInside = true
    }
    function pointerLeft() {
        collapseTimer.restart()
    }
    Timer {
        id: collapseTimer
        interval: 500
        onTriggered: {
            if (line.popupOpen) { restart(); return }
            line.pointerInside = false
        }
    }
    HoverHandler {
        onHoveredChanged: hovered ? line.pointerEntered() : line.pointerLeft()
    }

    function go(path) {
        climbList.close()
        cascade.close()
        moreList.close()
        headline.go(path)
    }

    Row {
        id: row
        visible: line.expanded
        y: (line.lineHeight - height) / 2
        x: 4
        spacing: 4

        FolderItem {  // the CWD: a click opens the way up (the cascade)
            id: cwdButton
            objectName: "cwdButton"
            label: line.view.name || ""
            style: "smallIcon"
            compactHeight: line.lineHeight - 4
            iconSource: "image://theme/folder-open"
            fillColor: line.theme.smallButtonActiveBg || "#2c3a55"
            strokeColor: line.theme.smallButtonActiveBorder || "#4a5675"
            textColor: line.theme.text || "#e6e6e6"
            textSize: line.baseFont
            textBold: true
            onActivate: {
                if (climbList.visible) { climbList.close(); cascade.close(); return }
                climbList.entries = headline.climb()
                climbList.currentPath = line.view.cwd
                climbList.dropBelow(cwdButton, line)
            }
        }

        Repeater {  // the standard folders: born ones, and suggested ones pale
            id: folderRepeater
            model: line.folders
            delegate: FolderItem {
                objectName: "standardFolder"
                visible: index < line.shownCount
                label: modelData.name
                style: "text"
                compactHeight: line.lineHeight - 4
                batchSource: modelData.batch || ""
                batchText: modelData.batchText || ""
                opacity: modelData.embryo ? line.embryoOpacity : 1.0
                fillColor: line.theme.pill || "#2c3040"
                strokeColor: line.theme.pillBorder || "#3a3f52"
                textColor: line.theme.text || "#e6e6e6"
                textSize: line.baseFont
                onActivate: if (!modelData.embryo) line.go(modelData.path)
            }
        }

        FolderItem {  // the rest, behind »
            id: moreButton
            objectName: "moreButton"
            visible: line.shownCount < line.folders.length
            label: "»"
            style: "text"
            compactHeight: line.lineHeight - 4
            fillColor: line.theme.pill || "#2c3040"
            strokeColor: line.theme.pillBorder || "#3a3f52"
            textColor: line.theme.text || "#e6e6e6"
            textSize: line.baseFont
            onActivate: {
                if (moreList.visible) { moreList.close(); return }
                moreList.entries = line.folders.slice(line.shownCount).filter(function(f) { return !f.embryo })
                moreList.dropBelow(moreButton, line)
            }
        }
    }

    Panel {
        id: panelWindow
        theme: line.theme
        embryoOpacity: line.embryoOpacity
        baseFont: line.baseFont
    }

    DropList {  // the way up: from the projects root down to where one is
        id: climbList
        objectName: "climbList"
        theme: line.theme
        baseFont: line.baseFont
        onChosen: function(path) { line.go(path) }
        onHovered: function(item, entry) {
            cascade.entries = headline.children(entry.path)
            cascade.currentPath = line.view.cwd
            if (cascade.entries.length > 0) cascade.besides(item)
            else cascade.close()
        }
    }
    DropList {  // beside a step: its folders
        id: cascade
        objectName: "cascade"
        theme: line.theme
        baseFont: line.baseFont
        onChosen: function(path) { line.go(path) }
    }
    DropList {
        id: moreList
        objectName: "moreList"
        theme: line.theme
        baseFont: line.baseFont
        onChosen: function(path) { line.go(path) }
    }
}
