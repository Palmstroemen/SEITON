#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seiton drive - mount the "Perspektiven" drive: the turned tree of a projects root
(/04_Finanz/Projekte/Job = Projekte/Job/04_Finanz; see core/perspective_fuse.py).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.acl_enforcement import allowed_at
from core.perspective_fuse import mount_perspective_drive
from core.brand import COMMAND, NAME  # noqa: E402


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=f"{COMMAND} drive", description=f"Mount the {NAME} perspective drive (turned tree)")
    parser.add_argument("--projects-root", "--project-root", dest="projects_root", required=True,
                        help="The projects root (the folder holding the projects, e.g. .../Projekte)")
    parser.add_argument("--mount-point", required=True,
                        help="Where the drive appears (e.g. .../Perspektiven next to Projekte)")
    parser.add_argument("--foreground", action="store_true", help="Run fuse in foreground")
    return parser.parse_args(args)


def main(argv=None) -> None:
    args = parse_args(argv)
    mount_perspective_drive(
        projects_root=str(Path(str(args.projects_root)).expanduser().resolve()),
        mount_point=str(Path(str(args.mount_point)).expanduser().resolve()),
        foreground=bool(args.foreground),
        # Security: the person's ACLs at every path, as in Scope and the daemon's drive (B11).
        may=lambda path, action: allowed_at(path, action),
    )


if __name__ == "__main__":
    main()
