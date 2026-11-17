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
    from Headline.model import HeadlineModel

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
