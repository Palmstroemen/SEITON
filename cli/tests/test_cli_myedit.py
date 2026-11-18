# cli/tests/test_cli_myedit.py

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from core.brand import META_DIR


def _run_cmd(args, cwd, env):
    script = Path(__file__).parent.parent.parent / "cli" / "myedit.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _create_project(path: Path) -> None:
    settings_dir = path / META_DIR
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "Project.md").write_text("# MyOS Project\n")


def _recording_editor(tmp: Path) -> Path:
    """An editor that writes down the path it was given, and saves nothing."""
    editor = tmp / "editor.sh"
    editor.write_text('#!/bin/sh\nprintf "%s" "$1" > "$(dirname "$0")/opened"\n')
    editor.chmod(0o755)
    return editor


def test_myedit_opens_the_project_file_and_writes_nothing_itself():
    """Only the editor writes: a placeholder written by myedit would end the inheritance
    (an empty ACLs.md of a subproject gives no one any right)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        root.mkdir()
        _create_project(root)
        env = os.environ.copy()
        env["EDITOR"] = str(_recording_editor(tmp))

        result = _run_cmd(["tags", str(root)], cwd=tmpdir, env=env)

        assert result.returncode == 0, result.stderr
        assert (tmp / "opened").read_text() == str(root / META_DIR / "Tags.md")
        assert not (root / META_DIR / "Tags.md").exists()


def test_myedit_in_an_inheriting_subproject_says_where_the_rules_come_from():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        sub.mkdir(parents=True)
        _create_project(root)
        _create_project(sub)
        rules = "# Users\nanna: Admin\n\n# Admin\n/*: *\n"
        (root / META_DIR / "ACLs.md").write_text(rules)
        env = os.environ.copy()
        env["EDITOR"] = str(_recording_editor(tmp))

        result = _run_cmd(["acl", str(sub)], cwd=tmpdir, env=env)

        assert result.returncode == 0, result.stderr
        assert not (sub / META_DIR / "ACLs.md").exists()
        assert (root / META_DIR / "ACLs.md").read_text() == rules
        assert str(root / META_DIR / "ACLs.md") in result.stdout


def test_myedit_without_editor_changes_nothing():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "Project"
        root.mkdir()
        _create_project(root)
        env = os.environ.copy()
        env.pop("EDITOR", None)

        result = _run_cmd(["acl", str(root)], cwd=tmpdir, env=env)

        assert result.returncode != 0
        assert "EDITOR" in result.stderr
        assert sorted(p.name for p in (root / META_DIR).iterdir()) == ["Project.md"]


def test_myedit_errors_when_no_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["EDITOR"] = "true"

        result = _run_cmd(["tags", tmpdir], cwd=tmpdir, env=env)

        assert result.returncode != 0
        assert "No project found" in result.stderr
