"""Whether a note opens in PostFix (core/bin/open_md.py): by default yes; the switch on Scope's
back (setting "General/postFix") turns it off, MD_USE_POSTFIX in the environment overrides both,
and without PostFix in the repository notes go to Obsidian or the system's editor."""

import importlib.util
from pathlib import Path

import pytest

from core.brand import env_name
from core.settings import Settings

OPEN_MD = Path(__file__).resolve().parents[2] / "bin" / "open_md.py"


@pytest.fixture
def open_md(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv(env_name("MD_USE_POSTFIX"), raising=False)
    spec = importlib.util.spec_from_file_location("open_md_under_test", OPEN_MD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_postfix_by_default(open_md):
    assert Settings().get("General/postFix") is True
    assert open_md.postfix_wanted()


def test_the_switch_turns_it_off(open_md):
    Settings().set("General/postFix", False)
    assert not open_md.postfix_wanted()


def test_the_environment_overrides_the_switch(open_md, monkeypatch):
    Settings().set("General/postFix", False)
    monkeypatch.setenv(env_name("MD_USE_POSTFIX"), "1")
    assert open_md.postfix_wanted()
    monkeypatch.setenv(env_name("MD_USE_POSTFIX"), "0")
    Settings().set("General/postFix", True)
    assert not open_md.postfix_wanted()


def test_without_postfix_in_the_repository_never(open_md, tmp_path, monkeypatch):
    monkeypatch.setattr(open_md, "POSTFIX_PATH", tmp_path / "PostFix" / "main.py")
    assert not open_md.postfix_wanted()


def test_switched_off_a_note_without_a_vault_goes_to_the_system(open_md, tmp_path, monkeypatch):
    Settings().set("General/postFix", False)
    note = tmp_path / "note.md"
    note.write_text("# Note\n")
    opened = []
    monkeypatch.setattr(open_md, "open_with_xdg", lambda target: opened.append(("xdg", target)) or 0)
    monkeypatch.setattr(open_md, "open_with_postfix", lambda path: opened.append(("postfix", path)) or 0)
    monkeypatch.setattr(open_md, "resolve_vault_root", lambda path: None)
    monkeypatch.setattr("sys.argv", ["open_md.py", str(note)])
    assert open_md.main() == 0
    assert opened == [("xdg", str(note.resolve()))]


def test_scope_and_suntree_leave_it_to_the_switch():
    repo = OPEN_MD.parents[2]
    for script in (repo / "Scope" / "Scope.py", repo / "SunTree" / "SunTree.py"):
        assert "MD_USE_POSTFIX" not in script.read_text(encoding="utf-8"), script
