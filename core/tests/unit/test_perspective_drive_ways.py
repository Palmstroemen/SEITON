"""Two things the FUSE drive learns for the programs with a role ("Designdocument Time.md",
7.2; decided 2026-11-16):

- A way may go on through a project to its subprojects:
  /0_Admin/Zeitaufwand/Projekte/Firma/7_Arbeit/Kunde Huber is Kunde Huber's
  0_Admin/Zeitaufwand. What the department folder holds comes first.
- A drive without fallback (the drive of a program with a role) shows a missing department
  folder as an empty one, born when something is saved into it, instead of the project or the
  nearest folder above it: the clock must never see 0_Admin's other folders.
"""

import shutil
from pathlib import Path

import pytest

from core.brand import META_DIR, env_name
from core.perspective_drive import PerspectiveDrive
from core.perspective_fuse import PerspectiveDriveFuse

TIME = "/0_Admin/Zeitaufwand/Projekte"


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# Project\n")
    return path


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)


@pytest.fixture
def world(tmp_path):
    template = tmp_path / META_DIR / "Templates" / "Standard"
    (template / "0_Admin" / "Zeitaufwand").mkdir(parents=True)
    (template / "0_Admin" / "01_Ziele").mkdir()
    (template / "7_Arbeit").mkdir()
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    firma = _project(root / "Firma")
    (firma / "0_Admin" / "Zeitaufwand").mkdir(parents=True)
    (firma / "0_Admin" / "Zeitaufwand" / "Oliver.md").write_text("o")
    huber = _project(firma / "7_Arbeit" / "Kunde Huber")
    (huber / "0_Admin" / "Zeitaufwand").mkdir(parents=True)
    (huber / "0_Admin" / "Zeitaufwand" / "Anna.md").write_text("a")
    (huber / "0_Admin" / "01_Ziele").mkdir()
    (huber / "0_Admin" / "01_Ziele" / "geheim.md").write_text("g")
    kitchen = _project(huber / "7_Arbeit" / "Küche")
    (kitchen / "5_Recht").mkdir()
    (kitchen / "5_Recht" / "Vertrag.pdf").write_text("v")
    _project(firma / ".Papierkorb" / "Alt")
    return {"root": root, "firma": firma, "huber": huber, "kitchen": kitchen}


# --- ways through a project --------------------------------------------------------------

def test_a_way_goes_on_through_a_project_to_its_subproject(world):
    drive = PerspectiveDrive(world["root"])
    node = drive.node(f"{TIME}/Firma/7_Arbeit/Kunde Huber")
    assert node.real == world["huber"] / "0_Admin" / "Zeitaufwand"
    assert drive.listdir(f"{TIME}/Firma/7_Arbeit/Kunde Huber") == ["Anna.md", "7_Arbeit"]  # on to Küche


def test_a_project_lists_the_ways_to_its_subprojects(world):
    drive = PerspectiveDrive(world["root"])
    assert drive.listdir(f"{TIME}/Firma") == ["Oliver.md", "7_Arbeit"]
    assert drive.listdir(f"{TIME}/Firma/7_Arbeit") == ["Kunde Huber"]
    assert drive.node(f"{TIME}/Firma/7_Arbeit").real is None  # a way, no folder of its own


def test_down_to_the_grandchild(world):
    drive = PerspectiveDrive(world["root"], fallback=False)
    node = drive.node(f"{TIME}/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche")
    assert node.project == ("Firma", "7_Arbeit", "Kunde Huber", "7_Arbeit", "Küche")


def test_what_the_department_folder_holds_comes_first(world):
    (world["firma"] / "0_Admin" / "Zeitaufwand" / "7_Arbeit").mkdir()
    drive = PerspectiveDrive(world["root"])
    assert drive.node(f"{TIME}/Firma/7_Arbeit").real == world["firma"] / "0_Admin" / "Zeitaufwand" / "7_Arbeit"
    assert drive.listdir(f"{TIME}/Firma").count("7_Arbeit") == 1


def test_no_way_through_hidden_folders(world):
    drive = PerspectiveDrive(world["root"])
    assert drive.node(f"{TIME}/Firma/.Papierkorb/Alt") is None
    assert ".Papierkorb" not in drive.listdir(f"{TIME}/Firma")


