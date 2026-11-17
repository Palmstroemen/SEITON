"""What the Headline shows, worked out once (Headline/model.py; Scope/Designdocument Headline.md,
3): where one is, the standard folders there, the path to climb. No Qt; the line and the panel
only draw it."""

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
    (standard / "01_Info").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio")
    (studio / "01_Info").mkdir()  # born: there for real
    return {"root": root.resolve(), "studio": studio.resolve(),
            "reisen": _project(root / "Reisen").resolve()}


def _model(start: Path):
    from core.scope_api import ScopeApi
    from daemon.lens_link import LensLink
    from Headline.model import HeadlineModel

    api = ScopeApi(str(start))
    return HeadlineModel(api, LensLink(api, start_daemon=False), str(start))


def test_it_shows_where_one_is(world):
    view = _model(world["studio"]).view()
    assert view["cwd"] == str(world["studio"])
    assert view["name"] == "Musikstudio"
    assert view["projectsRoot"] == str(world["root"])


def test_the_standard_folders_with_suggestions_pale(world):
    folders = {f["name"]: f for f in _model(world["studio"]).view()["folders"]}
    assert set(folders) == {"01_Info", "04_Finanz"}
    assert folders["01_Info"]["embryo"] is False  # born
    assert folders["04_Finanz"]["embryo"] is True  # only suggested
    assert folders["04_Finanz"]["path"] == str(world["studio"] / "04_Finanz")


def test_going_somewhere_moves_the_session(world):
    model = _model(world["studio"])
    assert model.go(str(world["reisen"]))
    assert model.view()["cwd"] == str(world["reisen"])
    assert model.lens("state")["cwd"] == str(world["reisen"])


def test_going_nowhere_is_refused(world):
    model = _model(world["studio"])
    assert not model.go(str(world["studio"] / "gibt-es-nicht"))
    assert model.view()["cwd"] == str(world["studio"])


def test_the_path_to_climb_runs_from_the_projects_root_down(world):
    model = _model(world["studio"])
    model.go(str(world["studio"] / "01_Info"))
    assert [step["name"] for step in model.climb()] == ["Projekte", "Musikstudio", "01_Info"]
    assert model.climb()[0]["path"] == str(world["root"])


def test_with_the_lens_on_it_shows_the_lens_folder(world):
    model = _model(world["studio"])
    on = model.lens("look_at", {"path": str(world["studio"] / "04_Finanz")})
    assert on["active"]
    view = model.view()
    assert view["lens"]["active"] and view["lens"]["projectDir"] == str(world["studio"])
    assert {f["name"] for f in view["folders"]} == {"Ausgaben"}  # the lens' folder's own
    assert view["cwd"] == str(world["studio"])  # the CWD stays (A3)


class _FakeLink:
    """A session another program moved: follow() tells where it went."""

    def __init__(self, went=None):
        self.went = went
        self.calls = []
        self.projects_root = None

    def call(self, method, params=None):
        self.calls.append((method, params))
        return {"ok": True, "result": {"cwd": (params or {}).get("path", ""), "active": False}}

    def follow(self):
        return self.went

    def update_context(self, path):
        pass


def test_it_follows_where_scope_or_suntree_went(world):
    from core.scope_api import ScopeApi
    from Headline.model import HeadlineModel

    link = _FakeLink(went=str(world["reisen"]))
    model = HeadlineModel(ScopeApi(str(world["studio"])), link, str(world["studio"]))
    assert model.follow()
    assert model.view()["cwd"] == str(world["reisen"])


def test_nothing_to_follow(world):
    from core.scope_api import ScopeApi
    from Headline.model import HeadlineModel

    model = HeadlineModel(ScopeApi(str(world["studio"])), _FakeLink(went=None), str(world["studio"]))
    assert not model.follow()
    assert model.view()["cwd"] == str(world["studio"])


def test_a_step_of_the_cascade_shows_its_folders(world):
    model = _model(world["studio"])
    names = [f["name"] for f in model.children(str(world["root"]))]
    assert names == ["Musikstudio", "Reisen"]  # sorted, the projects of the level
    assert all(f["project"] for f in model.children(str(world["root"])))
    assert [f["name"] for f in model.children(str(world["studio"]))] == ["01_Info"]  # no hidden .seiton


