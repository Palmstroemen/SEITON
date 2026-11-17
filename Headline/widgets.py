"""Widgets in the Headline (Scope/Designdocument Headline.md, 3a).

Other programs - the time tracking first - put themselves into the Headline; it knows widgets,
not the clock. A widget may be missing, or be replaced by another one.

- It **registers** with `<config>/headline/widgets/<id>.json`:
  `{"name", "folder", "open": [command ...], "commands": [...], "staleAfter": seconds}` -
  written by the widget's installer, taken away by its uninstaller.
- It **shows** what `<folder>/view.json` says: `text`, `state` (calm, active, asking), perhaps
  `tooltip`, a `question` with `answers`, a short list of `items` ({text, path}). It rewrites
  the file when something changes; older than staleAfter, it shows nothing.
- A **counter** (optional): `{"prefix", "since"}` - the Headline counts on to the second between
  views (the clock writes its view every 15 s): prefix and the time since, H:MM:SS.
- It **is told** by command files dropped into `<folder>/commands/`: an answer to its question,
  or one of the commands it declared.
- Its **screen is its own**: a click runs its `open` command.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.brand import config_dir

STATES = ("calm", "active", "asking")
WORD = re.compile(r"^[a-z][a-z0-9_]{0,23}$")  # widget ids, answer ids, commands
MAX_TEXT = 80
MAX_ITEMS = 10
DEFAULT_STALE = 60


def widgets_dir() -> Path:
    return config_dir() / "headline" / "widgets"


def _text(value: Any, limit: int = MAX_TEXT) -> Optional[str]:
    return value if isinstance(value, str) and len(value) <= limit else None


def registered() -> Dict[str, Dict[str, Any]]:
    """The widgets registered, by id (the file's name), in the order of their ids."""
    found: Dict[str, Dict[str, Any]] = {}
    try:
        files = sorted(widgets_dir().glob("*.json"))
    except OSError:
        return found
    for path in files:
        if not WORD.match(path.stem):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        name, folder, command = _text(data.get("name"), 40), data.get("folder"), data.get("open")
        commands = data.get("commands", [])
        stale = data.get("staleAfter", DEFAULT_STALE)
        if (name is None or not isinstance(folder, str) or not Path(folder).is_absolute()
                or not isinstance(command, list) or not command or not all(isinstance(c, str) for c in command)
                or not isinstance(commands, list) or not all(isinstance(c, str) and WORD.match(c) for c in commands)
                or type(stale) is not int or stale <= 0):
            continue
        found[path.stem] = {"name": name, "folder": Path(folder), "open": list(command),
                            "commands": list(commands), "staleAfter": stale}
    return found


def _question(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict):
        return None
    text, answers = _text(value.get("text"), 160), value.get("answers")
    if text is None or not isinstance(answers, list):
        return None
    kept = [{"id": a["id"], "label": a["label"]} for a in answers
            if isinstance(a, dict) and isinstance(a.get("id"), str) and WORD.match(a["id"])
            and _text(a.get("label"), 30) is not None]
    return {"text": text, "answers": kept[:4]} if kept else None


def _items(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    kept = [{"text": i["text"], "path": i["path"]} for i in value
            if isinstance(i, dict) and _text(i.get("text")) is not None
            and isinstance(i.get("path"), str) and Path(i["path"]).is_absolute()]
    return kept[:MAX_ITEMS]


def _counter(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict):
        return None
    prefix, since = _text(value.get("prefix"), 60), value.get("since")
    if prefix is None or type(since) not in (int, float):
        return None
    return {"prefix": prefix, "since": float(since)}


def counted(counter: Dict[str, Any], now: Optional[float] = None) -> str:
    """A counter as shown: its prefix and the time since, to the second (H:MM:SS)."""
    seconds = max(0, int((now if now is not None else time.time()) - counter["since"]))
    return f"{counter['prefix']}{seconds // 3600}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def view_of(widget: Dict[str, Any], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """What a widget shows, checked; None when its view is missing, broken or stale."""
    path = widget["folder"] / "view.json"
    try:
        if (now or time.time()) - path.stat().st_mtime > widget["staleAfter"]:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    text, state = _text(data.get("text")), data.get("state")
    if text is None or state not in STATES:
        return None
    return {"text": text, "state": state, "tooltip": _text(data.get("tooltip"), 200) or "",
            "question": _question(data.get("question")), "items": _items(data.get("items")),
            "counter": _counter(data.get("counter"))}


def shown(now: Optional[float] = None) -> List[Dict[str, Any]]:
    """The widgets to show now, each with its id, name and view."""
    result = []
    for widget_id, widget in registered().items():
        view = view_of(widget, now)
        if view is not None:
            result.append({"id": widget_id, "name": widget["name"], **view})
    return result


def tell(widget_id: str, command: str) -> bool:
    """Drop a command file: an answer to the widget's question, or a command it declared."""
    widget = registered().get(widget_id)
    if widget is None or not WORD.match(command):
        return False
    view = view_of(widget)
    answers = [a["id"] for a in ((view or {}).get("question") or {}).get("answers", [])]
    if command not in widget["commands"] and command not in answers:
        return False
    folder = widget["folder"] / "commands"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{time.time_ns()}-{command}").write_text("", encoding="utf-8")
    except OSError:
        return False
    return True


def open_screen(widget_id: str, start: Callable[[List[str]], Any] = None) -> bool:
    """A click on the widget: its own screen, by its own command (the Headline does not wait)."""
    widget = registered().get(widget_id)
    if widget is None:
        return False
    start = start or (lambda command: subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                                        stderr=subprocess.DEVNULL))
    try:
        start(list(widget["open"]))
    except OSError:
        return False
    return True
