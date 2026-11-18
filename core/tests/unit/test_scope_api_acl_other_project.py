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


def test_write_without_change_does_not_rename_the_rules(tmp_path):
    """"docs/Prüfung 2026-11-18.md", A2: renaming ACLs.md away would remove the rules."""
    a = _project(tmp_path / "A", "read, write, delete")
    acls = a / META_DIR / "ACLs.md"
    assert ScopeApi(str(a)).rename_entry(str(acls), "ACLs-alt") is None
    assert acls.exists()


def _readers_project(tmp_path):
    root = tmp_path / "P"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# Project\n")
    (root / META_DIR / "ACLs.md").write_text(
        "# Permissions\n\n## Team\n- /Arbeit/: read\n- /Arbeit/Geheim.md: none\n\n# Users\nKarl: Team\n")
    (root / "Arbeit").mkdir()
    (root / "Arbeit" / "Offen.md").write_text("x")
    (root / "Arbeit" / "Geheim.md").write_text("x")
    (root / "Privat").mkdir()
    (root / "Privat.md").write_text("x")
    return root


def test_the_quick_list_hides_what_may_not_be_read(tmp_path):
    """"docs/Prüfung 2026-11-18.md", API4: names showed until the full list came."""
    root = _readers_project(tmp_path)
    api = ScopeApi(str(root))
    assert [e["name"] for e in api.list_entries_quick(str(root))] == [e["name"] for e in api.list_entries(str(root))]
    assert [e["name"] for e in api.list_entries_quick(str(root / "Arbeit"))] == ["Offen.md"]


def test_x_ray_hides_files_one_may_not_read(tmp_path):
    """"docs/Prüfung 2026-11-18.md", B5."""
    root = _readers_project(tmp_path)
    shown = [e["name"] for e in ScopeApi(str(root)).list_entries_xray(str(root), 50, True)]
    assert "Offen.md" in shown and "Geheim.md" not in shown


def test_folder_tags_need_write(tmp_path):
    """"docs/Prüfung 2026-11-18.md", API5."""
    root = _readers_project(tmp_path)
    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(root / "Arbeit"), ["wichtig"]) is False
    assert api.set_folder_tag_color(str(root / "Arbeit"), "wichtig", "#ff0000") is False
    assert not (root / "Arbeit" / META_DIR).exists() and not (root / "app.json").exists()


def test_an_unreadable_subfolder_does_not_empty_the_folder_rows(tmp_path, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", API6 (/home, lost+found, other users' folders)."""
    monkeypatch.setenv(env_name("ACL_MODE"), "off")
    root = tmp_path / "Platte"
    for name in ("Fotos", "Gesperrt", "Musik"):
        (root / name).mkdir(parents=True)
    (root / "Gesperrt").chmod(0)
    try:
        api = ScopeApi(str(root))
        assert {c["name"] for c in api.list_children(str(root))} >= {"Fotos", "Musik"}
        assert {e["name"] for e in api.list_entries_quick(str(root))} >= {"Fotos", "Musik"}
    finally:
        (root / "Gesperrt").chmod(0o755)
