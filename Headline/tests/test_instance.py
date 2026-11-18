"""One Headline per user: a later start (the launcher in the taskbar, the shortcut, the applet)
hands "open the panel" to the one running and ends (Headline/instance.py)."""

import pytest

from Headline.instance import accepted, hand_over, server_name


def test_the_panel_at_the_pointer():
    assert accepted({"panel": None}) == {"panel": None}


def test_the_panel_at_an_anchor():
    anchor = {"x": 10, "y": 1040, "width": 40, "height": 40}
    assert accepted({"panel": anchor}) == {"panel": anchor}


@pytest.mark.parametrize("message", [
    {}, {"open": "/etc/passwd"}, {"panel": "x"}, {"panel": {"x": 1}},
    {"panel": {"x": "1", "y": 2, "width": 3, "height": 4}}, "panel", None,
])
def test_anything_else_is_refused(message):
    assert accepted(message) is None


def test_nobody_listening():
    assert hand_over("seiton-headline-nobody-here", {"panel": None}, timeout_ms=200) is False


def test_its_own_per_settings_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "a"))
    first = server_name()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "b"))
    assert server_name() != first and first.startswith("seiton-headline-")


def test_handed_over_to_the_one_running(monkeypatch, tmp_path):
    import threading
    from PySide6.QtCore import QCoreApplication
    from Headline.instance import InstanceServer

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    app = QCoreApplication.instance() or QCoreApplication([])
    server = InstanceServer(server_name())
    assert server.listen()
    heard = []
    server.panelRequested.connect(heard.append)
    result = {}
    thread = threading.Thread(target=lambda: result.setdefault("ok", hand_over(server.name, {"panel": None})))
    thread.start()
    for _ in range(200):
        app.processEvents()
        if "ok" in result:
            break
        thread.join(0.01)
    thread.join(1)
    server.close()
    assert result.get("ok") is True and heard == [None]


def _answering(path):
    """A Headline that runs, as far as a later start sees: it answers "ok"."""
    import socket
    import threading
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(path)
    server.listen(4)

    def serve():
        while True:
            try:
                connection, _ = server.accept()
            except OSError:
                return
            with connection:
                try:
                    if connection.recv(256):
                        connection.sendall(b"ok\n")
                except OSError:  # a look whether it is there, gone at once
                    pass
    threading.Thread(target=serve, daemon=True).start()
    return server


def test_a_second_headline_does_not_take_the_socket_of_one_running(monkeypatch, tmp_path):
    # H6 (review 2026-11-18): Qt replaced the living socket; two Headlines ran, the first one
    # out of reach.
    from PySide6.QtCore import QCoreApplication
    from Headline.instance import InstanceServer, socket_path
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    QCoreApplication.instance() or QCoreApplication([])
    running = _answering(socket_path("seiton-headline-test"))
    try:
        second = InstanceServer("seiton-headline-test")
        assert second.listen() is False
        assert hand_over("seiton-headline-test", {"panel": None}) is True  # the first still answers
    finally:
        running.close()


def test_a_later_start_hands_over_before_it_loads_qt(monkeypatch, tmp_path):
    # H5 (review 2026-11-18): it loaded PySide6 and Scope first - 1.5 s until the panel came.
    import os
    import subprocess
    import sys
    from pathlib import Path
    from Headline.instance import socket_path
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    running = _answering(socket_path(server_name()))
    try:
        script = Path(__file__).resolve().parents[1] / "Headline.py"
        done = subprocess.run([sys.executable, "-X", "importtime", str(script), "--panel"],
                              capture_output=True, text=True, timeout=30, env=dict(os.environ))
    finally:
        running.close()
    assert done.returncode == 0
    assert "PySide6" not in done.stderr
