# cli/tests/test_cli_project.py

import subprocess
import sys
import tempfile
from pathlib import Path
from core.brand import META_DIR, env_name


def _run_project(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "seiton.py"
    return subprocess.run(
        [sys.executable, str(script), "project"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_project_create_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "Root"
        child = root / "Child"
        child.mkdir(parents=True)

        settings_dir = root / META_DIR
        settings_dir.mkdir(parents=True)
        (settings_dir / "Project.md").write_text("# SEITON Project\n")

        result = _run_project(["create", str(child)], cwd=tmpdir)

        assert result.returncode == 0
        assert (child / META_DIR / "Project.md").exists()


def test_project_create_without_parent_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "NoParent"
        target.mkdir()

        result = _run_project(["create", str(target)], cwd=tmpdir)

        assert result.returncode != 0
        assert "Error:" in result.stderr


def test_project_create_new_path_with_flag():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "Root"
        root.mkdir()
        settings_dir = root / META_DIR
        settings_dir.mkdir(parents=True)
        (settings_dir / "Project.md").write_text("# SEITON Project\n")

        target = root / "NewChild"
        result = _run_project(["create", "--new", str(target)], cwd=tmpdir)

        assert result.returncode == 0
        assert (target / META_DIR / "Project.md").exists()


def _tidy_project(tmpdir: str) -> Path:
    """Project with born 04_Finanz/Ausgaben (unused) and Einnahmen (holds a user file)."""
    root = Path(tmpdir) / "Project"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# SEITON Project\n")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    template = root / META_DIR / "Templates" / "Standard" / "04_Finanz"
    (template / "Ausgaben").mkdir(parents=True)
    (template / "Einnahmen").mkdir(parents=True)
    (root / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    (root / "04_Finanz" / "Einnahmen").mkdir(parents=True)
    (root / "04_Finanz" / "Einnahmen" / "Beleg.pdf").write_bytes(b"%PDF")
    (root / "Privat").mkdir()
    return root


def _env_without_templates_override():
    import os
    return {k: v for k, v in os.environ.items() if k not in (env_name("TEMPLATES_DIR"), env_name("ROLES"))}


def test_project_tidy_turns_unused_born_folders_back_into_embryos():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _tidy_project(tmpdir)
        script = Path(__file__).parent.parent.parent / "cli" / "seiton.py"

        result = subprocess.run(
            [sys.executable, str(script), "project", "tidy", str(root / "04_Finanz")],
            capture_output=True, text=True, cwd=tmpdir, env=_env_without_templates_override(),
        )

        assert result.returncode == 0, result.stderr
        assert not (root / "04_Finanz" / "Ausgaben").exists()
        assert (root / "04_Finanz" / "Einnahmen" / "Beleg.pdf").is_file()
        assert (root / "Privat").is_dir()
        assert str(root / "04_Finanz" / "Ausgaben") in result.stdout


def test_project_tidy_outside_project_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run_project(["tidy", tmpdir], cwd=tmpdir)

        assert result.returncode == 1


def test_project_tidy_also_tidies_nested_sub_projects():
    with tempfile.TemporaryDirectory() as tmpdir:
        parent = Path(tmpdir) / "Parent"
        (parent / META_DIR).mkdir(parents=True)
        (parent / META_DIR / "Project.md").write_text("# SEITON Project\n")
        sub = _tidy_project(str(parent))
        script = Path(__file__).parent.parent.parent / "cli" / "seiton.py"

        result = subprocess.run(
            [sys.executable, str(script), "project", "tidy", str(parent)],
            capture_output=True, text=True, cwd=tmpdir, env=_env_without_templates_override(),
        )

        assert result.returncode == 0, result.stderr
        assert not (sub / "04_Finanz" / "Ausgaben").exists()
        assert (sub / "04_Finanz" / "Einnahmen" / "Beleg.pdf").is_file()


def _trash_project(tmpdir):
    import os
    root = Path(tmpdir) / "Root"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# SEITON Project\n")
    for name in ("Alt", "Neu"):
        (root / name).mkdir()
        (root / name / "a.md").write_text(name)
    return root


def _env():
    import os
    env = {k: v for k, v in os.environ.items() if not k.startswith(env_name("ACL"))}
    env[env_name("ACL_USER")] = "tester"
    return env


def _run(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "seiton.py"
    return subprocess.run([sys.executable, str(script), "project"] + args, capture_output=True, text=True, cwd=cwd, env=_env())


def test_project_trash_list_restore_delete_empty():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core import trash

    with tempfile.TemporaryDirectory() as tmpdir:
        root = _trash_project(tmpdir)
        trash.move_to_trash(root / "Alt", deleted_by="tester")
        trash.move_to_trash(root / "Neu", deleted_by="tester")

        listed = _run(["trash", "list", str(root)], cwd=tmpdir)
        assert listed.returncode == 0
        assert "Alt" in listed.stdout and "Neu" in listed.stdout and "tester" in listed.stdout

        assert _run(["trash", "restore", "Alt", "--in", str(root)], cwd=tmpdir).returncode == 0
        assert (root / "Alt" / "a.md").exists()

        refused = _run(["trash", "empty", "--in", str(root)], cwd=tmpdir)
        assert refused.returncode != 0 and "--yes" in refused.stderr
        assert [e.name for e in trash.list_trash(root)] == ["Neu"]

        assert _run(["trash", "empty", "--in", str(root), "--yes"], cwd=tmpdir).returncode == 0
        assert trash.list_trash(root) == []

        trash.move_to_trash(root / "Alt", deleted_by="tester")
        assert _run(["trash", "delete", "Alt", "--in", str(root)], cwd=tmpdir).returncode == 0
        assert trash.list_trash(root) == []
        missing = _run(["trash", "restore", "Nix", "--in", str(root)], cwd=tmpdir)
        assert missing.returncode != 0


def _project(args, cwd):
    import subprocess
    import sys
    script = Path(__file__).parent.parent.parent / "cli" / "seiton.py"
    return subprocess.run([sys.executable, str(script), "project"] + args, capture_output=True, text=True, cwd=cwd)


def _root(tmp_path):
    from core.brand import META_DIR

    root = tmp_path / "Projekte"
    (root / META_DIR / "Templates" / "Standard" / "4_Finanz").mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# SEITON Project\n")
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    return root


def test_create_refuses_what_the_p_button_refuses(tmp_path):
    """"docs/Prüfung 2026-11-18.md", CLI4: a template folder or a settings folder became a project."""
    from core.brand import META_DIR

    root = _root(tmp_path)
    template_folder = root / META_DIR / "Templates" / "Standard" / "4_Finanz"
    refused = _project(["create", str(template_folder)], tmp_path)
    assert refused.returncode == 1 and not (template_folder / META_DIR).exists(), refused.stderr
    again = _project(["create", str(root)], tmp_path)
    assert again.returncode == 1 and "already" in again.stderr.lower()
    (root / "Kunde").mkdir()
    assert _project(["create", str(root / "Kunde")], tmp_path).returncode == 0


def test_remove_makes_a_project_a_folder_again(tmp_path):
    """"docs/Prüfung 2026-11-18.md", CLI5."""
    from core.brand import META_DIR

    root = _root(tmp_path)
    kunde = root / "Kunde"
    kunde.mkdir()
    assert _project(["create", str(kunde)], tmp_path).returncode == 0
    (kunde / META_DIR / "Tags.md").write_text("# Tags\n#wichtig\n")  # a setting of its own
    asked = _project(["remove", str(kunde)], tmp_path)
    assert asked.returncode == 1 and "Tags.md" in asked.stderr and "--keep-own" in asked.stderr
    assert _project(["remove", str(kunde), "--keep-own"], tmp_path).returncode == 0
    assert not (kunde / META_DIR).exists()
