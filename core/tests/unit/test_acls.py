import tempfile
from pathlib import Path

import pytest
from core.brand import META_DIR


def _write_templates(project_root: Path, template_name: str, folders: list[str]) -> None:
    templates_root = project_root / META_DIR / "Templates" / template_name
    templates_root.mkdir(parents=True, exist_ok=True)
    for folder in folders:
        (templates_root / folder).mkdir(parents=True, exist_ok=True)


def _write_project_config(project_root: Path, template_name: str) -> None:
    settings_dir = project_root / META_DIR
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "Project.md").write_text("# MyOS Project\n")
    (settings_dir / "Templates.md").write_text(f"# Templates\n{template_name}\n")


def _write_acls(project_root: Path) -> None:
    settings_dir = project_root / META_DIR
    (settings_dir / "ACLs.md").write_text(
        "# Permissions\n"
        "\n"
        "## Folder\n"
        "- /{Folder}/: read, write\n"
        "- /info/: read\n"
        "\n"
        "## Admin\n"
        "- /*: read, write, execute\n"
        f"- /{META_DIR}/ACLs.md: change\n"
        "\n"
        "## Worker\n"
        "- /info/: read\n"
        "- /kommunikation/: read\n"
        "\n"
        "# Users\n"
        "Oliver: Admin, Worker\n"
        "Mia: Worker\n"
    )


