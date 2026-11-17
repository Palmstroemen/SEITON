"""What the Headline shows, worked out once (Scope/Designdocument Headline.md, 3).

Where one is (shared with Scope and SunTree through the session of the lens,
daemon/lens_link.py), the standard folders there - born ones and suggested ones (embryos) - and
the path to climb from the projects root. No Qt: the top line and the panel only draw it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.brand import META_DIR
from core.identity import person_for
from core.scope_api import find_project_root


class HeadlineModel:
    def __init__(self, api, link, start_path: str,
                 report: Optional[Callable[[Optional[str], str], None]] = None) -> None:
        """api: a ScopeApi; link: the program's line to the lens (LensLink); report(project,
        person): told the active project on every change of it (for the clock, 3a)."""
        self._api = api
        self._link = link
        self._report = report
        self._reported: Optional[tuple] = None
        self._cwd = str(Path(start_path).expanduser().resolve())
        self._link.call("set_cwd", {"path": self._cwd})
        self._link.update_context(self._cwd)
        self._tell_project()

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
        self._tell_project()
        return True

    def active_project(self) -> Optional[str]:
        """The project one works in: the lens' project while it is on, else the CWD's. The
        projects root holds the projects and is none to count time on."""
        lens = self.lens("state")
        if lens.get("active") and lens.get("project_dir"):
            return str(lens["project_dir"])
        project = find_project_root(Path(self._cwd))
        root = self._api.projects_root()
        if project is None or (root is not None and Path(project) == Path(root)):
            return None
        return str(project)

    def _tell_project(self) -> None:
        if self._report is None:
            return
        project = self.active_project()
        person = person_for(project) if project else ""
        if (project, person) != self._reported:
            self._reported = (project, person)
            self._report(project, person)

    def follow(self) -> bool:
        """Go where Scope or SunTree went since the Headline last set or saw the place."""
        place = self._link.follow()
        return bool(place) and self.go(place)

    def lens(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """A lens request (LensLink.REQUESTS); the lens' state afterwards, {} when refused."""
        answer = self._link.call(method, params or {})
        if method != "state" and answer.get("ok"):
            self._tell_project()  # a lens on another project changes the active one
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
        return [{"name": step.name, "path": str(step), "project": (step / META_DIR / "Project.md").is_file(),
                 **self._badge(step)} for step in reversed(steps)]

    def _badge(self, folder: Path) -> Dict[str, str]:
        """A folder's own badge (its .seiton/batch.*), as Scope's rows show it."""
        found = getattr(self._api, "_get_folder_batch", lambda _f: {})(Path(folder)) or {}
        return {"batch": found.get("batch") or "", "batchText": found.get("batchText") or ""}

    # --- the perspectives of the root (Designdocument Perspective Resolver MVP.md, A11) -----

    def perspectives(self) -> List[Dict[str, Any]]:
        """The root's named perspectives (its .seiton/Perspectives.md), each named as its
        folder; two of the same name get a part of their path. active: the lens wears it."""
        lenses = self._listed_lenses()
        worn = list(self.lens("state").get("lens") or []) if self.lens("state").get("active") else []
        last = [parts[-1] for parts in lenses]
        result = []
        for parts in lenses:
            name = parts[-1]
            if last.count(name) > 1 and len(parts) > 1:
                name = f"{name} ({'/'.join(parts[:-1])})"
            result.append({"name": name, "lens": list(parts), "active": list(parts) == worn})
        return result

    def wear(self, lens: List[str]) -> bool:
        """A click on a perspective: put that lens on; on the one worn already, take it off."""
        state = self.lens("state")
        if state.get("active") and list(state.get("lens") or []) == list(lens):
            return bool(self.lens("take_off"))
        return bool(self.lens("put_on", {"lens": list(lens)}))

    def _listed_lenses(self) -> List[tuple]:
        root = self._api.projects_root()
        if root is None:
            return []
        listing = Path(root) / META_DIR / "Perspectives.md"
        try:
            lines = listing.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        lenses = []
        for line in lines:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            parts = tuple(part for part in text.split("/") if part)
            # Security: a perspective is a folder path inside the root, nothing above it.
            if text.startswith("/") or not parts or any(p in (".", "..") for p in parts):
                continue
            lenses.append(parts)
        return lenses

    def children(self, path: str) -> List[Dict[str, Any]]:
        """The folders in one step of the cascade (real ones, sorted; no suggestions)."""
        result = [{
            "name": entry["name"],
            "path": str(Path(path) / entry["name"]),
            "project": bool(entry.get("isProject")),
            "color": entry.get("color") or "",
            "batch": entry.get("batch") or "",
            "batchText": entry.get("batchText") or "",
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
