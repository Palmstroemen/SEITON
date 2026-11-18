"""Where a popup of the Headline goes: towards the room (apps/Scope/Designdocument Headline.md, 3).

One rule for every popup, wherever the Headline sits: a dropdown opens below or above its
anchor, to the side with room - from the top edge down, from a taskbar at the bottom up; a
cascade opens to the right or, at the right edge, to the left. Rectangles are
(x, y, width, height); `room` is the screen without the panels (QScreen.availableGeometry).
"""

from __future__ import annotations

from typing import Dict, Tuple

Rect = Tuple[int, int, int, int]
Size = Tuple[int, int]


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def drop(anchor: Rect, size: Size, room: Rect) -> Dict[str, int | str]:
    """A dropdown under (or over) anchor, its left edge at the anchor's, kept on the screen.
    Too tall for both sides, it takes the larger one and gets a "height" to be cut to."""
    ax, ay, aw, ah = anchor
    width, height = size
    rx, ry, rw, rh = room
    below = ry + rh - (ay + ah)
    above = ay - ry
    x = _clamp(ax, rx, rx + rw - width)
    if height <= below or (height > above and below >= above):
        placed: Dict[str, int | str] = {"x": x, "y": max(ay + ah, ry), "direction": "down"}
        if height > below:
            placed["height"] = ry + rh - int(placed["y"])
        return placed
    if height <= above:
        return {"x": x, "y": ay - height, "direction": "up"}
    return {"x": x, "y": ry, "direction": "up", "height": above}


def side(anchor: Rect, size: Size, room: Rect) -> Dict[str, int | str]:
    """A cascade beside anchor: to the right when it fits, else to the left; its top at the
    anchor's, moved up as far as needed to stay on the screen. Taller than the screen, it
    stands from its top and gets a "height" to be cut to, as drop() does."""
    ax, ay, aw, ah = anchor
    width, height = size
    rx, ry, rw, rh = room
    y = _clamp(ay, ry, ry + rh - height)
    if ax + aw + width <= rx + rw:
        placed: Dict[str, int | str] = {"x": ax + aw, "y": y, "direction": "right"}
    else:
        placed = {"x": max(rx, ax - width), "y": y, "direction": "left"}
    if height > rh:
        placed["y"], placed["height"] = ry, rh
    return placed
