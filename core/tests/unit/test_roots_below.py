"""Above the roots one looks downwards (Designdocument Perspective Resolver MVP.md, A11,
decided 2026-11-16): started in the home folder, the roots are the projects one level below;
none found, one is not in a SEITON metaproject."""

from pathlib import Path

from core.brand import META_DIR
from core.scope_api import roots_below


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# SEITON Project\n")
    return path


def test_the_roots_one_level_below(tmp_path):
    _project(tmp_path / "Projekte")
    _project(tmp_path / "Dokumente")
    (tmp_path / "Musik").mkdir()
    _project(tmp_path / "Musik" / "Band")  # deeper: not a root of the home folder
    assert roots_below(tmp_path) == [tmp_path / "Dokumente", tmp_path / "Projekte"]


def test_hidden_folders_are_not_looked_into(tmp_path):
    _project(tmp_path / ".cache")
    assert roots_below(tmp_path) == []


def test_none_below(tmp_path):
    (tmp_path / "Bilder").mkdir()
    assert roots_below(tmp_path) == []


def test_none_one_level_below_it_looks_one_more_level(tmp_path):
    # E5 (review 2026-11-18): the first project in ~/Dokumente/Arbeit - Headline and clock
    # started in the home folder without a root.
    (tmp_path / "Dokumente").mkdir()
    _project(tmp_path / "Dokumente" / "Arbeit")
    _project(tmp_path / "Musik" / "Band")
    (tmp_path / "Musik" / "Band" / "Probe").mkdir()
    _project(tmp_path / "Musik" / "Band" / "Probe" / "Tief")  # two more levels: not looked at
    _project(tmp_path / ".local" / "Versteckt")
    assert roots_below(tmp_path) == [tmp_path / "Dokumente" / "Arbeit", tmp_path / "Musik" / "Band"]
