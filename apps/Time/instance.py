"""One time screen per user (2026-11-18: two could be opened): a later start - the stopwatch in
the Headline, the launcher - asks the one open to show itself and ends.

As the Headline (apps/Headline/instance.py): a Unix socket in the user's private runtime folder,
owner-only; one per user, display and settings folder, so tests with settings of their own get
one of their own.
"""

from __future__ import annotations

import hashlib
import os
import socket
import tempfile
from pathlib import Path
from typing import Any

from core.brand import file_name

MESSAGE = "show"


def server_name() -> str:
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    key = "|".join([str(os.getuid()), os.environ.get("DISPLAY", ""), os.environ.get("WAYLAND_DISPLAY", ""),
                    str(Path(config).expanduser().resolve())])
    return file_name("time-") + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def socket_path(name: str) -> str:
    folder = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return os.path.join(folder, name + ".sock")


def accepted(message: Any) -> bool:
    """Security: whatever connects can only ask it to show itself - nothing else."""
    return message == MESSAGE


def alive(name: str, timeout_ms: int = 500) -> bool:
    """Whether a time screen answers on name's socket (connecting is enough)."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout_ms / 1000)
            connection.connect(socket_path(name))
    except OSError:
        return False
    return True


def hand_over(name: str, timeout_ms: int = 1500) -> bool:
    """Ask the time screen open under name to show itself; False when none is open."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout_ms / 1000)
            connection.connect(socket_path(name))
            connection.sendall((MESSAGE + "\n").encode("utf-8"))
            answer = b""
            while not answer.endswith(b"\n"):
                chunk = connection.recv(64)
                if not chunk:
                    break
                answer += chunk
    except OSError:
        return False
    return answer.strip() == b"ok"


_SERVER_CLASS = None


def __getattr__(attribute):
    # The server needs Qt; only the time screen open makes one.
    global _SERVER_CLASS
    if attribute == "InstanceServer":
        if _SERVER_CLASS is None:
            _SERVER_CLASS = _server_class()
        return _SERVER_CLASS
    raise AttributeError(attribute)


def _server_class():
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtNetwork import QLocalServer

    class InstanceServer(QObject):
        """Listens for later starts; showRequested for each."""

        showRequested = Signal()

        def __init__(self, name: str, parent=None):
            super().__init__(parent)
            self.name = name
            self.path = socket_path(name)
            self.server = QLocalServer(self)
            # Security: only this user may connect (the socket file is owner-only).
            self.server.setSocketOptions(QLocalServer.UserAccessOption)
            self.server.newConnection.connect(self._accept)

        def listen(self) -> bool:
            """False when another time screen answers there (Qt would put its socket over it)."""
            if alive(self.name):
                return False
            if self.server.listen(self.path):
                return True
            # Left over from one that ended without cleaning up.
            QLocalServer.removeServer(self.path)
            return self.server.listen(self.path)

        def close(self):
            self.server.close()

        def _accept(self):
            while self.server.hasPendingConnections():
                connection = self.server.nextPendingConnection()
                connection.readyRead.connect(lambda c=connection: self._read(c))

        def _read(self, connection):
            if not connection.canReadLine():
                return
            line = bytes(connection.readLine().data()).decode("utf-8", errors="replace").strip()
            ok = accepted(line)
            connection.write(b"ok\n" if ok else b"refused\n")
            connection.flush()
            connection.disconnectFromServer()
            if ok:
                self.showRequested.emit()

    return InstanceServer
