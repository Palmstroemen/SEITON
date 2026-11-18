# quit_on_signal.py - a SEITON program asked to end (SIGTERM: kill, an IDE, logging out) ends as
# if the user quit it: Qt's event loop returns and the program cleans up as usual (Scope and
# SunTree unmount the lens drive through their daemon link). Without it Python died at once and
# the drive "Perspektiven" stayed mounted ("docs/Prüfung 2026-11-18.md", O2).

from __future__ import annotations

import signal
from typing import Callable, Optional

from PySide6.QtCore import QCoreApplication, QTimer


def quit_on_sigterm(app: QCoreApplication, quit: Optional[Callable[[], None]] = None) -> QTimer:
    """On SIGTERM call quit (default: app.quit). Python only sees a signal while it runs, so a
    quiet timer lets it run now and then; the timer is returned (it lives as long as app)."""
    signal.signal(signal.SIGTERM, lambda *_: (quit or app.quit)())
    timer = QTimer(app)
    timer.timeout.connect(lambda: None)
    timer.start(300)
    return timer
