#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mytag - tags of files and folders.

A file's tags are its extended attributes; a folder's are the ones Scope shows and filters by,
in its .seiton/myTags.md (Designdocument Tags.md) - plain tags without a value.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.tags import read_tags, write_tags
from core.brand import NAME  # noqa: E402


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{NAME} tags utility",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List tags for a path")
    list_cmd.add_argument("path", help="File or folder")

    add_cmd = sub.add_parser("add", help="Add a tag without value")
    add_cmd.add_argument("path")
    add_cmd.add_argument("tag")

    set_cmd = sub.add_parser("set", help="Set a tag value")
    set_cmd.add_argument("path")
    set_cmd.add_argument("tag_value", help="tag=value")

    remove_cmd = sub.add_parser("remove", help="Remove a tag")
    remove_cmd.add_argument("path")
    remove_cmd.add_argument("tag")

    clear_cmd = sub.add_parser("clear", help="Clear all tags")
    clear_cmd.add_argument("path")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "list":
            _list_tags(args.path)
        elif args.command == "add":
            _add_tag(args.path, args.tag)
        elif args.command == "set":
            _set_tag(args.path, args.tag_value)
        elif args.command == "remove":
            _remove_tag(args.path, args.tag)
        elif args.command == "clear":
            _clear_tags(args.path)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _folder_api(folder: Path):
    from core.scope_api import ScopeApi  # late: heavy, only for folders

    return ScopeApi(str(folder))


def _folder_tags(folder: Path) -> list:
    return _folder_api(folder).list_folder_tags(str(folder))


def _set_folder_tags(folder: Path, tags: list) -> None:
    if not _folder_api(folder).set_folder_tags(str(folder), tags):
        raise ValueError(f"Could not write the tags of {folder} (no write right?)")


def _list_tags(path: str) -> None:
    target = Path(path)
    if target.is_dir():
        found = _folder_tags(target)
        print(", ".join(found) if found else "No tags.")
        return
    tags = read_tags(target)
    if not tags:
        print("No tags.")
        return
    output = ", ".join(
        f"{key}={value}" if value is not None else key
        for key, value in tags.items()
    )
    print(output)


def _add_tag(path: str, tag: str) -> None:
    target = Path(path)
    if target.is_dir():
        _set_folder_tags(target, _folder_tags(target) + [tag])
        return
    tags = read_tags(target)
    tags[tag] = tags.get(tag)
    write_tags(target, tags)


def _set_tag(path: str, tag_value: str) -> None:
    if "=" not in tag_value:
        raise ValueError("Expected tag=value")
    tag, value = tag_value.split("=", 1)
    tag = tag.strip()
    value = value.strip()
    if not tag:
        raise ValueError("Tag name missing")
    if Path(path).is_dir():
        raise ValueError("A folder's tags have no value: use add")
    tags = read_tags(Path(path))
    try:
        tags[tag] = int(value)
    except ValueError:
        raise ValueError("Value must be an integer")
    write_tags(Path(path), tags)


def _remove_tag(path: str, tag: str) -> None:
    target = Path(path)
    if target.is_dir():
        _set_folder_tags(target, [t for t in _folder_tags(target) if t != tag])
        return
    tags = read_tags(target)
    if tag in tags:
        tags.pop(tag)
    write_tags(target, tags)


def _clear_tags(path: str) -> None:
    if Path(path).is_dir():
        _set_folder_tags(Path(path), [])
        return
    write_tags(Path(path), {})


if __name__ == "__main__":
    main()