def test_acl_roles_from_template_and_custom_roles():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "Project"
        project_root.mkdir(parents=True)

        _write_templates(project_root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(project_root, "Standard")
        _write_acls(project_root)

        policy = ACLPolicy.from_project(project_root)

        assert "admin" in policy.roles
        assert "info" in policy.roles
        assert "kommunikation" in policy.roles
        assert "worker" in policy.roles


def test_acl_permissions_basic_checks():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "Project"
        project_root.mkdir(parents=True)

        _write_templates(project_root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(project_root, "Standard")
        _write_acls(project_root)

        policy = ACLPolicy.from_project(project_root)

        assert policy.can_access("worker", "/info", "read")
        assert not policy.can_access("worker", "/info", "write")
        assert policy.can_access("worker", "/kommunikation/extern", "read")
        assert not policy.can_access("worker", "/admin")

        assert policy.can_access("admin", "/admin", "read")
        assert policy.can_access("admin", "/any/other/path", "write")
        assert not policy.can_access("admin", "/any/other/path", "change")
        assert policy.can_access("admin", f"/{META_DIR}/ACLs.md", "change")

        assert policy.can_access("info", "/info", "write")
        assert policy.can_access("kommunikation", "/kommunikation", "read")


def test_acl_users_role_mapping():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "Project"
        project_root.mkdir(parents=True)

        _write_templates(project_root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(project_root, "Standard")
        _write_acls(project_root)

        policy = ACLPolicy.from_project(project_root)

        assert policy.roles_for_user("Oliver") == {"admin", "worker"}
        assert policy.roles_for_user("mia") == {"worker"}
        assert policy.roles_for_user("Unknown") == set()


def test_acl_roles_from_inherited_templates_runtime_resolution():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "RootProject"
        child = root / "SubProject"
        root.mkdir(parents=True)
        child.mkdir(parents=True)

        _write_templates(root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(root, "Standard")
        _write_acls(root)

        child_settings = child / META_DIR
        child_settings.mkdir(parents=True)
        (child_settings / "Project.md").write_text("# MyOS Project\n")

        policy = ACLPolicy.from_project(child)
        assert "admin" in policy.roles
        assert "info" in policy.roles
        assert "kommunikation" in policy.roles


def test_acl_finance_glob_patterns_and_default_deny():
    from core.acl import ACLPolicy, PermissionRule

    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"read", "write", "execute"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )

    assert policy.can_access("finance", "/Finanz", "read")
    assert policy.can_access("finance", "/Finanz/Q1", "write")
    assert policy.can_access("finance", "/Finanz/Reports/2026", "read")
    assert not policy.can_access("finance", "/HR", "read")
    assert not policy.can_access("finance", "/Finanzen", "read")
    assert not policy.can_access("finance", "/Finanz", "delete")


def _build_authorizer_fixture(backend: str):
    from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule

    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLAuthorizer(policy, backend=backend)


@pytest.mark.parametrize("backend", ["legacy", "casbin"])
def test_a_name_like_a_role_gives_no_rights(backend):
    """People and roles are apart ("docs/Prüfung 2026-11-18.md", A1): someone not in # Users
    whose name is a role's gets nothing; a person named like a group passes no groups on."""
    import core.acl as acl_module
    from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule

    if backend == "casbin" and acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")
    policy = ACLPolicy(
        roles={"admin", "team"},
        permissions={"admin": [PermissionRule(path="/*", rights={"*"})],
                     "team": [PermissionRule(path="/0_Admin/**", rights={"read"})]},
        users={"anna": {"team"}, "team": {"admin"}},
    )
    auth = ACLAuthorizer(policy, backend=backend)
    assert auth.backend == backend
    assert not auth.can_user_access("admin", "/4_Finanz", "read")  # not listed
    assert not auth.can_user_access("anna", "/4_Finanz", "read")  # Team, not Admin
    assert auth.can_user_access("anna", "/0_Admin/x", "read")
    assert auth.can_user_access("team", "/4_Finanz", "write")  # the person Team is Admin
    assert not auth.can_access("team", "/4_Finanz", "write")  # the role Team is not


@pytest.mark.parametrize("backend", ["legacy", "casbin"])
def test_the_rights_files_need_change_also_to_be_moved_or_deleted(backend):
    """write or delete on ACLs.md (and the other files that manage rights) right in a settings
    folder, or on that folder itself, needs "change" ("docs/Prüfung 2026-11-18.md", A2)."""
    import core.acl as acl_module
    from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule

    if backend == "casbin" and acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")
    policy = ACLPolicy(
        roles={"admin", "prokura"},
        permissions={"admin": [PermissionRule(path="/*", rights={"*"})],
                     "prokura": [PermissionRule(path="/*", rights={"read", "write", "delete"})]},
        users={"anna": {"admin"}, "paul": {"prokura"}},
    )
    auth = ACLAuthorizer(policy, backend=backend)
    for path in (f"/{META_DIR}/ACLs.md", f"/Kunde/{META_DIR}/ACLs.md", f"/{META_DIR}/Nextcloud.md", f"/{META_DIR}"):
        for right in ("write", "delete"):
            assert not auth.can_user_access("paul", path, right), (path, right)
            assert auth.can_user_access("anna", path, right), (path, right)
    assert auth.can_user_access("paul", f"/{META_DIR}/ACLs.md", "read")
    assert auth.can_user_access("paul", f"/{META_DIR}/Tags.md", "write")  # not a rights file
    assert auth.can_user_access("paul", "/Notizen/ACLs.md", "write")  # not in a settings folder


@pytest.mark.parametrize("backend", ["legacy", "casbin"])
def test_a_lock_with_a_wildcard_in_the_middle_still_locks(backend):
    """"docs/Prüfung 2026-11-18.md", A9: /*/Geheim/ is deeper than /Finanz/, its none must win."""
    import core.acl as acl_module
    from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule

    if backend == "casbin" and acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")
    policy = ACLPolicy(
        roles={"team"},
        permissions={"team": [PermissionRule(path="/Finanz", rights={"read", "write"}),
                              PermissionRule(path="/*/Geheim", rights={"none"})]},
        users={"karl": {"team"}},
    )
    auth = ACLAuthorizer(policy, backend=backend)
    assert auth.can_user_access("karl", "/Finanz/Rechnung.pdf", "read")
    assert not auth.can_user_access("karl", "/Finanz/Geheim/Gehalt.pdf", "read")
    assert not auth.can_user_access("karl", "/Finanz/Geheim", "read")


def test_acl_authorizer_auto_backend_available():
    authorizer = _build_authorizer_fixture("auto")
    assert authorizer.backend in {"legacy", "casbin"}
    assert authorizer.can_access("finance", "/Finanz/Q1", "read")


def test_acl_authorizer_legacy_user_checks():
    authorizer = _build_authorizer_fixture("legacy")
    assert authorizer.backend == "legacy"
    assert authorizer.can_user_access("bertha", "/Finanz/Q1", "read")
    assert not authorizer.can_user_access("bertha", "/HR", "read")
    assert authorizer.can_user_access("alfred", "/Admin", "execute")


def test_acl_authorizer_casbin_backend_parity_if_installed():
    import core.acl as acl_module

    if acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")

    legacy = _build_authorizer_fixture("legacy")
    casbin_auth = _build_authorizer_fixture("casbin")
    assert casbin_auth.backend == "casbin"

    checks = [
        ("finance", "/Finanz", "read"),
        ("finance", "/Finanz/2026/report", "write"),
        ("finance", "/Finanzen", "read"),
        ("admin", "/Any/Path", "delete"),
    ]
    for role, path, right in checks:
        assert casbin_auth.can_access(role, path, right) == legacy.can_access(role, path, right)

    user_checks = [
        ("bertha", "/Finanz/Q2", "read"),
        ("bertha", "/HR", "read"),
        ("alfred", "/whatever", "write"),
    ]
    for user, path, right in user_checks:
        assert casbin_auth.can_user_access(user, path, right) == legacy.can_user_access(user, path, right)


def test_template_role_gets_its_folder_with_original_case(tmp_path):
    """{Folder} expands to the template folder's real name; paths are case-sensitive."""
    from core.acl import ACLPolicy

    project_root = tmp_path / "Project"
    project_root.mkdir()
    _write_templates(project_root, "Standard", ["04_Finanz", "01_Info"])
    _write_project_config(project_root, "Standard")
    (project_root / META_DIR / "ACLs.md").write_text(
        "# Permissions\n\n## Folder\n- /{Folder}/: read, write\n"
    )

    policy = ACLPolicy.from_project(project_root)

    assert policy.can_access("04_finanz", "/04_Finanz", "write")
    assert not policy.can_access("04_finanz", "/01_Info", "read")


def test_display_names_keep_original_case(tmp_path):
    from core.acl import ACLPolicy

    project_root = tmp_path / "Project"
    project_root.mkdir()
    _write_templates(project_root, "Standard", ["04_Finanz"])
    _write_project_config(project_root, "Standard")
    (project_root / META_DIR / "ACLs.md").write_text(
        "# Permissions\n\n## Buchhaltung\n- /04_Finanz/: read\n\n# Users\nAnna: Buchhaltung\n"
    )

    policy = ACLPolicy.from_project(project_root)

    assert policy.display_name("anna") == "Anna"
    assert policy.display_name("buchhaltung") == "Buchhaltung"
    assert policy.display_name("04_finanz") == "04_Finanz"
    assert policy.display_name("unknown") == "unknown"


# --- Nearest rule per role wins (rights can be taken away in sub-folders) ---

def _nearest_policy():
    from core.acl import ACLPolicy, PermissionRule

    return ACLPolicy(
        roles={"team", "gl", "admin", "reader"},
        permissions={
            "team": [
                PermissionRule(path="/07_Arbeit", rights={"read", "write"}),
                PermissionRule(path="/07_Arbeit/Vertraulich", rights={"none"}),
            ],
            "gl": [PermissionRule(path="/07_Arbeit/Vertraulich", rights={"read", "write"})],
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "reader": [
                PermissionRule(path="/Archiv", rights={"read", "write"}),
                PermissionRule(path="/Archiv/Alt", rights={"read"}),
                PermissionRule(path="/Docs/**", rights={"read"}),
                PermissionRule(path="/Docs", rights={"write"}),
            ],
        },
        users={"anna": {"team"}, "karl": {"team", "gl"}},
    )


NEAREST_CHECKS = [
    # none at a sub-folder locks the role out there, the rest of the parent stays open
    ("team", "/07_Arbeit/Vertraulich", "read", False),
    ("team", "/07_Arbeit/Vertraulich/plan.md", "write", False),
    ("team", "/07_Arbeit/Projekt", "write", True),
    # roles not named at the sub-folder are unaffected
    ("gl", "/07_Arbeit/Vertraulich", "write", True),
    ("admin", "/07_Arbeit/Vertraulich", "read", True),
    # a deeper rule with fewer rights replaces the inherited ones
    ("reader", "/Archiv/Alt/x", "write", False),
    ("reader", "/Archiv/Alt/x", "read", True),
    ("reader", "/Archiv/Neu", "write", True),
    # rules written for the same folder (/Docs and /Docs/**) are combined
    ("reader", "/Docs/a", "read", True),
    ("reader", "/Docs/a", "write", True),
]


@pytest.mark.parametrize("role,path,right,expected", NEAREST_CHECKS)
def test_nearest_rule_per_role_wins(role, path, right, expected):
    assert _nearest_policy().can_access(role, path, right) is expected


def test_user_rights_are_the_union_of_their_roles():
    from core.acl import ACLAuthorizer

    authorizer = ACLAuthorizer(_nearest_policy(), backend="legacy")

    assert not authorizer.can_user_access("anna", "/07_Arbeit/Vertraulich", "read")
    assert authorizer.can_user_access("karl", "/07_Arbeit/Vertraulich", "read")


def test_nearest_rule_casbin_parity_if_installed():
    import core.acl as acl_module
    from core.acl import ACLAuthorizer

    if acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")

    casbin_auth = ACLAuthorizer(_nearest_policy(), backend="casbin")
    assert casbin_auth.backend == "casbin"
    for role, path, right, expected in NEAREST_CHECKS:
        assert casbin_auth.can_access(role, path, right) is expected, (role, path, right)
    assert not casbin_auth.can_user_access("anna", "/07_Arbeit/Vertraulich", "read")
    assert casbin_auth.can_user_access("karl", "/07_Arbeit/Vertraulich", "read")
