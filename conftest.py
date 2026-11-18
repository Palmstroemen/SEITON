"""Shared safety fixtures for every test suite (core, cli, Scope, PostFix)."""

import os

import pytest
from core.brand import env_name

# core/archive is old code kept to look at, not to run: its tests no longer even collect.
collect_ignore_glob = ["core/archive/*"]

# Browser pages (PostFix's editor) without a screen: Chromium's GPU emulation crashes when pages
# are made and deleted one after another (measured); drawn without a GPU it does not. Set before
# QtWebEngine starts.
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")
# No test draws on the real screen (nor moves the real pointer: SunTree's tests set it).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def one_qt_application():
    """One Qt application for all tests, and a QApplication: tests that ask for a
    QGuiApplication get it as well, and widgets (PostFix's editor) still work after them.
    With a QGuiApplication first, one run over all folders aborted ("Cannot create a QWidget
    without QApplication")."""
    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401  (before the application, as Qt wants)
    except ImportError:
        pass
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        yield None
        return
    yield QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def no_real_desktop_changes(monkeypatch, tmp_path_factory):
    """
    Desk profiles are always on: opening a folder may change the wallpaper and theme,
    and MyOS keeps the user's own desktop in ~/.config/MyOS. Tests must never touch the
    real desktop or that file: no backend (tests that need one pass a fake) and a
    config home of their own.
    """
    monkeypatch.setenv(env_name("DESK_BACKEND"), "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    # Nor the user's cache (Scope's thumbnails): a cache of their own.
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path_factory.mktemp("cache")))
    # Nor the user's state (the clock's, the Headline's last place): a state of their own.
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("state")))
    # Nor start a perspective daemon that mounts a drive (Scope starts one by default).
    monkeypatch.setenv(env_name("SCOPE_START_DAEMON"), "0")
