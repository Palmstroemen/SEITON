"""What the Headline shows, worked out once (apps/Headline/model.py; apps/Scope/Designdocument Headline.md,
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
    from apps.Headline.model import HeadlineModel

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
    below = [step for step in model.climb() if not step["above"]]
    assert [step["name"] for step in below] == ["Projekte", "Musikstudio", "01_Info"]
    assert below[0]["path"] == str(world["root"])


def test_the_way_up_goes_on_above_the_projects_root(world):
    """One could not leave the projects root, into /home say (2026-11-18): the folders above it
    come first, marked as above (outside SEITON's projects)."""
    model = _model(world["studio"])
    steps = model.climb()
    assert steps[0]["path"] == "/" and steps[0]["above"]
    above = [Path(step["path"]) for step in steps if step["above"]]
    assert above == list(reversed(world["root"].parents))
    assert model.go(str(world["root"].parent))  # and one may go there


def test_the_way_up_and_the_cascade_carry_the_project_colours(world):
    (world["studio"] / META_DIR / "Color.md").write_text("#445566\n")
    model = _model(world["studio"])
    model.go(str(world["studio"] / "01_Info"))
    steps = {s["name"]: s for s in model.climb()}
    assert steps["Musikstudio"]["color"] == "#445566" and steps["01_Info"]["color"] == ""
    rows = {r["name"]: r for r in model.children(str(world["root"]))}
    assert rows["Musikstudio"]["color"] == "#445566"


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
    from apps.Headline.model import HeadlineModel

    link = _FakeLink(went=str(world["reisen"]))
    model = HeadlineModel(ScopeApi(str(world["studio"])), link, str(world["studio"]))
    assert model.follow()
    assert model.view()["cwd"] == str(world["reisen"])


def test_nothing_to_follow(world):
    from core.scope_api import ScopeApi
    from apps.Headline.model import HeadlineModel

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
    from apps.Headline.model import HeadlineModel

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


class _LensLink(_FakeLink):
    """A session where another program puts the lens on or takes it off: the place stays."""

    def __init__(self):
        super().__init__(went=None)
        self.lens_state = {"active": False}
        self.last_state = {}

    def call(self, method, params=None):
        self.calls.append((method, params))
        result = dict(self.lens_state, cwd=(params or {}).get("path", ""))
        if method == "state":
            self.last_state = result
        return {"ok": True, "result": result}

    def follow(self):
        self.call("state")
        return None


def test_it_follows_a_lens_put_on_or_off_elsewhere(world):
    # H1 (review 2026-11-18): Scope or SunTree changed the lens; the CWD stayed, so the line
    # kept the old folders and the clock counted on the old project.
    from core.scope_api import ScopeApi
    from apps.Headline.model import HeadlineModel

    told = []
    link = _LensLink()
    model = HeadlineModel(ScopeApi(str(world["studio"])), link, str(world["studio"]),
                          report=lambda project, person: told.append(project))
    assert not model.follow()
    link.lens_state = {"active": True, "project_dir": str(world["reisen"]),
                       "target": str(world["reisen"] / "04_Finanz"), "lens": ["04_Finanz"]}
    assert model.follow()
    assert told[-1] == str(world["reisen"])
    states = sum(1 for method, _p in link.calls if method == "state")
    assert not model.follow()  # seen: nothing new
    assert sum(1 for method, _p in link.calls if method == "state") - states == 1  # one request a beat
    link.lens_state = {"active": False}
    assert model.follow()
    assert told[-1] == str(world["studio"])


def test_the_real_link_keeps_the_state_it_was_told(world):
    model = _model(world["studio"])
    model.lens("look_at", {"path": str(world["studio"] / "04_Finanz")})
    model.follow()
    assert model._link.last_state["active"] and model._link.last_state["project_dir"] == str(world["studio"])


# --- dropping onto a folder (review 2026-11-18, H9) ------------------------------------------

@pytest.mark.parametrize("payload, paths", [
    ("/p/a.pdf", ["/p/a.pdf"]),
    ("file:///p/Neue%20Rechnung.pdf", ["/p/Neue Rechnung.pdf"]),                # one URL from Nemo
    ("file:///p/a.pdf\r\nfile:///p/b.pdf\r\n", ["/p/a.pdf", "/p/b.pdf"]),       # text/uri-list
    ("# comment\nfile:///p/a.pdf", ["/p/a.pdf"]),
    ('__SCOPE_PATHS__["/p/a.pdf", "file:///p/b%C3%BC.pdf"]', ["/p/a.pdf", "/p/bü.pdf"]),  # Scope's
    ("", []), ("__SCOPE_PATHS__[broken", []), ("relative/path", []), ("http://x/a.pdf", []),
])
def test_what_a_drop_brings(payload, paths):
    from apps.Headline.model import sources_of
    assert sources_of(payload) == paths


def test_a_file_dropped_onto_a_suggested_folder_bears_it(world):
    note = world["studio"] / "Rechnung.pdf"
    note.write_text("r")
    model = _model(world["studio"])
    target = world["studio"] / "04_Finanz"  # an embryo
    plan = model.plan_drop(f"file://{note}", str(target))
    assert plan == {"sources": [str(note)], "folders": 0, "target": str(target)}
    result = model.move(plan["sources"], plan["target"])
    assert result == {"moved": 1, "failed": []}
    assert (target / "Rechnung.pdf").is_file() and not note.exists()
    assert {f["name"]: f["embryo"] for f in model.view()["folders"]}["04_Finanz"] is False  # born


def test_folders_in_a_drop_are_counted_to_be_asked_about(world):
    folder = world["studio"] / "Alte Sachen"
    folder.mkdir()
    plan = _model(world["studio"]).plan_drop(str(folder), str(world["studio"] / "01_Info"))
    assert plan["folders"] == 1


def test_what_could_not_be_moved_is_named(world):
    model = _model(world["studio"])
    result = model.move([str(world["studio"] / "gibt es nicht.pdf")], str(world["studio"] / "01_Info"))
    assert result == {"moved": 0, "failed": ["gibt es nicht.pdf"]}


def test_rows_say_whether_folders_lie_below(world):
    """In the dropdowns one sees where the tree ends (2026-11-18)."""
    (world["studio"] / "01_Info" / "Archiv").mkdir()
    (world["studio"] / "02_Leer").mkdir()
    (world["studio"] / "02_Leer" / ".versteckt").mkdir()  # hidden folders do not count
    (world["studio"] / "02_Leer" / "notiz.md").write_text("x")  # nor files
    model = _model(world["studio"])
    rows = {r["name"]: r for r in model.children(str(world["studio"]))}
    assert rows["01_Info"]["leaf"] is False and rows["02_Leer"]["leaf"] is True
    model.go(str(world["studio"] / "02_Leer"))
    steps = {s["name"]: s for s in model.climb()}
    assert steps["02_Leer"]["leaf"] is True and steps["Musikstudio"]["leaf"] is False
