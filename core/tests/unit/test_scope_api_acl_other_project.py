"""ScopeApi checks a path by the ACLs.md that governs that path, not by the rules of the project
Scope stands in ("docs/Prüfung 2026-11-18.md", API2); a changed ACLs.md counts at once."""

from pathlib import Path

import pytest

from core.brand import META_DIR, env_name
from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    for key in (env_name("TEMPLATES_DIR"), env_name("ACL_BACKEND"), env_name("ACL_AUDIT")):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(env_name("ACL_MODE"), "enforce")
    monkeypatch.setenv(env_name("ACL_USER"), "karl")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


def _project(root: Path, rights: str) -> Path:
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# Project\n")
    (root / META_DIR / "ACLs.md").write_text(
        f"# Permissions\n\n## Team\n- /*: {rights}\n\n# Users\nKarl: Team\n")
    (root / "Inbox").mkdir()
    return root


def test_moving_into_a_project_that_forbids_it_is_refused(tmp_path):
    a = _project(tmp_path / "A", "*")
    b = _project(tmp_path / "B", "read")
    note = a / "note.md"
    note.write_text("x")
    api = ScopeApi(str(a))

    assert api.acl_allows("write", a / "Inbox")
    assert not api.acl_allows("write", b / "Inbox")
    api.move_entries([str(note)], str(b / "Inbox"))
    assert note.exists() and not (b / "Inbox" / "note.md").exists()


def test_from_a_strict_project_another_one_allows_by_its_own_rules(tmp_path):
    a = _project(tmp_path / "A", "*")
    b = _project(tmp_path / "B", "read")
    api = ScopeApi(str(b))

    assert not api.acl_allows("write", b / "Inbox")
    assert api.acl_allows("write", a / "Inbox")


def test_outside_every_project_no_rules_apply(tmp_path):
    b = _project(tmp_path / "B", "read")
    elsewhere = tmp_path / "Ablage"
    elsewhere.mkdir()
    assert ScopeApi(str(b)).acl_allows("write", elsewhere)


def test_a_changed_acls_md_counts_at_once(tmp_path):
    a = _project(tmp_path / "A", "*")
    api = ScopeApi(str(a))
    assert api.acl_allows("write", a / "Inbox")
    acls = a / META_DIR / "ACLs.md"
    acls.write_text(acls.read_text().replace("/*: *", "/*: read"))
    assert not api.acl_allows("write", a / "Inbox")
