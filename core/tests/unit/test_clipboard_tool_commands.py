"""The CopyQ commands of the ClipboardTool, read as CopyQ reads them (QSettings, INI format,
"File, Load Commands"): the whole script arrives, not only its first line ("docs/Prüfung
2026-11-18.md", ST1)."""

from pathlib import Path

import pytest

QtCore = pytest.importorskip("PySide6.QtCore")

TOOL = Path(__file__).resolve().parents[3] / "ClipboardTool"


def _command(name: str) -> dict:
    settings = QtCore.QSettings(str(TOOL / name), QtCore.QSettings.IniFormat)
    assert int(settings.value("Commands/size", 0)) == 1, settings.allKeys()
    settings.beginGroup("Commands/1")
    return {key: settings.value(key) for key in settings.allKeys()}


@pytest.mark.parametrize("name", ["copyq-myos-save-auto.ini", "copyq-myos-save-manual.ini"])
def test_the_whole_script_arrives(name):
    command = _command(name)
    script = command["Command"]
    assert script.startswith("copyq:") and "\n" in script
    assert "execute('python3', scriptPath" in script
    assert "save_clip_to_myos.py" in script
    assert command["Input"] == "text/plain"


def test_the_auto_command_runs_by_itself_and_skips_file_copies():
    command = _command("copyq-myos-save-auto.ini")
    assert str(command["Automatic"]).lower() == "true"
    assert "text/uri-list" in command["MatchCommand"]


def test_the_manual_command_is_in_the_menu():
    assert str(_command("copyq-myos-save-manual.ini")["InMenu"]).lower() == "true"
