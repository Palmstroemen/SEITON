"""One perspective daemon per projects root ("docs/Prüfung 2026-11-18.md", B1): a second one
started at the same time (Headline and SunTree at login) ends at once, without touching the
socket or the mount point of the first - else the first would be left unreachable."""

from pathlib import Path

from daemon import perspective_daemon as pd


def test_only_one_holds_the_root(tmp_path):
    socket_path = str(tmp_path / "root.sock")
    first = pd.hold_the_root(socket_path)
    assert first is not None
    assert pd.hold_the_root(socket_path) is None
    first.close()
    again = pd.hold_the_root(socket_path)
    assert again is not None
    again.close()


def test_a_second_daemon_leaves_the_first_alone(tmp_path):
    socket_path = tmp_path / "root.sock"
    socket_path.write_text("")  # the first daemon's socket
    first = pd.hold_the_root(str(socket_path))
    mount_point = tmp_path / "Perspektiven"
    try:
        pd.run_daemon(str(tmp_path / "Projekte"), str(mount_point), socket_path=str(socket_path))
    finally:
        first.close()
    assert socket_path.exists() and not mount_point.exists()
    assert "already running" in (tmp_path / "perspective-daemon.log").read_text()


def test_a_dead_drive_is_cleared_before_a_new_daemon(tmp_path):
    """"docs/Prüfung 2026-11-18.md", B4: after a hard end no daemon could mount again."""
    import errno
    import os

    from daemon.lens_link import clear_dead_mount

    calls = []

    def dead(path):
        raise OSError(errno.ENOTCONN, "Transport endpoint is not connected")

    assert clear_dead_mount(tmp_path / "Perspektiven", stat=dead, unmount=lambda argv: calls.append(argv) or 0)
    assert calls == [["fusermount", "-u", str(tmp_path / "Perspektiven")]]
    calls.clear()
    assert not clear_dead_mount(tmp_path, stat=os.stat, unmount=lambda argv: calls.append(argv) or 0)
    assert not clear_dead_mount(tmp_path / "fehlt", unmount=lambda argv: calls.append(argv) or 0)
    assert calls == []
