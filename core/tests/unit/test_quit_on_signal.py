"""SIGTERM ends a SEITON program as a quit does ("docs/Prüfung 2026-11-18.md", O2)."""

import os
import signal
import time

from PySide6.QtCore import QCoreApplication

from core.quit_on_signal import quit_on_sigterm


def test_sigterm_quits_through_the_event_loop():
    app = QCoreApplication.instance() or QCoreApplication([])
    before = signal.getsignal(signal.SIGTERM)
    quits = []
    timer = quit_on_sigterm(app, quit=lambda: quits.append(True))
    try:
        os.kill(os.getpid(), signal.SIGTERM)
        end = time.time() + 2
        while not quits and time.time() < end:
            app.processEvents()
            time.sleep(0.01)
        assert quits == [True]
        assert timer.isActive()
    finally:
        timer.stop()
        signal.signal(signal.SIGTERM, before)
