from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script = Path(__file__).parent.parent.parent / "cli" / "seiton_drive.py"
    spec = importlib.util.spec_from_file_location("seiton_drive", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_args():
    drive = _load_module()
    args = drive.parse_args(["--projects-root", "/tmp/Projekte", "--mount-point", "/tmp/Perspektiven", "--foreground"])
    assert (args.projects_root, args.mount_point, args.foreground) == ("/tmp/Projekte", "/tmp/Perspektiven", True)
    # the former name still works
    assert drive.parse_args(["--project-root", "/x", "--mount-point", "/y"]).projects_root == "/x"


def test_main_mounts_the_drive(tmp_path, monkeypatch):
    drive = _load_module()
    captured = {}
    monkeypatch.setattr(drive, "mount_perspective_drive", lambda **kwargs: captured.update(kwargs))

    drive.main(["--projects-root", str(tmp_path / "Projekte"), "--mount-point", str(tmp_path / "Perspektiven")])

    may = captured.pop("may")  # the ACL check of every access (B11)
    assert callable(may)
    assert captured == {"projects_root": str((tmp_path / "Projekte").resolve()),
                        "mount_point": str((tmp_path / "Perspektiven").resolve()), "foreground": False}
