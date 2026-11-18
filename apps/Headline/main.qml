import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import "../Scope"

// The Headline's line (apps/Scope/Designdocument Headline.md, 2): the CWD with its cascade to climb,
// the standard folders there, as many as fit, the rest behind ». At the top edge as a dock
// (apps/Headline/x11_dock.py): always there, or a thin edge that opens when the pointer comes.
Window {
    id: line
    objectName: "headlineLine"
    property var view: headline.view()
    // What other programs put in (apps/Headline/widgets.py): the time tracking first.
    property var widgets: headline.widgets()
    // Widgets with an icon sit in the CWD's tab (WidgetIcon.qml), the others at the right.
    readonly property var iconWidgets: (widgets || []).filter(function(w) { return !!w.icon })
    // A widget's counter counts on to the second (apps/Headline/widgets.py, counter).
    property real nowSeconds: Date.now() / 1000
    Timer {
        interval: 1000
        repeat: true
        running: line.widgets.some(function(w) { return !!w.counter })
        onTriggered: line.nowSeconds = Date.now() / 1000
    }
    function counted(counter) {
        var seconds = Math.max(0, Math.floor(nowSeconds - counter.since))
        var minutes = Math.floor(seconds / 60) % 60
        return counter.prefix + Math.floor(seconds / 3600) + ":" + ("0" + minutes).slice(-2)
               + ":" + ("0" + seconds % 60).slice(-2)
    }
    property var theme: headline.colorScheme()
    property real embryoOpacity: headline.embryoOpacity()
    readonly property int lineHeight: 30
    readonly property int baseFont: 13
    readonly property var folders: view.folders || []
    // How many folders fit beside the CWD and the » (worked out from their widths).
    property int shownCount: folders.length
    // Always there ("keep") or hiding itself ("hide"), as set in its own settings (SettingsWindow.qml).
    property string dockMode: headline.dockMode()
    readonly property int edgeHeight: 2
    property bool pointerInside: false
    readonly property bool popupOpen: climbList.visible || cascade.visible || moreList.visible || deeperOpen
    // A widget that asks (the clock's "Still working on ...?") must be seen: hidden, the line
    // comes out while it asks (review 2026-11-18, H8).
    readonly property bool asking: (widgets || []).some(function(w) { return w.state === "asking" })
    readonly property bool expanded: dockMode === "keep" || pointerInside || popupOpen || asking
    // Hiding itself, the line slides in from above and out again (2026-11-18): reveal goes
    // from 0 to 1, the window is as high as the line until it has slid out (the pointer stays
    // in it), the line's background slides with its content - the window is see-through.
    readonly property int slideMs: 150
    property real reveal: expanded ? 1 : 0
    Behavior on reveal { NumberAnimation { duration: line.slideMs; easing.type: Easing.OutCubic } }
    readonly property real slideY: -(1 - reveal) * (lineHeight - edgeHeight)
    readonly property bool shown: expanded || reveal > 0

    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    x: Screen.virtualX
    y: Screen.virtualY
    width: Screen.width
    height: shown ? lineHeight : edgeHeight
    // From the taskbar (Setup) there is no line, only the panel.
    property string placeMode: headline.placeMode()
    visible: placeMode === "top"
    color: dockMode === "hide" ? "transparent" : (theme.bg || "#0f1014")
    title: "Headline"

    Rectangle {  // the line's background; hiding, its last 2 px are the edge
        objectName: "lineBackground"
        width: line.width
        height: line.lineHeight
        y: line.slideY
        color: line.theme.bg || "#0f1014"
    }

    function refresh() {
        view = headline.view()
        Qt.callLater(fit)
    }
    // » takes room only when something must hide behind it: first all, without it.
    function fit() {
        var room = line.width - cwdButton.width - 2 * row.spacing - 8
                   - (widgetRow.implicitWidth > 0 ? widgetRow.implicitWidth + 12 : 0)
        var widths = []
        var all = 0
        for (var i = 0; i < folderRepeater.count; i++) {
            var item = folderRepeater.itemAt(i)
            if (!item) break
            widths.push(item.implicitWidth + row.spacing)
            all += widths[i]
        }
        if (widths.length === folderRepeater.count && all <= room) {
            shownCount = widths.length
            return
        }
        room -= moreButton.implicitWidth + row.spacing
        var used = 0
        var count = 0
        while (count < widths.length && used + widths[count] <= room) {
            used += widths[count]
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
        function onThemeChanged() {
            line.theme = headline.colorScheme()
            line.embryoOpacity = headline.embryoOpacity()
            panelWindow.theme = line.theme
            panelWindow.embryoOpacity = line.embryoOpacity
            settingsWindow.read()
        }
        function onWidgetsChanged() {
            line.widgets = headline.widgets()
            Qt.callLater(line.fit)
        }
        function onSetupRequested() { settingsWindow.openCentered() }
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
    // The dropdowns close once the pointer has left them and the line for about 0.6 s.
    // pointerOnLine: the pointer is over the line now; pointerInside: the line stays out (it is
    // kept while a dropdown is open). The dropdowns close by the first: by the second they
    // waited for each other and stayed for ever (2026-11-18).
    property bool pointerOnLine: false
    readonly property bool pointerNearPopups: pointerOnLine || climbList.pointerInside
                                              || cascade.pointerInside || moreList.pointerInside
                                              || deeperPointer
    Timer {
        id: popupCloser
        interval: 600
        running: line.popupOpen && !line.pointerNearPopups
        onTriggered: {
            climbList.close()
            line.closeCascades(1)
            moreList.close()
        }
    }

    // The cascades beside the way up, as deep as the folders go (2026-11-18: only one step to
    // the right could be opened). Level 1 is `cascade`; the deeper ones are made when needed
    // ("cascade2", "cascade3", ...) and kept.
    property var deeper: []
    property bool deeperOpen: false
    property bool deeperPointer: false
    function recountDeeper() {
        var open = false, near = false
        for (var i = 0; i < deeper.length; i++) {
            open = open || deeper[i].visible
            near = near || (deeper[i].visible && deeper[i].pointerInside)
        }
        deeperOpen = open
        deeperPointer = near
    }
    function cascadeAt(level) {
        if (level === 1) return cascade
        while (deeper.length < level - 1) {
            var made = deeperCascade.createObject(line, { objectName: "cascade" + (deeper.length + 2),
                                                          level: deeper.length + 2 })
            deeper.push(made)
        }
        return deeper[level - 2]
    }
    // Hovering a row of level-1 (or a step of the way up for level 1): its folders beside it.
    function openCascade(level, item, entry) {
        closeCascades(level + 1)
        var list = cascadeAt(level)
        list.entries = headline.children(entry.path)
        list.currentPath = line.view.cwd
        if (list.entries.length > 0) list.besides(item)
        else list.close()
        recountDeeper()
    }
    function closeCascades(from) {
        if (from <= 1) cascade.close()
        for (var i = Math.max(0, from - 2); i < deeper.length; i++) deeper[i].close()
        recountDeeper()
    }
    Component {
        id: deeperCascade
        DropList {
            property int level: 2
            theme: line.theme
            baseFont: line.baseFont
            onDropped: function(payload, path) { line.dropped(payload, path) }
            onChosen: function(path) { line.go(path) }
            onHovered: function(item, entry) { line.openCascade(level + 1, item, entry) }
            onVisibleChanged: line.recountDeeper()
            onPointerInsideChanged: line.recountDeeper()
        }
    }

    function pointerEntered() {
        collapseTimer.stop()
        pointerOnLine = true
        pointerInside = true
    }
    function pointerLeft() {
        pointerOnLine = false
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
        closeCascades(1)
        moreList.close()
        headline.go(path)
    }

    // Something dropped onto a folder (H9): moved there as in Scope - an embryo is born by it;
    // folders are asked about first.
    function dropped(payload, path) {
        var plan = headline.dropPlan(payload, path)
        if (!plan.sources || plan.sources.length === 0) return
        if (plan.folders > 0 && plan.ask) dropAsk.askAbout(plan)
        else move(plan)
    }
    function move(plan) {
        var result = headline.dropMove(plan.sources, plan.target)
        if (result.failed && result.failed.length > 0)
            dropAsk.tell(qsTr("Could not move: %1").arg(result.failed.join(", ")))
    }
    SettingsWindow {
        id: settingsWindow
        theme: line.theme
        baseFont: line.baseFont
    }
    TipWindow {  // tooltips below the line: inside its window they were cut off
        id: tipWindow
        band: line
        theme: line.theme
        baseFont: line.baseFont
    }
    onShownChanged: if (!shown) tipWindow.hide()
    DropAsk {
        id: dropAsk
        theme: line.theme
        baseFont: line.baseFont
        onConfirmed: function(plan) { line.move(plan) }
    }

    Row {
        id: row
        visible: line.shown
        y: (line.lineHeight - height) / 2 + line.slideY
        x: 4
        spacing: 4

        FolderItem {  // the CWD: a click opens the way up (the cascade)
            id: cwdButton
            objectName: "cwdButton"
            label: line.view.name || ""
            style: "smallIcon"
            centerName: true
            compactHeight: line.lineHeight - 4
            iconSource: "image://theme/folder-open"
            projectBadge: !!line.view.project
            smallProjectP: true  // a folder with a small P (2026-11-18)
            batchSource: line.view.batch || ""
            batchText: line.view.batchText || ""
            fillColor: line.theme.smallButtonActiveBg || "#2c3a55"
            strokeColor: line.theme.smallButtonActiveBorder || "#4a5675"
            textColor: line.theme.text || "#e6e6e6"
            textSize: line.baseFont
            textBold: true
            trailingSpace: line.iconWidgets.length > 0 ? tabIcons.implicitWidth + 4 : 0
            allowDrops: true
            onDropReceived: function(payload) { line.dropped(payload, line.view.cwd) }

            Row {  // the widgets with an icon (the clock's stopwatch), at the end of the tab
                id: tabIcons
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6
                Repeater {
                    model: line.iconWidgets
                    delegate: WidgetIcon {
                        kind: modelData.icon
                        widgetId: modelData.id
                        beating: modelData.state === "active"
                        warn: !!modelData.warn
                        off: modelData.state === "off"
                        tip: off ? qsTr("%1 is not running - a click opens it").arg(modelData.name)
                                 : (modelData.tooltip || modelData.text)
                        color: line.theme.text || "#e6e6e6"
                        onOpened: function(widgetId) { headline.widgetOpen(widgetId) }
                        onTipWanted: function(anchor, text) { tipWindow.ask(anchor, text) }
                        onTipGone: tipWindow.hide()
                    }
                }
            }
            onActivate: {
                if (climbList.visible) { climbList.close(); line.closeCascades(1); return }
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
                // A click alone bears no embryo (Designdocument Headline.md, 3); a drop does.
                allowDrops: true
                onDropReceived: function(payload) { line.dropped(payload, modelData.path) }
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

    Row {  // far right: the widgets, each with its question's answers when it asks
        id: widgetRow
        visible: line.shown
        anchors.right: parent.right
        anchors.rightMargin: 4
        y: (line.lineHeight - height) / 2 + line.slideY
        spacing: 4
        Repeater {
            model: line.widgets
            delegate: Row {
                spacing: 2
                Repeater {  // its button - not for a widget in the CWD's tab (an icon): only its question
                    model: modelData.icon ? [] : [modelData]
                    delegate: FolderItem {
                        objectName: "widget"
                        label: modelData.counter ? line.counted(modelData.counter) : modelData.text
                        style: "text"
                        compactHeight: line.lineHeight - 4
                        fillColor: modelData.state === "active" ? (line.theme.smallButtonActiveBg || "#2c3a55")
                                                                : (line.theme.pill || "#2c3040")
                        strokeColor: modelData.state === "asking" ? (line.theme.lensFrame || "#d97706")
                                                                  : (line.theme.pillBorder || "#3a3f52")
                        textColor: modelData.state === "calm" ? (line.theme.setupMuted || "#9aa0ad")
                                                              : (line.theme.text || "#e6e6e6")
                        textSize: line.baseFont
                        onHoverActiveChanged: hoverActive && modelData.tooltip.length > 0
                                              ? tipWindow.ask(this, modelData.tooltip) : tipWindow.hide()
                        onActivate: headline.widgetOpen(modelData.id)
                    }
                }
                Text {  // what it asks, before the answers
                    objectName: "widgetQuestion"
                    visible: !!modelData.question
                    text: modelData.question ? modelData.question.text : ""
                    color: line.theme.text || "#e6e6e6"
                    font.pixelSize: line.baseFont
                    height: line.lineHeight - 4
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 4
                    rightPadding: 2
                }
                Repeater {
                    model: modelData.question ? modelData.question.answers : []
                    delegate: FolderItem {
                        objectName: "widgetAnswer"
                        label: modelData.label
                        style: "text"
                        compactHeight: line.lineHeight - 4
                        fillColor: line.theme.smallButtonBg || "#2c3040"
                        strokeColor: line.theme.lensFrame || "#d97706"
                        textColor: line.theme.text || "#e6e6e6"
                        textSize: line.baseFont
                        onActivate: headline.widgetTell(widgetEntry.id, modelData.id)
                    }
                }
                property var widgetEntry: modelData
            }
        }
    }

    Panel {
        id: panelWindow
        counted: line.counted
        onDropped: function(payload, path) { line.dropped(payload, path) }
        theme: line.theme
        embryoOpacity: line.embryoOpacity
        baseFont: line.baseFont
    }

    DropList {  // the way up: from the projects root down to where one is
        id: climbList
        onDropped: function(payload, path) { line.dropped(payload, path) }
        objectName: "climbList"
        showTools: true
        theme: line.theme
        baseFont: line.baseFont
        onChosen: function(path) { line.go(path) }
        onHovered: function(item, entry) { line.openCascade(1, item, entry) }
    }
    DropList {  // beside a step: its folders; beside a row of it the next level, and so on
        id: cascade
        onDropped: function(payload, path) { line.dropped(payload, path) }
        objectName: "cascade"
        theme: line.theme
        baseFont: line.baseFont
        onChosen: function(path) { line.go(path) }
        onHovered: function(item, entry) { line.openCascade(2, item, entry) }
    }
    DropList {
        id: moreList
        onDropped: function(payload, path) { line.dropped(payload, path) }
        objectName: "moreList"
        theme: line.theme
        baseFont: line.baseFont
        onChosen: function(path) { line.go(path) }
    }
}
