#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seiton export - export CLI
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.exporter import export_subtree
from core.brand import COMMAND, NAME  # noqa: E402


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=f"{COMMAND} export", 
        description=f"{NAME} export utility",
    )
    parser.add_argument("path", help="Path inside a project to export")
    parser.add_argument(
        "--out",
        default=".",
        help="Output directory for the export package (default: .)",
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Create a zip archive and remove the export folder",
    )
    return parser.parse_args(args)


def main(argv=None) -> None:
    args = parse_args(argv)
    try:
        result = export_subtree(args.path, args.out, zip_output=args.zip)
        print(f"Exported to {result.package_path}")
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
