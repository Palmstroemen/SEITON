#!/usr/bin/env python3
"""
importer.py - MyOS import utilities.
Imports a subtree from an export package with security checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Dict
import logging
import os
import re
import shutil
import tempfile
import zipfile
from core.brand import META_DIR

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImportResult:
    import_root: Path
    subtree_path: Path


CONFLICTS = ("skip", "overwrite")


def import_package(
    package_path: Union[str, Path],
    target_root: Optional[Union[str, Path]] = None,
    mode: str = "auto",
    conflict: str = "skip",
) -> ImportResult:
    """
    Import an export package (decided 2026-11-18): back to its place when that is still a
    project (restore), else into target_root as a project of its own (adopt) - a folder named
    as the exported project, with the package's settings: its ACLs always travel with it, so
    in another project it is a child with its own rights beside the mother's.

    Args:
        package_path: Path to an export folder or zip archive.
        target_root: Where to adopt it; without one it is restored.
        mode: "auto" (restore without a target, else adopt), "restore" or "adopt".
        conflict: "skip" (files already there stay) or "overwrite". Settings already at the
            place (a .MyOS there) are never written over.

    Returns:
        ImportResult describing the import.
    """
    if mode not in {"auto", "restore", "adopt"}:
        raise ValueError(f"Invalid mode: {mode}")
    if conflict not in CONFLICTS:
        raise ValueError(f"Invalid conflict mode: {conflict} (skip or overwrite)")
    package_path = Path(package_path).expanduser().resolve()

    if package_path.is_file() and package_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmpdir:
            extracted = Path(tmpdir) / "package"
            extracted.mkdir(parents=True, exist_ok=True)
            _safe_extract_zip(package_path, extracted)
            return _import_from_folder(extracted, target_root, mode, conflict)

    if package_path.is_dir():
        return _import_from_folder(package_path, target_root, mode, conflict)

    raise FileNotFoundError(f"Import package not found: {package_path}")


def _import_from_folder(
    package_root: Path,
    target_root: Optional[Union[str, Path]],
    mode: str,
    conflict: str,
) -> ImportResult:
    project_md = package_root / META_DIR / "Project.md"
    if not project_md.exists():
        raise ValueError(f"Invalid package: missing {META_DIR}/Project.md")

    metadata = _read_export_metadata(project_md)
    subtree = metadata.get("Subtree")
    if not subtree:
        raise ValueError("Missing Subtree in export metadata")

    subtree_path = _validate_subtree_path(subtree)
    source_subtree = package_root / subtree_path
    if not source_subtree.exists():
        raise FileNotFoundError(f"Subtree not found in package: {subtree_path}")

    if mode == "restore" or (mode == "auto" and target_root is None):
        import_root = _restore_place(metadata)
    else:
        import_root = _adopt_place(metadata, target_root)
        # A project of its own: the package's settings with it - its ACLs above all, whoever
        # they name (they keep their rights wherever the project goes next).
        _copy_tree_secure(package_root / META_DIR, import_root / META_DIR, "skip")
        _drop_export_block(import_root / META_DIR / "Project.md")
    _copy_tree_secure(source_subtree, import_root / subtree_path, conflict)

    return ImportResult(import_root=import_root, subtree_path=subtree_path)


def _restore_place(metadata: Dict[str, str]) -> Path:
    """The package's own place - taken only when it is still a project. Security: else a package
    could write anywhere it names (an autostart entry into the home, D2)."""
    ref = metadata.get("ReferencePath")
    if ref:
        ref_path = Path(ref).expanduser().resolve()
        if (ref_path / META_DIR / "Project.md").is_file():
            return ref_path
        raise ValueError(f"{ref_path} is no project any more: give a target (--target) to adopt it")
    raise ValueError("The package names no place: give a target (--target) to adopt it")


def _adopt_place(metadata: Dict[str, str], target_root: Optional[Union[str, Path]]) -> Path:
    """target_root/<the exported project's name>, new: it never mixes with what is there."""
    if target_root is None:
        raise ValueError("Adopting needs a target (--target)")
    target = Path(target_root).expanduser().resolve()
    if not target.is_dir():
        raise ValueError(f"Target is no folder: {target}")
    name = Path(metadata.get("ReferencePath") or "").name or "Import"
    place = target / name
    if place.exists() or place.is_symlink():
        raise ValueError(f"{place} exists already: the import does not mix with it")
    place.mkdir()
    return place


def _drop_export_block(project_md: Path) -> None:
    """Project.md without the "# Export" block the exporter wrote (where it came from)."""
    if not project_md.is_file():
        return
    text = project_md.read_text(encoding="utf-8")
    kept = re.sub(r"(?ms)^# Export\s*\n.*?(?=^# |\Z)", "", text).rstrip("\n") + "\n"
    project_md.write_text(kept, encoding="utf-8")


def _read_export_metadata(project_md: Path) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    for line in project_md.read_text().splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            if key in {"ReferencePath", "Subtree", "ExportedAt", "Source"}:
                metadata[key] = value.strip()
    return metadata


def _validate_subtree_path(subtree: str) -> Path:
    subtree = subtree.strip()
    if subtree.startswith("/"):
        subtree = subtree[1:]
    path = Path(subtree)
    if path.is_absolute():
        raise ValueError("Subtree path must be relative")
    if ".." in path.parts:
        raise ValueError("Subtree path traversal not allowed")
    return path


def _copy_tree_secure(src: Path, dst: Path, conflict: str) -> None:
    """Copy src to dst without symlinks; a file there already stays (skip) or is replaced
    (overwrite) - but never one in a .MyOS: the settings and rights of a project at the place."""
    if conflict not in CONFLICTS:
        raise ValueError(f"Invalid conflict mode: {conflict}")
    if src.is_file():  # a package of a single file (D6)
        if src.is_symlink():
            raise ValueError("Symlinked files are not allowed in import")
        if dst.exists() and conflict != "overwrite":
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return

    for root, dirs, files in os.walk(src, followlinks=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(src)
        target_root = dst / rel_root
        target_root.mkdir(parents=True, exist_ok=True)

        for name in list(dirs):
            if (root_path / name).is_symlink():
                raise ValueError("Symlinked directories are not allowed in import")

        for name in files:
            src_file = root_path / name
            if src_file.is_symlink():
                raise ValueError("Symlinked files are not allowed in import")
            dest_file = target_root / name
            if dest_file.exists():
                if conflict == "skip" or META_DIR in dest_file.relative_to(dst).parts[:-1] \
                        or dst.name == META_DIR:
                    continue
                dest_file.unlink()
            shutil.copy2(src_file, dest_file)


def _safe_extract_zip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            name = member.filename
            # Security: no absolute path, no drive letter (C:...); a colon elsewhere is a
            # usual file name on Linux (a time, "Besprechung 10:30.md") and stays allowed.
            if name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name):
                raise ValueError("Unsafe path in zip archive")
            member_path = (dest / name).resolve()
            if not member_path.is_relative_to(dest.resolve()):
                raise ValueError("Zip traversal detected")
            zf.extract(member, dest)
