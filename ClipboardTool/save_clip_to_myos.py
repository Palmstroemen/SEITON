#!/usr/bin/env python3
"""
Save clipboard text to a Markdown file in the MyOS Clipboard folder.

Reads text from stdin and writes clip_YYYYMMDD_HHMMSS.md with optional
frontmatter (source URL if detected, copied timestamp).

Environment:
  MYOS_CLIPBOARD_PATH  Target directory for clip files (required, or falls back to ~/Clipboard).
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path


def get_clipboard_path() -> Path:
    raw = os.environ.get("MYOS_CLIPBOARD_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / "Clipboard"


# Simple URL detection for frontmatter (http/https)
_URL_RE = re.compile(
    r"https?://[^\s<>\"']+",
    re.IGNORECASE,
)


def extract_first_url(text: str) -> str:
    m = _URL_RE.search(text)
    return m.group(0) if m else ""


def build_content(text: str, copied_iso: str, source_url: str) -> str:
    if not source_url:
        return f"---\ncopied: \"{copied_iso}\"\n---\n\n{text}"
    return f"---\nsource: \"{source_url}\"\ncopied: \"{copied_iso}\"\n---\n\n{text}"


def main() -> int:
    try:
        raw = sys.stdin.buffer.read()
    except Exception as e:
        print(f"save_clip_to_myos: read stdin: {e}", file=sys.stderr)
        return 1

    try:
        text = raw.decode("utf-8", errors="replace").strip()
    except Exception as e:
        print(f"save_clip_to_myos: decode: {e}", file=sys.stderr)
        return 1

    if not text:
        return 0

    base = get_clipboard_path()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"save_clip_to_myos: mkdir {base}: {e}", file=sys.stderr)
        return 1

    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    copied_iso = now.strftime("%Y-%m-%d %H:%M")
    source_url = extract_first_url(text)
    content = build_content(text, copied_iso, source_url)

    # Created, never written over: several clips in one second (the menu command saves each
    # selected item) each get a file of their own - clip_..._2.md and so on.
    number = 1
    while True:
        filepath = base / (f"clip_{stamp}.md" if number == 1 else f"clip_{stamp}_{number}.md")
        try:
            with open(filepath, "x", encoding="utf-8") as handle:
                handle.write(content)
            break
        except FileExistsError:
            number += 1
        except OSError as e:
            print(f"save_clip_to_myos: write {filepath}: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
