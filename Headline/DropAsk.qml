import QtQuick 2.15
import QtQuick.Window 2.15
import "../Scope"

// Asked before folders are moved by a drop onto a folder of the Headline (as Scope asks), and
// told what could not be moved (Designdocument Headline.md, 3; review 2026-11-18, H9).
Window {
    id: ask
    objectName: "dropAsk"
    property var theme: ({})
    property int baseFont: 13
    property var plan: null        // {sources, folders, target}; null: only telling
    property string message: ""
    signal confirmed(var plan)

    flags: Qt.Dialog | Qt.WindowStaysOnTopHint
    title: "SEITON"
    color: theme.panel || "#202124"
    width: 420
    height: content.implicitHeight + 32

    function _show() {
        x = Screen.virtualX + (Screen.width - width) / 2
        y = Screen.virtualY + (Screen.height - height) / 3
        show()
        raise()
        requestActivate()
    }
    function askAbout(next) {
        plan = next
        var name = String(next.target).split("/").pop()
        message = qsTr("Really move %n folder(s) to “%1”?", "", next.folders).arg(name)
        _show()
    }
    function tell(text) {
        plan = null
        message = text
        _show()
    }

    Column {
        id: content
        x: 16
        y: 16
        width: ask.width - 32
        spacing: 12
        Text {
            objectName: "dropAskText"
            width: parent.width
            text: ask.message
            wrapMode: Text.WordWrap
            color: ask.theme.text || "#e6e6e6"
            font.pixelSize: ask.baseFont
        }
        Row {
            spacing: 6
            anchors.right: parent.right
            FolderItem {
                objectName: "dropAskCancel"
                visible: ask.plan !== null
                label: qsTr("Cancel")
                style: "text"
                compactHeight: 28
                fillColor: ask.theme.smallButtonBg || "#2c3040"
                strokeColor: ask.theme.pillBorder || "#3a3f52"
                textColor: ask.theme.text || "#e6e6e6"
                textSize: ask.baseFont
                onActivate: ask.close()
            }
            FolderItem {
                objectName: "dropAskOk"
                label: ask.plan !== null ? qsTr("Move") : qsTr("OK")
                style: "text"
                compactHeight: 28
                fillColor: ask.theme.smallButtonActiveBg || "#2c3a55"
                strokeColor: ask.theme.smallButtonActiveBorder || "#4a5675"
                textColor: ask.theme.text || "#e6e6e6"
                textSize: ask.baseFont
                onActivate: {
                    var plan = ask.plan
                    ask.close()
                    if (plan !== null) ask.confirmed(plan)
                }
            }
        }
    }
}
