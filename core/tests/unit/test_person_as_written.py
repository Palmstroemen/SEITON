"""The person's name as written (core/identity.person_for; Designdocument Time.md, 2): the time
file is named as the person stands in "# Users" - Oliver.md, not oliver.md (on Linux two files)."""

from pathlib import Path

from core.brand import META_DIR, env_name
from core.identity import acl_user_for, person_for


def _project(path: Path, users: str = "") -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# SEITON Project\n")
    if users:
        (path / META_DIR / "ACLs.md").write_text(
            "# Permissions\n\n## Folder\n- /{Folder}/: read, write\n\n# Users\n" + users)
    return path


def test_as_written_in_the_users(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("ACL_USER"), "oliver")
    project = _project(tmp_path / "Küche", "Oliver Rafelsberger: Admin\nOliver: Admin\n")
    assert acl_user_for(project) == "oliver"  # the key, lower-case
    assert person_for(project) == "Oliver"  # as written


def test_not_listed_one_of_ones_own_names_as_written(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv(env_name("ACL_USER"), raising=False)
    from core.identity import identity_file
    identity_file().parent.mkdir(parents=True, exist_ok=True)
    identity_file().write_text("# Identity\nNames: Liesl\n")
    project = _project(tmp_path / "Garten", "Liesl: Admin\n")
    assert person_for(project) == "Liesl"


def test_without_users_the_override_as_written(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("ACL_USER"), "Oliver")
    assert person_for(_project(tmp_path / "Auto")) == "Oliver"
