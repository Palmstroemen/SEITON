"""Importing an export package (core/importer.py; decided 2026-11-18, "docs/Prüfung
2026-11-18.md", D8): back to its place when that is still a project (restore), else into a
target as a project of its own (adopt). The project's ACLs always travel with it: imported
into another project, it is a child project with its own rules beside the mother's. Settings
already at the target are never written over; conflicts: skip (default) or overwrite."""

from pathlib import Path

import pytest

from core.brand import META_DIR
from core.exporter import export_subtree
from core.importer import import_package

ACLS = ("# Permissions\n\n## Admin\n- /*: read, write, delete\n- /.seiton/ACLs.md: read, write, change\n\n"
        "## Buchhaltung\n- /4_Finanz/: read, write\n\n# Users\nEva: Admin\nKarl: Buchhaltung\n")


def _firma(root: Path) -> Path:
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# SEITON Project\n")
    (root / META_DIR / "ACLs.md").write_text(ACLS)
    (root / "4_Finanz").mkdir()
    (root / "4_Finanz" / "Rechnung.pdf").write_text("R")
    return root


def test_without_a_target_it_goes_back_to_its_place(tmp_path):
    firma = _firma(tmp_path / "Firma")
    package = export_subtree(firma / "4_Finanz", tmp_path / "out").package_path
    (firma / "4_Finanz" / "Rechnung.pdf").unlink()
    result = import_package(package)
    assert result.import_root == firma.resolve()
    assert (firma / "4_Finanz" / "Rechnung.pdf").read_text() == "R"


def test_into_another_project_it_comes_as_a_child_with_its_own_rights(tmp_path):
    firma = _firma(tmp_path / "Firma")
    package = export_subtree(firma, tmp_path / "out").package_path
    mine = tmp_path / "Mein Rechner" / "Projekte"
    (mine / META_DIR).mkdir(parents=True)
    (mine / META_DIR / "Project.md").write_text("# SEITON Project\n")
    (mine / META_DIR / "ACLs.md").write_text("# Permissions\n\n## Ich\n- /*: *\n\n# Users\nOliver: Ich\n")

    result = import_package(package, target_root=mine)

    child = mine / "Firma"
    assert result.import_root == child.resolve()
    assert (child / "4_Finanz" / "Rechnung.pdf").read_text() == "R"
    assert (child / META_DIR / "ACLs.md").read_text() == ACLS  # the rights travel with it
    project_md = (child / META_DIR / "Project.md").read_text()
    assert "# Export" not in project_md and "ReferencePath" not in project_md
    assert "Oliver: Ich" in (mine / META_DIR / "ACLs.md").read_text()  # the mother's stay


def test_it_never_mixes_with_a_project_already_there(tmp_path):
    firma = _firma(tmp_path / "Firma")
    package = export_subtree(firma, tmp_path / "out").package_path
    target = tmp_path / "Ziel"
    (target / "Firma").mkdir(parents=True)
    with pytest.raises(ValueError):
        import_package(package, target_root=target)


def test_settings_at_the_place_are_never_written_over(tmp_path):
    firma = _firma(tmp_path / "Firma")
    package = export_subtree(firma, tmp_path / "out").package_path  # the whole project
    (firma / META_DIR / "ACLs.md").write_text(ACLS + "Anna: Admin\n")  # changed since
    import_package(package, conflict="overwrite")
    assert "Anna: Admin" in (firma / META_DIR / "ACLs.md").read_text()
    assert "# Export" not in (firma / META_DIR / "Project.md").read_text()


def test_merge_is_no_conflict_mode_any_more(tmp_path):
    firma = _firma(tmp_path / "Firma")
    package = export_subtree(firma, tmp_path / "out").package_path
    with pytest.raises(ValueError):
        import_package(package, conflict="merge")
