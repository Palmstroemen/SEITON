# cli/tests/test_cli_mytag.py

import subprocess
import sys
import tempfile
from pathlib import Path
import os

import pytest


def _run_cmd(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "mytag.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _skip_if_no_xattr():
    if not hasattr(os, "setxattr") or not hasattr(os, "getxattr"):
        pytest.skip("xattr not available on this platform")


def test_mytag_set_and_list():
    _skip_if_no_xattr()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        target = tmp / "file.txt"
        target.write_text("x")

        result = _run_cmd(["set", str(target), "wichtig=60"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "wichtig=60" in result.stdout


def test_mytag_add_remove_clear():
    _skip_if_no_xattr()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        target = tmp / "file.txt"
        target.write_text("x")

        result = _run_cmd(["add", str(target), "dringend"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "dringend" in result.stdout

        result = _run_cmd(["remove", str(target), "dringend"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "No tags" in result.stdout

        result = _run_cmd(["add", str(target), "foo"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["clear", str(target)], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "No tags" in result.stdout


def test_folder_tags_are_the_ones_scope_shows(tmp_path):
    """"docs/Prüfung 2026-11-18.md", CLI2: a folder's tags live in .seiton/myTags.md, as Scope
    keeps them - the CLI wrote them as extended attributes, which Scope never read."""
    from core.brand import META_DIR
    from core.scope_api import ScopeApi

    folder = tmp_path / "Rechnungen"
    folder.mkdir()
    assert _run_cmd(["add", str(folder), "wichtig"], cwd=tmp_path).returncode == 0
    assert ScopeApi(str(tmp_path)).list_folder_tags(str(folder)) == ["wichtig"]
    assert (folder / META_DIR / "myTags.md").is_file()
    ScopeApi(str(tmp_path)).set_folder_tags(str(folder), ["wichtig", "2026"])
    assert _run_cmd(["list", str(folder)], cwd=tmp_path).stdout.strip() == "2026, wichtig"
    assert _run_cmd(["remove", str(folder), "2026"], cwd=tmp_path).returncode == 0
    assert ScopeApi(str(tmp_path)).list_folder_tags(str(folder)) == ["wichtig"]
    refused = _run_cmd(["set", str(folder), "wichtig=60"], cwd=tmp_path)
    assert refused.returncode == 1 and "folder" in refused.stderr.lower()
    assert _run_cmd(["clear", str(folder)], cwd=tmp_path).returncode == 0
    assert not (folder / META_DIR).exists()


def test_myls_shows_the_folder_tags_scope_shows(tmp_path):
    from core.scope_api import ScopeApi

    folder = tmp_path / "Rechnungen"
    folder.mkdir()
    ScopeApi(str(tmp_path)).set_folder_tags(str(folder), ["wichtig"])
    script = Path(__file__).parent.parent.parent / "cli" / "myls.py"
    shown = subprocess.run([sys.executable, str(script), str(tmp_path), "--tags"], capture_output=True, text=True)
    assert "Rechnungen: wichtig" in shown.stdout, (shown.stdout, shown.stderr)
