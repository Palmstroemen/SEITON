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