# --- the perspectives of the root (Designdocument Perspective Resolver MVP.md, A11) ----------

def _perspectives(world, text):
    (world["root"] / META_DIR / "Perspectives.md").write_text(text)


def test_no_list_no_perspectives(world):
    assert _model(world["studio"]).perspectives() == []


def test_the_roots_perspectives_named_as_their_folder(world):
    _perspectives(world, "# Perspectives\n04_Finanz\n9_Dokumentation/92_Bilder\n\n")
    shown = _model(world["studio"]).perspectives()
    assert [(p["name"], p["lens"]) for p in shown] == [
        ("04_Finanz", ["04_Finanz"]), ("92_Bilder", ["9_Dokumentation", "92_Bilder"])]
    assert not any(p["active"] for p in shown)


def test_two_of_the_same_name_get_a_part_of_their_path(world):
    _perspectives(world, "# Perspectives\n04_Finanz/Bilder\n9_Dokumentation/Bilder\n")
    assert [p["name"] for p in _model(world["studio"]).perspectives()] == [
        "Bilder (04_Finanz)", "Bilder (9_Dokumentation)"]


def test_no_way_out_of_the_root(world):
    _perspectives(world, "# Perspectives\n../Fremd\n/etc\n04_Finanz\n")
    assert [p["name"] for p in _model(world["studio"]).perspectives()] == ["04_Finanz"]


def test_a_perspective_puts_the_lens_on_and_off(world):
    _perspectives(world, "# Perspectives\n04_Finanz\n")
    model = _model(world["studio"])
    assert model.wear(["04_Finanz"])
    assert model.perspectives()[0]["active"]
    assert model.view()["lens"]["active"]
    assert model.wear(["04_Finanz"])  # the active one again: off
    assert not model.perspectives()[0]["active"] and not model.view()["lens"]["active"]


# --- the active project, for whoever wants it (the clock; Designdocument Headline.md, 3a) ----

def _reporting(world, start):
    from core.scope_api import ScopeApi
    from daemon.lens_link import LensLink
    from Headline.model import HeadlineModel

    told = []
    api = ScopeApi(str(start))
    model = HeadlineModel(api, LensLink(api, start_daemon=False), str(start),
                          report=lambda project, person: told.append((project, person)))
    return model, told


def test_it_tells_the_active_project_at_the_start_and_on_every_change(world):
    model, told = _reporting(world, world["studio"] / "01_Info")
    assert told[-1][0] == str(world["studio"])  # the project, not the folder in it
    assert told[-1][1]  # and who works in it
    model.go(str(world["reisen"]))
    assert told[-1][0] == str(world["reisen"])


def test_a_folder_in_the_same_project_tells_nothing_new(world):
    model, told = _reporting(world, world["studio"])
    before = len(told)
    model.go(str(world["studio"] / "01_Info"))
    assert len(told) == before


def test_outside_a_project_no_project(world):
    model, told = _reporting(world, world["studio"])
    model.go(str(world["root"]))  # the projects root holds projects, it is none
    assert told[-1][0] is None


# --- badges in the dropdowns: the P of projects, a folder's own badge (2026-11-17) -------------

def test_the_way_up_knows_its_projects(world):
    model = _model(world["studio"])
    model.go(str(world["studio"] / "01_Info"))
    steps = {s["name"]: s for s in model.climb()}
    assert steps["Musikstudio"]["project"] and not steps["01_Info"]["project"]
    assert "batch" in steps["01_Info"] and "batchText" in steps["01_Info"]


def test_the_cascade_carries_the_badges(world):
    (world["studio"] / "04_Finanz").mkdir()
    (world["studio"] / "04_Finanz" / ".seiton").mkdir()
    (world["studio"] / "04_Finanz" / ".seiton" / "batch.md").write_text("€\n")
    model = _model(world["studio"])
    entry = {c["name"]: c for c in model.children(str(world["studio"]))}["04_Finanz"]
    assert entry["batchText"] == "€" and entry["batch"] == ""
