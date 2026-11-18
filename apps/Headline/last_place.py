"""Where the Headline was last (2026-11-18): started again without a place - the restart after
an update, the login - it goes back there instead of to the first root below the home folder;
else the clock had no project and counted nothing.

The place lies in SEITON's state folder (beside the clock's, core/clock.default_store), not in
the settings: it is where one was, not how one wants it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Optional

from core.brand import CONFIG_DIR


def path() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / CONFIG_DIR / "headline.json"


def read() -> Optional[str]:
    """The place remembered, when it is still a folder; else None."""
    try:
        data = json.loads(path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    place = data.get("place") if isinstance(data, dict) else None
    if not isinstance(place, str) or not Path(place).is_absolute() or not Path(place).is_dir():
        return None
    return place


def write(place: str) -> None:
    """Remember place (written whole: a reader never sees half a file)."""
    target = path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        writing = target.with_name(f".{target.name}.writing")
        writing.write_text(json.dumps({"place": str(place)}, ensure_ascii=False), encoding="utf-8")
        os.replace(writing, target)
    except OSError:
        pass  # not remembered: the next start goes where it went before


def start(place: Optional[str], start_place: Callable[[Optional[str]], str]) -> str:
    """Where to start: the place given, else the one remembered - each through start_place
    (core.scope_api), which goes into the first root when there is none."""
    return start_place(place if place is not None else read())
