"""SEITON stands without the workshop pieces PostFix and SunTree: nothing in the core, the CLI,
the daemons or the apps (apps/) import them; the one small crown that borrows SunTree's arithmetic is
loaded only when SunTree is there, and Scope tells its back whether it is."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
IMPORT = re.compile(r"^\s*(from|import)\s+(examples|PostFix|SunTree)\b", re.MULTILINE)


def _sources(suffix):
    for folder in ("core", "cli", "daemon", "apps"):
        assert (REPO / folder).is_dir(), folder  # a folder gone would find nothing
        for path in (REPO / folder).rglob(f"*{suffix}"):
            if "tests" not in path.parts and "__pycache__" not in path.parts:
                yield path


def test_no_python_of_seiton_imports_postfix_or_suntree():
    found = [str(p.relative_to(REPO)) for p in _sources(".py") if IMPORT.search(p.read_text(encoding="utf-8"))]
    assert found == []


def test_only_the_small_crown_reaches_into_suntree():
    reaching = [p.name for p in _sources(".qml")
                if re.search(r'import\s+"(?:\.\./)+examples/', p.read_text(encoding="utf-8"))]
    assert reaching == ["CrownPreview.qml"]


def test_scope_tells_its_back_whether_suntree_is_there():
    scope = (REPO / "apps" / "Scope" / "Scope.py").read_text(encoding="utf-8")
    main = (REPO / "apps" / "Scope" / "main.qml").read_text(encoding="utf-8")
    assert 'ctx.setContextProperty("scopeSunTreePresent", sun_tree_present())' in scope
    assert "sunTreePresent: typeof scopeSunTreePresent" in main


def test_sun_tree_present_looks_for_suntree(tmp_path, monkeypatch):
    import os
    import sys

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, str(REPO))
    from apps.Scope import Scope as scope

    assert scope.sun_tree_present() == (REPO / "examples" / "SunTree" / "SunTree.py").is_file()
    monkeypatch.setattr(scope, "REPO_ROOT", tmp_path)
    assert scope.sun_tree_present() is False
