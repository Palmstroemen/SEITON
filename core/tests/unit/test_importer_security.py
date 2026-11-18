# test_importer_security.py

import tempfile
import zipfile
from pathlib import Path

import pytest

from core.importer import import_package
from core.brand import META_DIR


def _write_export_project(project_root: Path, subtree: str) -> None:
    settings_dir = project_root / META_DIR
    settings_dir.mkdir(parents=True, exist_ok=True)
    project_md = settings_dir / "Project.md"
    project_md.write_text(
        "# MyOS Project\n"
        "# Export\n"
        f"ReferencePath: {project_root}\n"
        f"Subtree: {subtree}\n"
        "ExportedAt: 2026-02-02T00:00:00Z\n"
        "Source: test@host\n"
    )


def test_import_rejects_missing_project_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()
        with pytest.raises(ValueError):
            import_package(package, target_root=tmp / "target", mode="adopt")


def test_import_rejects_subtree_traversal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()

        _write_export_project(package, "/../evil")
        (package / "evil").mkdir()

        with pytest.raises(ValueError):
            import_package(package, target_root=tmp / "target", mode="adopt")


def test_import_rejects_symlinks():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()

        _write_export_project(package, "/data")
        data_dir = package / "data"
        data_dir.mkdir(parents=True)

        secret = package / "secret.txt"
        secret.write_text("secret")
        (data_dir / "link.txt").symlink_to(secret)

        with pytest.raises(ValueError):
            import_package(package, target_root=tmp / "target", mode="adopt")


def test_import_rejects_zip_traversal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        zip_path = tmp / "attack.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../evil.txt", "boom")

        with pytest.raises(ValueError):
            import_package(zip_path, target_root=tmp / "target", mode="adopt")


def test_import_basic_adopt():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()

        _write_export_project(package, "/data")
        data_dir = package / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "note.txt").write_text("hello")

        target = tmp / "target"
        target.mkdir()

        result = import_package(package, target_root=target, mode="adopt")

        # A project of its own, named as the exported one (D8): here the package's folder.
        assert (target / "package" / "data" / "note.txt").exists()
        assert result.import_root == target.resolve() / "package"


def _package_pointing_at(tmp: Path, reference: Path) -> Path:
    package = tmp / "package"
    (package / META_DIR).mkdir(parents=True)
    (package / META_DIR / "Project.md").write_text(
        f"# Project\n# Export\nReferencePath: {reference}\nSubtree: /.\nExportedAt: 2026-02-02T00:00:00Z\n")
    (package / ".config" / "autostart").mkdir(parents=True)
    (package / ".config" / "autostart" / "x.desktop").write_text("[Desktop Entry]\nExec=evil\n")
    return package


def test_restore_writes_only_into_a_project(tmp_path):
    """"docs/Prüfung 2026-11-18.md", D2: a package naming the home as its place wrote an
    autostart entry there."""
    home = tmp_path / "home"
    home.mkdir()
    package = _package_pointing_at(tmp_path, home)
    with pytest.raises(ValueError):
        import_package(package, mode="restore")
    assert not (home / ".config").exists()


def test_restore_with_a_target_goes_there(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    package = _package_pointing_at(tmp_path, home)
    import_package(package, target_root=target)  # with a target: adopted there, never the home
    assert not (home / ".config").exists()
    assert (target / "home" / ".config" / "autostart" / "x.desktop").exists()
