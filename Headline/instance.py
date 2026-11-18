"""One Headline per user (Scope/Designdocument Headline.md, 3): a later start - the launcher in
the taskbar, the shortcut, the applet - hands "open the panel" to the Headline running and ends.

As PostFix does (PostFix/single_instance.py): a Unix socket in the user's private runtime
folder, owner-only; one Headline per user, display and settings folder, so tests with settings
of their own get one of their own.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.brand import file_name

ANCHOR_KEYS = ("x", "y", "width", "height")


def server_name() -> str:
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    key = "|".join([str(os.getuid()), os.environ.get("DISPLAY", ""), os.environ.get("WAYLAND_DISPLAY", ""),
                    str(Path(config).expanduser().resolve())])
    return file_name("headline-") + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def socket_path(name: str) -> str:
    folder = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return os.path.join(folder, name + ".sock")


def accepted(message: Any) -> Optional[Dict[str, Any]]:
    """The request as the Headline takes it, or None when refused.
    Security: whatever connects can only ask for the panel - at the pointer (None) or at an
    anchor of four whole numbers (the applet's button) - nothing else."""
    if not isinstance(message, dict) or set(message) != {"panel"}:
        return None
    anchor = message["panel"]
    if anchor is None:
        return {"panel": None}
    if (isinstance(anchor, dict) and set(anchor) == set(ANCHOR_KEYS)
            and all(type(anchor[k]) is int for k in ANCHOR_KEYS)):
        return {"panel": {k: anchor[k] for k in ANCHOR_KEYS}}
    return None


def parse_start(args: list) -> Tuple[Optional[str], Optional[dict]]:
    """Headline.py [--panel [--anchor x,y,w,h]] [place] -> (place or None, request or None).
    A broken anchor opens the panel at the pointer. Here, not in Headline.py: a later start
    reads its arguments and hands over before it loads Qt (review 2026-11-18, H5)."""
    place, request, rest = None, None, list(args)
    anchor = None
    if "--anchor" in rest:
        at = rest.index("--anchor")
        value = rest[at + 1] if at + 1 < len(rest) else ""
        del rest[at:at + 2]
        try:
            numbers = [int(part) for part in value.split(",")]
        except ValueError:
            numbers = []
        if len(numbers) == 4 and numbers[2] > 0 and numbers[3] > 0:
            anchor = dict(zip(ANCHOR_KEYS, numbers))
    if "--panel" in rest:
        rest.remove("--panel")
        request = {"panel": anchor}
    places = [a for a in rest if not a.startswith("--")]
    if places:
        place = places[0]
    return place, request


def alive(name: str, timeout_ms: int = 500) -> bool:
    """Whether a Headline answers on name's socket (connecting is enough)."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout_ms / 1000)
            connection.connect(socket_path(name))
    except OSError:
        return False
    return True


def hand_over(name: str, message: Dict[str, Any], timeout_ms: int = 1500) -> bool:
    """Give message to the Headline running under name; False when none runs (or it refused).
    Plain Python, no Qt: a later start hands over quickly and ends."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout_ms / 1000)
            connection.connect(socket_path(name))
            connection.sendall((json.dumps(message) + "\n").encode("utf-8"))
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
    # The server needs Qt; only the running Headline makes one.
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
        """Listens for later starts; panelRequested(anchor or None) for each accepted one."""

        panelRequested = Signal(object)

        def __init__(self, name: str, parent=None):
            super().__init__(parent)
            self.name = name
            self.path = socket_path(name)
            self.server = QLocalServer(self)
            # Security: only this user may connect (the socket file is owner-only).
            self.server.setSocketOptions(QLocalServer.UserAccessOption)
            self.server.newConnection.connect(self._accept)

        def listen(self) -> bool:
            """False when another Headline answers there: Qt would put its own socket over the
            living one (review 2026-11-18, H6)."""
            if alive(self.name):
                return False
            if self.server.listen(self.path):
                return True
            # Left over from a Headline that ended without cleaning up (hand_over found nobody).
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
            line = bytes(connection.readLine().data()).decode("utf-8", errors="replace")
            try:
                request = accepted(json.loads(line))
            except ValueError:
                request = None
            connection.write(b"ok\n" if request is not None else b"refused\n")
            connection.flush()
            connection.disconnectFromServer()
            if request is not None:
                self.panelRequested.emit(request["panel"])

    return InstanceServer
