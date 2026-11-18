#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myedit - open a project's config file (Tags.md, Templates.md, ACLs.md, Config.md) in $EDITOR.

myedit writes nothing itself: a file that is not there yet is made by the editor when it is
saved. A placeholder written here would end the inheritance (an empty ACLs.md in a subproject
gives no one any right). Where the project still inherits, myedit says from where.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.brand import META_DIR, NAME
from core.project import find_config_in_parents, resolve_cwp


SECTION_MAP = {
    "tags": "Tags.md",
    "templates": "Templates.md",
    "template": "Templates.md",
    "acl": "ACLs.md",
    "acls": "ACLs.md",
    "config": "Config.md",
}


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Open the relevant {NAME} config file in your editor.",
    )
    parser.add_argument("section", help="Config section (tags, templates, acl, config)")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path inside a project (default: .)",
    )
    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        editor = os.environ.get("EDITOR")
        if not editor:
            raise ValueError("EDITOR is not set")
        target = _resolve_target_file(args.section, args.path)
        if not target.exists():
            inherited = find_config_in_parents(target.parent.parent.parent, target.name)
            if inherited is not None:
                print(f"{target} is not there yet: this project uses {inherited}. "
                      "Saving in the editor gives it rules of its own.")
            else:
                print(f"{target} is not there yet: saving in the editor makes it.")
        subprocess.run([editor, str(target)], check=False)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _resolve_target_file(section: str, path: str) -> Path:
    key = section.strip().lower()
    if key not in SECTION_MAP:
        raise ValueError(f"Unknown section: {section}")

    cwp = resolve_cwp(Path(path))
    if not cwp:
        raise ValueError("No project found for path")
    return cwp.path / META_DIR / SECTION_MAP[key]


if __name__ == "__main__":
    main()
