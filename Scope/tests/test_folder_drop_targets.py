"""Every folder button in Scope's folder rows that can be dragged also takes drops - also in the
H view's preview rows, the core of "go to the target with the file in hand" ("docs/Prüfung
2026-11-18.md", F1: a file dropped there went into the clipboard)."""

import re
from pathlib import Path

BROWSER = Path(__file__).resolve().parents[1] / "FolderBrowser.qml"


def _folder_items(text: str):
    """The FolderItem blocks, each up to its closing brace."""
    for match in re.finditer(r"FolderItem \{", text):
        depth, i = 0, match.end() - 1
        while True:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            if depth == 0:
                break
            i += 1
        yield text[match.start():i + 1]


def test_folders_one_can_drag_take_drops():
    folders = [block for block in _folder_items(BROWSER.read_text(encoding="utf-8"))
               if "dragPayload: fullPath" in block]
    assert len(folders) >= 6  # folder row, previews, the V columns
    for block in folders:
        first = block.splitlines()[1].strip()
        assert re.search(r"allowDrops: (root|browserRoot)\.allowDrops", block), first
        assert re.search(r"emitMoveEntryIntent\(payload, fullPath\)", block), first
