"""SunTree's global shortcut (examples/SunTree/Designdocument Krone.md: one action, then gone).

The default must be a hotkey pynput understands; an invalid one makes the service fail
silently and SunTree stays a normal window."""

import pytest

from examples.SunTree.SunTree import DEFAULT_HOTKEY


def test_the_default_hotkey_is_valid_for_pynput():
    keyboard = pytest.importorskip("pynput.keyboard")
    keys = keyboard.HotKey.parse(DEFAULT_HOTKEY)
    assert keys == keyboard.HotKey.parse("<ctrl>+<alt>+<space>")
