"""What Scope's dialogs use of the main window (window.<name>) is there: an id of main.qml is no
property of the window, so window.moveReportDialog was undefined and every error message of the
dialogs went nowhere ("docs/Prüfung 2026-11-18.md", S3)."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication  # noqa: E402

sys.path.insert(0, str(REPO))
from core.scope_api import ScopeApi  # noqa: E402
from Scope.Scope import close_scope, load_scope  # noqa: E402


def _members(obj) -> set:
    meta = obj.metaObject()
    names = {bytes(meta.property(i).name()).decode() if isinstance(meta.property(i).name(), bytes)
             else str(meta.property(i).name()) for i in range(meta.propertyCount())}
    for i in range(meta.methodCount()):
        signature = meta.method(i).methodSignature()
        signature = bytes(signature).decode() if not isinstance(signature, str) else signature
        names.add(signature.split("(", 1)[0])
    return names


def test_the_dialogs_use_only_what_the_window_has(tmp_path):
    root = tmp_path / "Dokumente"
    (root / ".seiton").mkdir(parents=True)
    (root / ".seiton" / "Project.md").write_text("# SEITON Project\n", encoding="utf-8")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = load_scope(ScopeApi(str(root)), app)
    window = engine.rootObjects()[0]
    try:
        members = _members(window)
        missing = []
        for dialog in sorted((REPO / "Scope" / "Dialogs").glob("*.qml")):
            for name in sorted(set(re.findall(r"\bwindow\.([A-Za-z_]\w*)", dialog.read_text(encoding="utf-8")))):
                if name not in members:
                    missing.append(f"{dialog.name}: window.{name}")
        assert not missing, "\n".join(missing)
    finally:
        close_scope(engine, app)
