#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seiton import - import an export package: back to its place when that is still a project, else
into --target as a project of its own (its rights travel with it).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.importer import import_package
from core.brand import COMMAND, NAME  # noqa: E402


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=f"{COMMAND} import", 
        description=f"{NAME} import utility",
    )
    parser.add_argument("package", help="Path to export package (folder or zip)")
    parser.add_argument(
        "--target",
        help="Folder to adopt it into, as a project of its own (without one: back to its place)",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "adopt", "restore"],
        default="auto",
        help="auto (default): back to its place, or into --target when one is given",
    )
    parser.add_argument(
        "--conflict",
        choices=["skip", "overwrite"],
        default="skip",
        help="Files already there: kept (skip, default) or replaced; settings are always kept",
    )
    return parser.parse_args(args)


def main(argv=None) -> None:
    args = parse_args(argv)
    try:
        result = import_package(
            args.package,
            target_root=args.target,
            mode=args.mode,
            conflict=args.conflict,
        )
        print(f"Imported into {result.import_root}")
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
