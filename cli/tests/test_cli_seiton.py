"""The one command `seiton`: without a subcommand it starts Scope, with one it runs that tool
(cli/seiton.py). One name in PATH instead of eight, like git or gh."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from cli import seiton

REPO = Path(__file__).resolve().parents[2]
COMMANDS = ("ls", "project", "tag", "acl", "edit", "filter", "export", "import", "drive")


def _run(*args, cwd=None):
    return subprocess.run([sys.executable, str(REPO / "cli" / "seiton.py"), *args],
                          capture_output=True, text=True, cwd=cwd)


def test_every_command_has_its_module_with_a_main():
    assert tuple(seiton.COMMANDS) == COMMANDS
    for name in COMMANDS:
        module = seiton.load(name)
        assert callable(module.main), name


def test_no_tool_keeps_the_old_name():
    assert not list((REPO / "cli").glob("my*.py"))


@pytest.mark.parametrize("name", COMMANDS)
def test_each_command_names_itself_in_its_help(name):
    result = _run(name, "--help")
    assert result.returncode == 0, result.stderr
    assert f"usage: seiton {name}" in result.stdout
    assert "my" + name not in result.stdout


def test_a_command_gets_the_rest_of_the_line(tmp_path):
    (tmp_path / "Brief.md").write_text("x", encoding="utf-8")
    result = _run("ls", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "Brief.md" in result.stdout


def test_help_lists_the_commands():
    for flag in ("--help", "-h", "help"):
        result = _run(flag)
        assert result.returncode == 0
        for name in COMMANDS:
            assert f"  {name} " in result.stdout, (flag, name)


def test_without_a_command_scope_starts_with_the_arguments(tmp_path):
    started = []
    assert seiton.main([], start_gui=started.append) == 0
    assert seiton.main([str(tmp_path)], start_gui=started.append) == 0
    assert started == [[], [str(tmp_path)]]


def test_a_folder_named_like_a_command_opens_with_a_path(tmp_path, monkeypatch):
    (tmp_path / "tag").mkdir()
    monkeypatch.chdir(tmp_path)
    started = []
    seiton.main(["./tag"], start_gui=started.append)
    assert started == [["./tag"]]


def test_an_unknown_word_is_an_error_not_a_folder(capsys):
    started = []
    assert seiton.main(["lss"], start_gui=started.append) == 2
    assert started == []
    err = capsys.readouterr().err
    assert "lss" in err and "seiton ls" in err  # the closest command is suggested


def test_scope_is_started_as_its_own_script(monkeypatch):
    """As `python3 apps/Scope/Scope.py` would: its folder first on the path (it imports its
    neighbours, window_icon & co.), its name in argv[0], the arguments behind it."""
    seen = {}

    def fake_run_path(path, run_name):
        seen.update(path=path, run_name=run_name, first=sys.path[0], argv=list(sys.argv))

    monkeypatch.setattr(seiton.runpy, "run_path", fake_run_path)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["seiton"])
    seiton.start_scope(["--search", "/x"])
    scope = REPO / "apps" / "Scope" / "Scope.py"
    assert seen == {"path": str(scope), "run_name": "__main__", "first": str(scope.parent),
                    "argv": [str(scope), "--search", "/x"]}
