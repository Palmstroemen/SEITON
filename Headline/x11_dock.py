"""The line at the top edge on X11 (Scope/Designdocument Headline.md, 3).

The window says it is a dock (`_NET_WM_WINDOW_TYPE_DOCK`): no frame, on every workspace, above
the others, as a panel. While it is always there it keeps its room with a strut
(`_NET_WM_STRUT_PARTIAL`, and `_NET_WM_STRUT` for older window managers): maximised windows stop
below it. While it hides itself it keeps none. Wayland has no such properties (layer-shell,
later).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

Rect = Tuple[int, int, int, int]


def strut(screen: Rect, height: int) -> List[int]:
    """_NET_WM_STRUT_PARTIAL for a line of `height` at the top of `screen` (x, y, w, h in root
    coordinates): left, right, top, bottom, then the start and end of each side's range."""
    x, y, width, _h = screen
    return [0, 0, y + height, 0, 0, 0, 0, 0, x, x + width - 1, 0, 0]


def apply(display, window_id: int, partial: Optional[List[int]]) -> None:
    """Make window_id a dock; with `partial` keeping that room, without it keeping none.
    display: an Xlib display (or anything with intern_atom, create_resource_object, flush)."""
    window = display.create_resource_object("window", window_id)
    atom = display.intern_atom
    window.change_property(atom("_NET_WM_WINDOW_TYPE"), atom("ATOM"), 32,
                           [atom("_NET_WM_WINDOW_TYPE_DOCK")])
    if partial is None:
        window.delete_property(atom("_NET_WM_STRUT_PARTIAL"))
        window.delete_property(atom("_NET_WM_STRUT"))
    else:
        window.change_property(atom("_NET_WM_STRUT_PARTIAL"), atom("CARDINAL"), 32, partial)
        window.change_property(atom("_NET_WM_STRUT"), atom("CARDINAL"), 32, partial[:4])
    display.flush()


def apply_to(window_id: int, partial: Optional[List[int]]) -> bool:
    """apply() on the running X server; False where there is none (Wayland, offscreen)."""
    try:
        from Xlib import display as xdisplay
    except Exception:
        return False
    try:
        connection = xdisplay.Display()
    except Exception:
        return False
    try:
        apply(connection, window_id, partial)
        return True
    finally:
        connection.close()
