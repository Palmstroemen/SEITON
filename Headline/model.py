"""What the Headline shows, worked out once (Scope/Designdocument Headline.md, 3).

Where one is (shared with Scope and SunTree through the session of the lens,
daemon/lens_link.py), the standard folders there - born ones and suggested ones (embryos) - and
the path to climb from the projects root. No Qt: the top line and the panel only draw it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class HeadlineModel:
    def __init__(self, api, link, start_path: str) -> None:
        """api: a ScopeApi; link: the program's line to the lens (LensLink)."""
        self._api = api
        self._link = link
        self._cwd = str(Path(start_path).expanduser().resolve())
        self._link.call("set_cwd", {"path": self._cwd})
        self._link.update_context(self._cwd)

    # --- where one is -------------------------------------------------------------------------

    @property
    def cwd(self) -> str:
        return self._cwd

    def go(self, path: str) -> bool:
        """Stand at path: the session, and so Scope and SunTree, follow; a lens on stays (A3)."""
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            return False
        if not target.is_dir():
            return False
        self._cwd = str(target)
        self._link.call("set_cwd", {"path": self._cwd})
        self._link.update_context(self._cwd)
        return True

    def follow(self) -> bool:
        """Go where Scope or SunTree went since the Headline last set or saw the place."""
        place = self._link.follow()
        return bool(place) and self.go(place)

    def lens(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """A lens request (LensLink.REQUESTS); the lens' state afterwards, {} when refused."""
        answer = self._link.call(method, params or {})
        return dict(answer.get("result") or {}) if answer.get("ok") else {}

    # --- what it shows ------------------------------------------------------------------------

    def view(self) -> Dict[str, Any]:
        lens = self.lens("state")
        in_project = bool(lens.get("active") and lens.get("project_dir"))
        shown = str(lens.get("target") or "") if in_project else ""
        root = self._api.projects_root()
        return {
            "cwd": self._cwd,
            "name": Path(self._cwd).name,
            "projectsRoot": str(root) if root is not None else "",
            "lens": {
                "active": in_project,
                "projectDir": str(lens.get("project_dir") or "") if in_project else "",
                "target": shown,
            },
            "folders": self._folders(shown or self._cwd),
        }

    def climb(self) -> List[Dict[str, str]]:
        """The steps from the projects root down to where one is (the CWD's cascade)."""
        cwd = Path(self._cwd)
        root = self._api.projects_root()
        top = Path(root) if root is not None else None
        steps = [cwd]
        for parent in cwd.parents:
            if top is None or not (parent == top or top in parent.parents):
                break
            steps.append(parent)
        return [{"name": step.name, "path": str(step)} for step in reversed(steps)]

    def children(self, path: str) -> List[Dict[str, Any]]:
        """The folders in one step of the cascade (real ones, sorted; no suggestions)."""
        result = [{
            "name": entry["name"],
            "path": str(Path(path) / entry["name"]),
            "project": bool(entry.get("isProject")),
            "color": entry.get("color") or "",
        } for entry in self._api.list_children(path, False)]
        return sorted(result, key=lambda f: f["name"].lower())

    def _folders(self, place: str) -> List[Dict[str, Any]]:
        result = []
        for entry in self._api.list_templates(place, True):
            result.append({
                "name": entry["name"],
                "path": str(Path(place) / entry["name"]),
                "embryo": bool(entry.get("isEmbryo")),
                "batch": entry.get("batch") or "",
                "batchText": entry.get("batchText") or "",
                "color": entry.get("color") or "",
            })
        return result
