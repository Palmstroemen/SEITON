"""Programs with a role (core/programs.py, "Designdocument Time.md" 7.1): written down once,
readable, in ~/.config/seiton/Programs.md. A rule's path is a path in every project, as in
ACLs.md, so one rule fits all projects, also those that do not exist yet. The role only says
what the program may at most; the person's ACLs still apply on top (the drive asks both)."""

from pathlib import Path

import pytest

from core import programs as pg
from core.brand import META_DIR

TEXT = """# Programs

Notes in between are fine.

## Zeiterfassung
- Program: seiton-clock
- /0_Admin/Zeitaufwand/: read, write

## Bildbetrachter
- Program: eog
- /9_Dokumentation/92_Bilder/: read
"""


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# Project\n")
    return path


@pytest.fixture
def world(tmp_path):
    root = tmp_path / "Projekte"
    firma = _project(root / "Firma")
    huber = _project(firma / "7_Arbeit" / "Kunde Huber")
    return root, firma, huber


def test_reading_the_roles():
    roles = pg.parse(TEXT)
    assert [r.name for r in roles] == ["Zeiterfassung", "Bildbetrachter"]
    clock = pg.role_for("seiton-clock", roles)
    assert clock.rules == [("/0_Admin/Zeitaufwand", frozenset({"read", "write"}))]
    assert pg.role_for("gimp", roles) is None


def test_without_a_file_the_clock_has_its_role(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert pg.programs_file() == tmp_path / "config" / "seiton" / "Programs.md"
    clock = pg.role_for("seiton-clock", pg.load())
    assert clock is not None and clock.rules == [("/0_Admin/Zeitaufwand", frozenset({"read", "write"}))]


def test_the_file_written_by_hand_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    pg.programs_file().parent.mkdir(parents=True)
    pg.programs_file().write_text("# Programs\n\n## Zeiterfassung\n- Program: seiton-clock\n- /0_Admin/Zeitaufwand/: read\n")
    assert pg.role_for("seiton-clock", pg.load()).rules == [("/0_Admin/Zeitaufwand", frozenset({"read"}))]


def test_the_role_holds_in_every_project_and_subproject(world):
    root, firma, huber = world
    clock = pg.role_for("seiton-clock", pg.parse(TEXT))
    assert clock.allows(root, firma / "0_Admin" / "Zeitaufwand" / "Oliver.md", "write")
    assert clock.allows(root, huber / "0_Admin" / "Zeitaufwand" / "Anna.md", "write")
    assert clock.allows(root, huber / "0_Admin" / "Zeitaufwand", "read")  # the folder itself


def test_and_nowhere_else(world):
    root, firma, huber = world
    clock = pg.role_for("seiton-clock", pg.parse(TEXT))
    assert not clock.allows(root, huber / "0_Admin", "read")
    assert not clock.allows(root, huber / "0_Admin" / "01_Ziele" / "geheim.md", "read")
    assert not clock.allows(root, firma / "7_Arbeit" / "0_Admin" / "Zeitaufwand" / "x.md", "write")  # no project there
    assert not clock.allows(root, root.parent / "elsewhere" / "0_Admin" / "Zeitaufwand" / "x.md", "write")
    assert not clock.allows(root, firma / "0_Admin" / "Zeitaufwand" / ".." / ".." / "5_Recht" / "v.pdf", "read")


def test_a_right_the_role_does_not_have(world):
    root, _firma, huber = world
    viewer = pg.role_for("eog", pg.parse(TEXT))
    assert viewer.allows(root, huber / "9_Dokumentation" / "92_Bilder" / "a.jpg", "read")
    assert not viewer.allows(root, huber / "9_Dokumentation" / "92_Bilder" / "a.jpg", "write")


def test_a_broken_rule_is_named():
    roles, problems = pg.parse_with_problems("# Programs\n\n## X\n- Program: x\n- /a/: fly\n- nonsense\n")
    assert roles[0].rules == []
    assert len(problems) == 2


def test_a_role_without_program_is_named_and_left_out():
    roles, problems = pg.parse_with_problems("# Programs\n\n## X\n- /a/: read\n")
    assert roles == [] and problems
