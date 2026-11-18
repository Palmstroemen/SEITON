"""A project becomes an ordinary folder again (crossed-out P-Button).

What creating the project wrote is remembered (.MyOS/.created.json); without anything of
its own since, .MyOS is simply removed. Settings of its own (changed rights, tags, a
trash, ...) are not lost: .MyOS goes into the parent project's trash as "MyOS settings".
Not possible for the top project and outside the projects tree; subprojects stay."""

from pathlib import Path

import pytest

from core import trash
from core.project import ProjectConfig, ProjectFinder
from core.project_unmake import ProjectHasOwnSettings, can_unmake, own_settings, unmake_project
from core.brand import META_DIR, NAME, env_name, project_heading


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    monkeypatch.setenv(env_name("ACL_USER"), "oliver")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


@pytest.fixture
def tree(tmp_path):
    template = tmp_path / META_DIR / "Templates" / "Standard"
    (template / META_DIR).mkdir(parents=True)
    (template / "04_Finanz").mkdir()
    (template / META_DIR / "ACLs.md").write_text("# Permissions\n\n## Buchhaltung\n- /04_Finanz/: read, write\n")
    (template / META_DIR / "Desk.md").write_text("# Desk\nPanelTheme: Mint-Y-Blue\n")
    projects = tmp_path / "Projekte"
    (projects / META_DIR).mkdir(parents=True)
    (projects / META_DIR / "Project.md").write_text("# MyOS Project\n")
    (projects / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    (projects / META_DIR / "ACLs.md").write_text(
        f"# Permissions\n\n## Admin\n- /*: read, write, execute\n- /{META_DIR}/ACLs.md: read, write, change\n\n"
        "# Users\nOliver: Admin\nAnna: Buchhaltung\n")
    kunde = projects / "Kunde"
    (kunde / "Rechnungen").mkdir(parents=True)
    (kunde / "Rechnungen" / "r1.pdf").write_text("pdf\n")
    assert ProjectConfig.make_project(kunde)
    return {"projects": projects, "kunde": kunde, "tmp": tmp_path}


def test_a_fresh_project_becomes_a_folder_again(tree):
    kunde = tree["kunde"]
    (kunde / META_DIR / ".TagsHere.json").write_text("{}")  # a cache, not a setting

    assert can_unmake(kunde)
    assert own_settings(kunde) == []
    unmake_project(kunde, "oliver")

    assert not (kunde / META_DIR).exists()
    assert (kunde / "Rechnungen" / "r1.pdf").read_text() == "pdf\n"


def test_settings_of_its_own_are_named_and_not_removed_without_consent(tree):
    kunde = tree["kunde"]
    acls = kunde / META_DIR / "ACLs.md"
    acls.write_text(acls.read_text() + "Karl: Admin\n")
    (kunde / META_DIR / "Tags.md").write_text("# Tags\nwichtig\n")
    (kunde / META_DIR / "ACLs-history").mkdir()
    (kunde / META_DIR / "ACLs-history" / "alt.md").write_text("alt\n")
    (kunde / META_DIR / "Trash" / "files").mkdir(parents=True)  # empty trash: nothing of its own

    assert own_settings(kunde) == ["ACLs-history", "ACLs.md", "Tags.md"]
    with pytest.raises(ProjectHasOwnSettings):
        unmake_project(kunde, "oliver")
    assert (kunde / META_DIR / "Tags.md").exists()


def test_with_consent_they_go_into_the_parents_trash(tree):
    kunde = tree["kunde"]
    (kunde / META_DIR / "Tags.md").write_text("# Tags\nwichtig\n")

    unmake_project(kunde, "oliver", keep_own=True)

    assert not (kunde / META_DIR).exists()
    entries = trash.list_trash(tree["projects"])
    assert [(e.original, e.is_dir, e.deleted_by) for e in entries] == [(f"Kunde/{NAME} settings", True, "oliver")]
    restored = trash.restore(tree["projects"], entries[0].name)
    # Back as its .seiton: the folder is a project again, with its settings (P7).
    assert restored == kunde / META_DIR
    assert (restored / "Tags.md").read_text() == "# Tags\nwichtig\n"
    assert ProjectFinder.is_project(kunde)


def test_settings_of_a_folder_that_is_a_project_again_come_back_beside_it(tree):
    kunde = tree["kunde"]
    (kunde / META_DIR / "Tags.md").write_text("# Tags\nwichtig\n")
    unmake_project(kunde, "oliver", keep_own=True)
    assert ProjectConfig.make_project(kunde)  # made a project anew meanwhile

    entry = trash.list_trash(tree["projects"])[0]
    restored = trash.restore(tree["projects"], entry.name)

    assert restored == kunde / f"{NAME} settings"  # never over the new settings


def test_subprojects_stay_projects(tree):
    sub = tree["kunde"] / "Teilprojekt"
    assert ProjectConfig.make_project(sub)

    unmake_project(tree["kunde"], "oliver")

    assert (sub / META_DIR / "Project.md").exists()


def test_projects_made_before_count_everything_but_the_marker_as_their_own(tree):
    old = tree["projects"] / "Alt"
    (old / META_DIR).mkdir(parents=True)
    (old / META_DIR / "Project.md").write_text("---\nwindow_x: 10\n---\n# MyOS Project\n")
    assert own_settings(old) == []
    (old / META_DIR / "Desk.md").write_text("# Desk\n")
    assert own_settings(old) == ["Desk.md"]


def test_the_marker_under_the_current_name_is_not_their_own(tree):
    new = tree["projects"] / "Neu"
    (new / META_DIR).mkdir(parents=True)
    (new / META_DIR / "Project.md").write_text(f"---\nwindow_x: 10\n---\n{project_heading()}\n")
    assert own_settings(new) == []


def test_what_cannot_be_turned_back(tree):
    assert not can_unmake(tree["projects"])                       # the top project
    assert not can_unmake(tree["kunde"] / "Rechnungen")           # no project
    assert not can_unmake(tree["tmp"] / META_DIR / "Templates" / "Standard")  # a template
    with pytest.raises(ValueError):
        unmake_project(tree["projects"], "oliver")
    assert (tree["projects"] / META_DIR / "Project.md").exists()


def _folder_with_settings(projects: Path) -> Path:
    """A folder that has settings of its own before it becomes a project (tags, a sort rule)."""
    folder = projects / "Archiv"
    (folder / META_DIR).mkdir(parents=True)
    (folder / META_DIR / "myTags.md").write_text("# Tags\nwichtig\n")
    (folder / META_DIR / "Sort.md").write_text("# Sort\nPattern: {{YYYY}}\n")
    (folder / "Brief.md").write_text("Brief\n")
    return folder


def test_turning_back_leaves_what_was_there_before(tree):
    """"docs/Prüfung 2026-11-18.md", P1: the folder's own settings were lost."""
    folder = _folder_with_settings(tree["projects"])
    assert ProjectConfig.make_project(folder)
    assert own_settings(folder) == []  # what was there before is not the project's

    unmake_project(folder, user="oliver")

    assert not (folder / META_DIR / "Project.md").exists()
    assert sorted(p.name for p in (folder / META_DIR).iterdir()) == ["Sort.md", "myTags.md"]
    assert (folder / META_DIR / "myTags.md").read_text() == "# Tags\nwichtig\n"


def test_restored_settings_join_what_stayed_in_its_seiton(tree):
    folder = _folder_with_settings(tree["projects"])
    assert ProjectConfig.make_project(folder)
    (folder / META_DIR / "Tags.md").write_text("# Tags\neigen\n")
    unmake_project(folder, "oliver", keep_own=True)
    assert not ProjectFinder.is_project(folder) and (folder / META_DIR / "myTags.md").exists()

    entry = trash.list_trash(tree["projects"])[0]
    restored = trash.restore(tree["projects"], entry.name)

    assert restored == folder / META_DIR and ProjectFinder.is_project(folder)
    assert (restored / "Tags.md").exists() and (restored / "myTags.md").exists()


def test_with_consent_only_the_projects_own_go_into_the_trash(tree):
    folder = _folder_with_settings(tree["projects"])
    assert ProjectConfig.make_project(folder)
    (folder / META_DIR / "ACLs.md").write_text("# Permissions\n\n## Neu\n- /*: read\n")
    assert own_settings(folder) == ["ACLs.md"]

    unmake_project(folder, user="oliver", keep_own=True)

    assert sorted(p.name for p in (folder / META_DIR).iterdir()) == ["Sort.md", "myTags.md"]
    entries = trash.list_trash(tree["projects"])
    assert [e.original for e in entries] == [f"Archiv/{NAME} settings"]
    restored = trash.restore(tree["projects"], entries[0].name)
    # Back in its .seiton, beside the folder's settings from before (P7).
    assert restored == folder / META_DIR
    assert sorted(p.name for p in restored.iterdir()) == sorted(
        ["ACLs.md", "Project.md", ".created.json", "Desk.md", "Sort.md", "myTags.md"])
