"""A link is an entry of its own: renaming, deleting or moving it acts on the link, never on
what it points to - that may lie in another project ("docs/Prüfung 2026-11-18.md", API1)."""

from pathlib import Path

import pytest

from core.brand import META_DIR, env_name
from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    for key in (env_name("TEMPLATES_DIR"), env_name("ACL_MODE"), env_name("ACL_USER")):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


@pytest.fixture
def linked(tmp_path):
    projects = {}
    for name in ("A", "B"):
        root = tmp_path / name
        (root / META_DIR).mkdir(parents=True)
        (root / META_DIR / "Project.md").write_text("# Project\n")
        projects[name] = root
    shared = projects["B"] / "Shared"
    shared.mkdir()
    (shared / "plan.md").write_text("Plan\n")
    (projects["B"] / "f.md").write_text("F\n")
    (projects["A"] / "Ablage").mkdir()
    (projects["A"] / "LinkToShared").symlink_to(shared)
    (projects["A"] / "flink.md").symlink_to(projects["B"] / "f.md")
    return projects


def test_renaming_a_link_renames_the_link(linked):
    a, b = linked["A"], linked["B"]
    renamed = ScopeApi(str(a)).rename_entry(str(a / "LinkToShared"), "Geteilt")
    assert renamed == str(a / "Geteilt")
    assert (a / "Geteilt").is_symlink() and (b / "Shared" / "plan.md").exists()


def test_deleting_a_link_deletes_the_link(linked):
    a, b = linked["A"], linked["B"]
    report = ScopeApi(str(a)).delete_entries([str(a / "flink.md"), str(a / "LinkToShared")])
    assert report["ok"], report
    assert not (a / "flink.md").is_symlink() and not (a / "LinkToShared").is_symlink()
    assert (b / "f.md").read_text() == "F\n" and (b / "Shared" / "plan.md").exists()


def test_moving_a_link_moves_the_link(linked):
    a, b = linked["A"], linked["B"]
    report = ScopeApi(str(a)).move_entries([str(a / "LinkToShared")], str(a / "Ablage"))
    assert report["ok"], report
    assert (a / "Ablage" / "LinkToShared").is_symlink()
    assert (b / "Shared" / "plan.md").exists()
    assert ScopeApi(str(a)).move_entry(str(a / "flink.md"), str(a / "Ablage"))
    assert (a / "Ablage" / "flink.md").is_symlink() and (b / "f.md").exists()
