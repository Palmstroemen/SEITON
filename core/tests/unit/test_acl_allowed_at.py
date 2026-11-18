"""core.acl_enforcement.allowed_at: whether the person may do something at a path, by the
ACLs.md that governs that path (its own project, or the parent's it inherits), whatever program
asks and whatever project it is in otherwise. Off and monitor allow everything."""

from pathlib import Path

import pytest

from core.acl_enforcement import allowed_at
from core.brand import META_DIR, env_name

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: *\n\n"
    "## Team\n- /Arbeit/: read, write\n- /Arbeit/Geheim/: none\n\n"
    "# Users\nAnna: Admin\nKarl: Team\n"
)
OTHER = "# Permissions\n\n## Admin\n- /*: *\n\n# Users\nKarl: Admin\n"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for key in (env_name("ACL_BACKEND"), env_name("ACL_USER")):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(env_name("ACL_MODE"), "enforce")


def _project(root: Path, acls: str) -> Path:
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# Project\n")
    (root / META_DIR / "ACLs.md").write_text(acls)
    return root


def test_the_rules_of_the_path_decide(tmp_path, monkeypatch):
    root = _project(tmp_path / "Firma", ACLS)
    (root / "Arbeit" / "Geheim").mkdir(parents=True)
    monkeypatch.setenv(env_name("ACL_USER"), "karl")
    assert allowed_at(root / "Arbeit" / "Notiz.md", "write")
    assert not allowed_at(root / "Arbeit" / "Geheim" / "Notiz.md", "write")
    assert not allowed_at(root / "Arbeit" / "Notiz.md", "delete")
    monkeypatch.setenv(env_name("ACL_USER"), "anna")
    assert allowed_at(root / "Arbeit" / "Geheim" / "Notiz.md", "write")


def test_another_project_has_its_own_rules(tmp_path, monkeypatch):
    _project(tmp_path / "Firma", ACLS)
    other = _project(tmp_path / "Verein", OTHER)
    monkeypatch.setenv(env_name("ACL_USER"), "karl")
    assert allowed_at(other / "Kasse.md", "write")  # Admin there, Team in the first


def test_a_subproject_without_rules_inherits(tmp_path, monkeypatch):
    root = _project(tmp_path / "Firma", ACLS)
    sub = root / "Arbeit" / "Kunde"
    (sub / META_DIR).mkdir(parents=True)
    (sub / META_DIR / "Project.md").write_text("# Sub\n")
    monkeypatch.setenv(env_name("ACL_USER"), "karl")
    assert allowed_at(sub / "Notiz.md", "write")
    assert not allowed_at(sub / "Notiz.md", "delete")


def test_without_rules_or_enforcement_everything_is_allowed(tmp_path, monkeypatch):
    plain = tmp_path / "Ordner"
    plain.mkdir()
    monkeypatch.setenv(env_name("ACL_USER"), "karl")
    assert allowed_at(plain / "Notiz.md", "write")
    root = _project(tmp_path / "Firma", ACLS)
    for mode in ("off", "monitor"):
        monkeypatch.setenv(env_name("ACL_MODE"), mode)
        assert allowed_at(root / "Arbeit" / "Geheim" / "x.md", "write")


def test_an_unknown_mode_enforces(monkeypatch):
    """A typo must not switch the checks off ("docs/Prüfung 2026-11-18.md", A6; ACL_ROLLOUT 1)."""
    from core.acl_enforcement import configured_mode

    for value, mode in (("enforec", "enforce"), ("ENFORCE", "enforce"), ("monitor", "monitor"),
                        ("off", "off"), ("", "off")):
        monkeypatch.setenv(env_name("ACL_MODE"), value)
        assert configured_mode() == mode, value
    monkeypatch.delenv(env_name("ACL_MODE"))
    assert configured_mode() == "off"
