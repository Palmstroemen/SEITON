"""Rules for everyone, and {Self} (core/acl.py; "Designdocument Time.md" 7.4, decided
2026-11-16): "## Everyone" holds rules for every person of the project (in "# Users"), and
{Self} in such a rule is the asking person, as written there. So everyone writes their own time
file, and only their own. The rules only give rights, they apply again in every subproject the
ACLs.md governs (like "## Folder"), and both backends agree."""

from pathlib import Path

import pytest

from core.acl import ACLAuthorizer, ACLPolicy
from core.brand import META_DIR, env_name


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)


ACLS = (
    "# Permissions\n\n"
    "## Folder\n- /{Folder}/: read, write\n\n"
    "## Everyone\n- /0_Admin/Zeitaufwand/{Self}.md: read, write\n- /1_Info/: read\n\n"
    "## Leitung\n- /*: read, write\n\n"
    "# Users\nOliver Rafelsberger: Leitung\nAnna: 4_Finanz\nBen: 1_Info\n"
)


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True)
    (path / META_DIR / "Project.md").write_text("# Project\n")
    (path / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    return path


@pytest.fixture
def world(tmp_path):
    root = _project(tmp_path / "Firma")
    for folder in ("0_Admin", "1_Info", "4_Finanz"):
        (root / META_DIR / "Templates" / "Standard" / folder).mkdir(parents=True)
        (root / folder).mkdir()
    sub = _project(root / "Huber")
    (root / META_DIR / "ACLs.md").write_text(ACLS)
    return root, sub


BACKENDS = ["legacy", "casbin"]


def _can(root, user, path, right, backend, context=None):
    return ACLAuthorizer.from_project(root, backend=backend, context=context).can_user_access(user, path, right)


@pytest.mark.parametrize("backend", BACKENDS)
def test_everyone_writes_their_own_time_file(world, backend):
    root, _sub = world
    assert _can(root, "anna", "/0_Admin/Zeitaufwand/Anna.md", "write", backend)
    assert _can(root, "ben", "/0_Admin/Zeitaufwand/Ben.md", "write", backend)


@pytest.mark.parametrize("backend", BACKENDS)
def test_but_not_another_ones(world, backend):
    root, _sub = world
    assert not _can(root, "anna", "/0_Admin/Zeitaufwand/Ben.md", "write", backend)
    assert not _can(root, "anna", "/0_Admin/Zeitaufwand/Ben.md", "read", backend)
    assert not _can(root, "anna", "/0_Admin/Ziele.md", "read", backend)


@pytest.mark.parametrize("backend", BACKENDS)
def test_self_is_the_name_as_written_in_users(world, backend):
    root, _sub = world
    assert _can(root, "oliver rafelsberger", "/0_Admin/Zeitaufwand/Oliver Rafelsberger.md", "write", backend)
    # Anna's file is "Anna.md", not "anna.md": paths keep their case
    assert not _can(root, "anna", "/0_Admin/Zeitaufwand/anna.md", "write", backend)


@pytest.mark.parametrize("backend", BACKENDS)
def test_everyone_rules_without_self_hold_for_all(world, backend):
    root, _sub = world
    assert _can(root, "anna", "/1_Info/Telefonliste.md", "read", backend)
    assert not _can(root, "anna", "/1_Info/Telefonliste.md", "write", backend)


@pytest.mark.parametrize("backend", BACKENDS)
def test_someone_not_in_the_project_is_not_everyone(world, backend):
    root, _sub = world
    assert not _can(root, "mallory", "/0_Admin/Zeitaufwand/Mallory.md", "write", backend)
    assert not _can(root, "mallory", "/1_Info/Telefonliste.md", "read", backend)


@pytest.mark.parametrize("backend", BACKENDS)
def test_everyone_rules_only_give_rights(world, backend):
    root, _sub = world
    # the other roles keep theirs: Leitung reads every time file
    assert _can(root, "oliver rafelsberger", "/0_Admin/Zeitaufwand/Anna.md", "read", backend)
    assert _can(root, "anna", "/4_Finanz/Belege.md", "write", backend)


@pytest.mark.parametrize("backend", BACKENDS)
def test_in_a_subproject_too(world, backend):
    root, sub = world
    path = "/Huber/0_Admin/Zeitaufwand/Ben.md"
    assert _can(root, "ben", path, "write", backend, context=sub)
    assert not _can(root, "anna", "/Huber/0_Admin/Zeitaufwand/Ben.md", "read", backend, context=sub)


@pytest.mark.parametrize("name", ["../Anna", "a/b", "*", "Anna?"])
def test_a_name_that_would_widen_the_rule_gives_nothing(world, name):
    root, _sub = world
    acls = (root / META_DIR / "ACLs.md")
    acls.write_text(ACLS + f"{name}: 1_Info\n")
    policy = ACLPolicy.from_project(root)
    key = name.lower()
    assert policy.everyone_rights(key, "/0_Admin/Zeitaufwand/Ben.md") == set()
    assert policy.everyone_rights(key, "/0_Admin/Ziele.md") == set()


def test_everyone_is_no_role_of_its_own(world):
    root, _sub = world
    policy = ACLPolicy.from_project(root)
    assert "everyone" not in policy.roles and "everyone" not in policy.permissions
