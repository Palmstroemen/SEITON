"""ScopeApi and filing by date (core/filing.py): catching up when a folder is looked at,
after moves, across a project; the preview when moving; enabling sorting in a folder."""

from pathlib import Path

import pytest

from core.scope_api import ScopeApi
from core.brand import META_DIR, env_name


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    for key in (env_name("TEMPLATES_DIR"), env_name("ACL_MODE"), env_name("ACL_USER")):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


RULE = "# Sort\nPattern: {{YYYY}}/{{MM}}\nDateSource: filename\nNewLevelFrom: 2\n"


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "Projekt"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# MyOS Project\n")
    folder = root / "Rechnungen"
    (folder / META_DIR).mkdir(parents=True)
    (folder / META_DIR / "Sort.md").write_text(RULE)
    return root


def _put(folder: Path, *names: str) -> None:
    for name in names:
        (folder / name).write_text(name)


def test_looking_at_a_sorted_folder_files_what_is_due(project):
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf", "c 2025-01-01.pdf")

    names = {e["name"] for e in ScopeApi(str(project)).list_entries(str(folder))}

    assert {"2024", "2025"} <= names and "a 2024-01-01.pdf" not in names
    assert (folder / "2024" / "a 2024-01-01.pdf").exists()


def test_a_moved_file_is_filed_and_reported(project, tmp_path):
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf")
    incoming = project / "c 2025-01-01.pdf"
    incoming.write_text("c")
    api = ScopeApi(str(project))

    preview = api.preview_sort_target_for_move(str(incoming), str(folder))
    result = api.move_entries([str(incoming)], str(folder))

    assert preview == {"ok": True, "reason": "filed", "target": str((folder / "2025").resolve())}
    assert (folder / "2025" / "c 2025-01-01.pdf").exists()
    assert result["sorted"][0]["destination"].endswith("Rechnungen/2025/c 2025-01-01.pdf")


def test_without_a_level_to_go_to_the_preview_says_nothing(project):
    incoming = project / "a 2024-01-01.pdf"
    incoming.write_text("a")

    preview = ScopeApi(str(project)).preview_sort_target_for_move(str(incoming), str(project / "Rechnungen"))

    assert preview["ok"] is False


def test_catching_up_across_the_project(project):
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf", "c 2025-01-01.pdf")

    report = ScopeApi(str(project)).catch_up_filing_all(str(project / "Rechnungen"))

    assert len(report["moved"]) == 3 and report["ok"]


def test_enabling_sorting_puts_a_rule_into_the_folder(project):
    fotos = project / "Fotos"
    fotos.mkdir()
    api = ScopeApi(str(project))

    result = api.enable_sorting(str(fotos))

    assert result["ok"] and (fotos / META_DIR / "Sort.md").read_text().startswith("# Sort\nPattern: {{YYYY}}/{{MM}}\n")
    assert api.enable_sorting(str(fotos))["reason"] == "exists"
    assert api.enable_sorting(str(project.parent))["reason"] == "no_project"


def test_a_rule_that_cannot_be_written_is_reported_not_raised(project):
    import os
    fotos = project / "Fotos"
    fotos.mkdir()
    fotos.chmod(0o555)  # the file system says no (no ACL here)
    try:
        if os.access(fotos, os.W_OK):
            pytest.skip("running as root")
        assert ScopeApi(str(project)).enable_sorting(str(fotos))["reason"] == "failed"
    finally:
        fotos.chmod(0o755)


@pytest.fixture
def few(tmp_path):
    """A sorted folder with few files: they stay loose, shown in virtual folders."""
    root = tmp_path / "Projekt"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# MyOS Project\n")
    folder = root / "Rechnungen"
    (folder / META_DIR).mkdir(parents=True)
    (folder / META_DIR / "Sort.md").write_text("# Sort\nPattern: {{YYYY}}/{{MM}}\nDateSource: filename\nNewLevelFrom: 10\n")
    _put(folder, "a 2024-01-01.pdf", "b 2024-03-01.pdf", "c 2025-01-01.pdf", "ohne Datum.pdf")
    return folder


def test_loose_files_are_shown_in_virtual_folders(few):
    entries = {e["name"]: e for e in ScopeApi(str(few.parent)).list_entries(str(few))}

    assert entries["2024"]["isVirtual"] is True and entries["2024"]["isDir"] is True
    assert entries["2024"]["path"] == str(few / "2024")
    assert "a 2024-01-01.pdf" not in entries and "ohne Datum.pdf" in entries
    assert not (few / "2024").exists()  # nothing moved


def test_inside_virtual_folders(few):
    api = ScopeApi(str(few.parent))

    year = {e["name"]: e for e in api.list_entries(str(few / "2024"))}
    month = api.list_entries(str(few / "2024" / "03"))

    assert sorted(year) == ["01", "03"] and year["03"]["isVirtual"] is True
    assert [(e["name"], e["path"]) for e in month] == [("b 2024-03-01.pdf", str(few / "b 2024-03-01.pdf"))]


def test_xray_sees_through_small_virtual_folders(few):
    entries = ScopeApi(str(few.parent)).list_entries_xray(str(few), 10, True)

    names = sorted(e["name"] for e in entries if not e["name"].startswith("."))
    assert names == ["a 2024-01-01.pdf", "b 2024-03-01.pdf", "c 2025-01-01.pdf", "ohne Datum.pdf"]
    assert not any(e.get("xrayVia") or e.get("isVirtual") for e in entries)


def test_the_quick_listing_shows_the_same_virtual_folders(few):
    api = ScopeApi(str(few.parent))

    quick = sorted(e["name"] for e in api.list_entries_quick(str(few)))
    inside = [e["name"] for e in api.list_entries_quick(str(few / "2024" / "03"))]

    assert quick == ["2024", "2025", "ohne Datum.pdf"] and inside == ["b 2024-03-01.pdf"]


def test_a_new_note_in_a_sorted_folder_opens_where_it_is_filed(project):
    """Filed at once, not on the next look: an editor opened on the old place would lose
    everything typed into it ("docs/Prüfung 2026-11-18.md", X2)."""
    folder = project / "Rechnungen"
    (folder / META_DIR / "Sort.md").write_text(RULE.replace("DateSource: filename", "DateSource: modified"))
    _put(folder, "a.pdf", "b.pdf", "c.pdf")  # more than NewLevelFrom: the year folder is real
    api = ScopeApi(str(project))
    api.catch_up_filing(str(folder))

    created = Path(api.create_note(str(folder), "Protokoll"))

    assert created.exists() and created.parent != folder
    assert created.name == "Protokoll.md" and folder in created.parents
    assert not (folder / "Protokoll.md").exists()
    api.catch_up_filing(str(folder))
    assert created.exists()  # filed once, stays there


def test_a_folder_that_cannot_take_the_file_skips_it_and_the_rest_goes_on(project):
    """"docs/Prüfung 2026-11-18.md", API3: one failure emptied the listing and stopped filing."""
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf", "c 2025-01-01.pdf")
    (folder / "2024").mkdir()
    (folder / "2024").chmod(0o555)  # the year folder takes nothing
    try:
        names = {e["name"] for e in ScopeApi(str(project)).list_entries(str(folder))}
        assert "a 2024-01-01.pdf" in names and "b 2024-02-01.pdf" in names  # stayed, shown
        assert (folder / "2025" / "c 2025-01-01.pdf").exists()  # the rest was filed
    finally:
        (folder / "2024").chmod(0o755)
