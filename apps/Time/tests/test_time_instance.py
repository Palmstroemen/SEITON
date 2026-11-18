"""One time screen per user (apps/Time/instance.py, 2026-11-18): two could be opened. A later
start - the stopwatch in the Headline, the launcher - brings the one open to the front and
ends."""

import threading

import pytest

from apps.Time import instance


def test_only_show_is_accepted():
    assert instance.accepted("show") is True
    for message in ("", "show me", "open /etc/passwd", "SHOW", None, 5):
        assert instance.accepted(message) is False, message


def test_nobody_listening():
    assert instance.hand_over("seiton-time-nobody-here", timeout_ms=200) is False


def test_its_own_per_settings_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "a"))
    first = instance.server_name()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "b"))
    assert instance.server_name() != first and first.startswith("seiton-time-")


def _serve(monkeypatch, tmp_path):
    from PySide6.QtCore import QCoreApplication
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    app = QCoreApplication.instance() or QCoreApplication([])
    server = instance.InstanceServer(instance.server_name())
    assert server.listen()
    return app, server


def test_handed_over_to_the_one_open(monkeypatch, tmp_path):
    app, server = _serve(monkeypatch, tmp_path)
    heard = []
    server.showRequested.connect(lambda: heard.append("show"))
    result = {}
    thread = threading.Thread(target=lambda: result.setdefault("ok", instance.hand_over(server.name)))
    thread.start()
    for _ in range(200):
        app.processEvents()
        if "ok" in result:
            break
        thread.join(0.01)
    thread.join(1)
    server.close()
    assert result.get("ok") is True and heard == ["show"]


def test_a_second_does_not_take_the_socket_of_the_one_open(monkeypatch, tmp_path):
    _app, server = _serve(monkeypatch, tmp_path)
    second = instance.InstanceServer(server.name)
    assert second.listen() is False
    server.close()


def test_a_later_start_hands_over_and_ends(monkeypatch):
    from apps.Time import TimeScreen
    monkeypatch.setattr(instance, "hand_over", lambda name, **_k: True)
    assert TimeScreen.main() == 0