def test_saving_into_a_subproject_lands_there(world):
    drive = PerspectiveDrive(world["root"])
    target = drive.target_for_create(f"{TIME}/Firma/7_Arbeit/Kunde Huber/Ben.md")
    assert target == world["huber"] / "0_Admin" / "Zeitaufwand" / "Ben.md"


def test_nothing_is_saved_on_a_way(world):
    drive = PerspectiveDrive(world["root"])
    with pytest.raises(PermissionError):
        drive.target_for_create(f"{TIME}/Firma/7_Arbeit/Ben.md")


# --- without fallback ----------------------------------------------------------------------

def test_with_fallback_a_missing_folder_shows_the_project_itself(world):
    # as before, for LibreOffice: the project itself stands in for the department folder
    drive = PerspectiveDrive(world["root"])
    assert "5_Recht" in drive.listdir(f"{TIME}/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche")


def test_without_fallback_a_missing_folder_is_empty(world):
    drive = PerspectiveDrive(world["root"], fallback=False)
    path = f"{TIME}/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche"
    node = drive.node(path)
    assert node.is_dir and node.real is None and node.missing
    assert drive.listdir(path) == []
    assert drive.node(path + "/5_Recht") is None
    assert drive.node(path + "/5_Recht/Vertrag.pdf") is None


def test_without_fallback_0_admins_other_folders_stay_unseen(world):
    del_time = world["huber"] / "0_Admin" / "Zeitaufwand"
    for item in del_time.iterdir():
        item.unlink()
    del_time.rmdir()  # Kunde Huber has 0_Admin, but no Zeitaufwand yet
    leaky = PerspectiveDrive(world["root"])
    assert "01_Ziele" in leaky.listdir(f"{TIME}/Firma/7_Arbeit/Kunde Huber")  # the fallback
    drive = PerspectiveDrive(world["root"], fallback=False)
    assert drive.listdir(f"{TIME}/Firma/7_Arbeit/Kunde Huber") == ["7_Arbeit"]
    assert drive.node(f"{TIME}/Firma/7_Arbeit/Kunde Huber/01_Ziele/geheim.md") is None


def test_without_fallback_the_folder_is_born_when_saving(world):
    drive = PerspectiveDrive(world["root"], fallback=False)
    target = drive.target_for_create(f"{TIME}/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche/Anna.md")
    assert target == world["kitchen"] / "0_Admin" / "Zeitaufwand" / "Anna.md"
    assert target.parent.is_dir()


def test_without_fallback_the_acl_check_asks_for_the_missing_folder(world):
    kitchen_time = world["kitchen"] / "0_Admin" / "Zeitaufwand"
    asked = []
    drive = PerspectiveDrive(world["root"], fallback=False,
                             may=lambda path, action: asked.append((path, action)) or path != kitchen_time)
    with pytest.raises(PermissionError):
        drive.node(f"{TIME}/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche")
    assert (kitchen_time, "read") in asked


def test_the_fuse_drive_writes_into_a_missing_folder(world):
    fs = PerspectiveDriveFuse(PerspectiveDrive(world["root"], fallback=False))
    path = f"{TIME}/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche"
    assert fs.getattr(path)["st_mode"] & 0o200  # shown as a folder one may write into
    handle = fs.create(path + "/Anna.md", 0o644)
    fs.write(path + "/Anna.md", b"| Datum |\n", 0, handle)
    fs.release(path + "/Anna.md", handle)
    assert (world["kitchen"] / "0_Admin" / "Zeitaufwand" / "Anna.md").read_bytes() == b"| Datum |\n"


def test_a_parent_without_the_department_still_shows_the_way(world):
    """"docs/Prüfung 2026-11-18.md", B3: with the fallback, a parent without the department
    folder stood in with its whole top level, and the way to its subprojects was hidden."""
    (world["root"].parent / META_DIR / "Templates" / "Standard" / "5_Recht").mkdir()  # a department
    drive = PerspectiveDrive(world["root"])  # with fallback, as the drive "Perspektiven"
    assert not (world["firma"] / "5_Recht").exists() and not (world["huber"] / "5_Recht").exists()
    way = "/5_Recht/Projekte/Firma/7_Arbeit/Kunde Huber/7_Arbeit/Küche"
    assert drive.listdir(way) == ["Vertrag.pdf"]
    assert drive.target_for_create(way + "/x.pdf") == world["kitchen"] / "5_Recht" / "x.pdf"
