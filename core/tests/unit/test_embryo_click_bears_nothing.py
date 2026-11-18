"""A click alone bears no embryo (decided 2026-11-17): only a drop onto it, or making something
in it (a right click: new note, new folder), brings a suggested folder into being. Going there,
looking at it, putting the lens on it - everything a click or a double click does in Scope,
SunTree or the Headline - leaves the disk as it was."""

from pathlib import Path

import pytest

from core.brand import META_DIR, env_name


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# SEITON Project\n")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv(env_name("SCOPE_START_DAEMON"), "0")
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    standard = tmp_path / META_DIR / "Templates" / "Standard"
    (standard / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio")
    return {"root": root.resolve(), "studio": studio.resolve(),
            "embryo": studio.resolve() / "04_Finanz", "deeper": studio.resolve() / "04_Finanz" / "Ausgaben"}


def _session(world):
    from core.scope_api import ScopeApi
    from daemon.lens_link import LensLink

    api = ScopeApi(str(world["studio"]))
    return api, LensLink(api, start_daemon=False)


def test_the_embryo_is_one(world):
    from core.scope_api import ScopeApi

    names = {e["name"]: e for e in ScopeApi(str(world["studio"])).list_templates(str(world["studio"]), True)}
    assert names["04_Finanz"]["isEmbryo"] and not world["embryo"].exists()


@pytest.mark.parametrize("place", ["embryo", "deeper"])
def test_going_and_looking_there_bears_nothing(world, place):
    api, link = _session(world)
    target = str(world[place])
    link.call("set_cwd", {"path": target})
    link.update_context(target)
    api.update_context(target)
    api.list_entries(target)
    api.list_entries_quick(target)
    api.list_children(target, True)
    api.list_templates(target, True)
    assert not world["embryo"].exists()


@pytest.mark.parametrize("place", ["embryo", "deeper"])
def test_putting_the_lens_on_bears_nothing(world, place):
    _api, link = _session(world)
    link.call("look_at", {"path": str(world[place])})
    link.call("state", {})
    link.call("listing", {})
    link.call("take_off", {})
    assert not world["embryo"].exists()


def test_the_headline_going_to_an_embryo_bears_nothing(world):
    from apps.Headline.model import HeadlineModel

    api, link = _session(world)
    model = HeadlineModel(api, link, str(world["studio"]))
    assert not model.go(str(world["embryo"]))  # not there: refused, not made
    model.view()
    model.children(str(world["embryo"]))
    assert not world["embryo"].exists()


def test_a_drop_does_bear_it(world, tmp_path):
    from core.scope_api import ScopeApi

    note = tmp_path / "Rechnung.md"
    note.write_text("x")
    assert ScopeApi(str(world["studio"])).move_entry(str(note), str(world["embryo"]))
    assert (world["embryo"] / "Rechnung.md").exists()


def test_without_suggestions_the_born_folders_stay(tmp_path, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", API7: switching off the pale suggestions hid the real ones too."""
    from core.scope_api import ScopeApi

    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    standard = tmp_path / META_DIR / "Templates" / "Standard"
    for name in ("04_Finanz", "05_Recht"):
        (standard / name).mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    (root / "04_Finanz").mkdir()
    (root / "04_Finanz" / "Rechnung.pdf").write_text("x")
    api = ScopeApi(str(root))
    with_them = {e["name"]: e["isEmbryo"] for e in api.list_templates(str(root), True)}
    without = {e["name"]: e["isEmbryo"] for e in api.list_templates(str(root), False)}
    assert with_them == {"04_Finanz": False, "05_Recht": True}
    assert without == {"04_Finanz": False}


def test_the_listing_shows_the_suggestions_of_the_listed_folders_project(tmp_path, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", API8: they came from the project Scope stood in."""
    from core.scope_api import ScopeApi

    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    standard = tmp_path / META_DIR / "Templates" / "Standard"
    (standard / "04_Finanz").mkdir(parents=True)
    other = tmp_path / META_DIR / "Templates" / "Musik"
    (other / "Aufnahmen").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Studio")
    (studio / META_DIR / "Templates.md").write_text("# Templates\nMusik\n")
    api = ScopeApi(str(root))  # Scope stands in the parent project
    names = {e["name"] for e in api.list_entries(str(studio)) if e.get("isEmbryo")}
    assert names == {"Aufnahmen"}


def test_a_refused_drop_on_a_suggestion_leaves_no_empty_folder(world):
    """"docs/Prüfung 2026-11-18.md", API10."""
    from core.scope_api import ScopeApi

    api = ScopeApi(str(world["studio"]))
    report = api.move_entries([str(world["studio"] / "fehlt.pdf")], str(world["embryo"]))
    assert not report["moved"]
    assert not world["embryo"].exists()  # still a suggestion
    assert not api.move_entry(str(world["studio"] / "fehlt.pdf"), str(world["embryo"]))
    assert not world["embryo"].exists()


def test_a_project_icon_belongs_to_its_project(tmp_path, monkeypatch):
    """"docs/Prüfung 2026-11-18.md", D9: not inherited, and kept with inherit: not."""
    from core.scope_api import ScopeApi

    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Desk.md").write_text("# Desk\nProjectIcon: 🏠\nThemePreset: Mint-Y\n")
    sub = _project(root / "Garten")
    own = _project(root / "Werkstatt")
    (own / META_DIR / "Desk.md").write_text("# Desk\ninherit: not\nProjectIcon: 🔧\n")
    api = ScopeApi(str(root))
    assert api.get_project_icon(str(root)) == "🏠"
    assert api.get_project_icon(str(sub)) is None
    assert api.get_project_icon(str(own)) == "🔧"
