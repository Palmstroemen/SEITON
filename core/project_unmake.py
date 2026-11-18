# project_unmake.py - a project becomes an ordinary folder again (crossed-out P-Button)
#
# Creating a project remembers what it wrote into .MyOS (CREATED, names and checksums).
# Turning it back removes .MyOS when nothing of its own came since (changed rights, tags,
# a trash with entries, ...); otherwise only with consent, and then .MyOS is not deleted
# but goes into the parent project's trash as "SEITON settings". Not for the top project,
# not outside the projects tree; subprojects stay projects.

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List

from core import trash
from core.template_place import find_templates_dir
from core.brand import META_DIR, NAME, legacy_project_headings, project_heading

CREATED = ".created.json"  # in .MyOS: what creating the project wrote
SETTINGS_NAME = f"{NAME} settings"  # .seiton with settings of its own, in the parent's trash


class ProjectHasOwnSettings(Exception):
    """The project has settings of its own; turning it back needs consent (keep_own)."""

    def __init__(self, names: List[str]) -> None:
        super().__init__(", ".join(names))
        self.names = names


def settings_before(folder: Path) -> List[str]:
    """What the folder's .MyOS holds before it becomes a project (its tags, a sort rule, ...):
    the folder's, not the project's - turning the project back leaves it."""
    settings_dir = Path(folder) / META_DIR
    try:
        return sorted(item.name for item in settings_dir.iterdir())
    except OSError:
        return []


def record_created(project_root: Path, before: List[str] = ()) -> None:
    """Remember the files creating the project wrote into its .MyOS, and what was there
    before (settings_before), which is not the project's."""
    settings_dir = Path(project_root) / META_DIR
    kept = set(before)
    files = {item.name: _checksum(item) for item in settings_dir.iterdir()
             if not item.name.startswith(".") and item.is_file() and not item.is_symlink() and item.name not in kept}
    (settings_dir / CREATED).write_text(json.dumps({"created": files, "kept": sorted(kept)}, indent=2, sort_keys=True),
                                        encoding="utf-8")


def can_unmake(path: Path) -> bool:
    """Whether path is a project that can become an ordinary folder again."""
    target = Path(path).expanduser().resolve()
    if not (target / META_DIR / "Project.md").is_file():
        return False
    if not any((parent / META_DIR / "Project.md").is_file() for parent in target.parents):
        return False  # the top project of the projects tree
    templates_dir = find_templates_dir(target)
    return templates_dir is None or templates_dir.resolve() not in target.parents


def own_settings(project_root: Path) -> List[str]:
    """Names in the project's .MyOS that creating it did not write (or that changed since)."""
    settings_dir = Path(project_root) / META_DIR
    created, kept = _created(settings_dir), _kept(settings_dir)
    own = []
    for item in sorted(settings_dir.iterdir(), key=lambda p: p.name):
        if item.name in kept:
            continue  # the folder's, from before it was a project
        if item.name.startswith("."):
            continue  # caches and drafts (.TagsHere.json, ...)
        if item.is_symlink():
            own.append(item.name)
        elif item.is_dir():
            if any(p.is_file() or p.is_symlink() for p in item.rglob("*")):
                own.append(item.name)
        elif item.name == "Project.md":
            if created.get(item.name) != _checksum(item) and _marker_body(item) not in (project_heading(), *legacy_project_headings()):
                own.append(item.name)
        elif created.get(item.name) != _checksum(item):
            own.append(item.name)
    return own


def unmake_project(project_root: Path, user: str, keep_own: bool = False) -> None:
    """
    Make project_root an ordinary folder again. With settings of its own this needs
    keep_own (else ProjectHasOwnSettings): its .MyOS then goes into the parent project's
    trash as SETTINGS_NAME (restorable), instead of being deleted.
    """
    root = Path(project_root).expanduser().resolve()
    if not can_unmake(root):
        raise ValueError(f"{root} cannot become an ordinary folder")
    own = own_settings(root)
    settings_dir = root / META_DIR
    kept = _kept(settings_dir)
    if own and not keep_own:
        raise ProjectHasOwnSettings(own)
    project_part = [item for item in settings_dir.iterdir() if item.name not in kept]
    if not own:
        # Only what creating it wrote, caches and empty folders: nothing to keep.
        for item in project_part:
            shutil.rmtree(item) if item.is_dir() and not item.is_symlink() else item.unlink()
    else:
        # Moved out first (the marker with it), so root is no project any more and its parent
        # project takes them into its trash.
        settings = root / SETTINGS_NAME
        number = 2
        while settings.exists():
            settings = root / f"{SETTINGS_NAME} {number}"
            number += 1
        if kept:
            settings.mkdir()
            for item in project_part:
                item.rename(settings / item.name)
        else:
            settings_dir.rename(settings)
        trash.move_to_trash(settings, deleted_by=user)
    if settings_dir.is_dir() and not any(settings_dir.iterdir()):
        settings_dir.rmdir()


def _record(settings_dir: Path) -> dict:
    try:
        data = json.loads((settings_dir / CREATED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    # Written before 2026-11-18: only the created files, names to checksums.
    return data if isinstance(data.get("created"), dict) else {"created": data, "kept": []}


def _created(settings_dir: Path) -> Dict[str, str]:
    return dict(_record(settings_dir).get("created") or {})


def _kept(settings_dir: Path) -> set:
    kept = _record(settings_dir).get("kept") or []
    return {name for name in kept if isinstance(name, str)}


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _marker_body(path: Path) -> str:
    """Project.md without its front matter (PostFix keeps window positions there)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5:]
    return text.strip()
