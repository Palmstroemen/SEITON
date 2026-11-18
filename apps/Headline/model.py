"""What the Headline shows, worked out once (apps/Scope/Designdocument Headline.md, 3).

Where one is (shared with Scope and SunTree through the session of the lens,
daemon/lens_link.py), the standard folders there - born ones and suggested ones (embryos) - and
the path to climb from the projects root. No Qt: the top line and the panel only draw it.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse
from typing import Any, Callable, Dict, List, Optional

from core.brand import META_DIR
from core.identity import person_for
from core.scope_api import find_project_root


SCOPE_PATHS = "__SCOPE_PATHS__"  # Scope's own drag of several entries (apps/Scope/js/DropUtils.js)


def _path_of(value: str) -> Optional[str]:
    value = str(value or "").strip()
    if value.startswith("file://"):
        parsed = urlparse(value)
        if parsed.netloc not in ("", "localhost"):
            return None
        value = unquote(parsed.path)
    # Security: only absolute local paths; a URL of another kind or a relative path is no file.
    return value if value.startswith("/") else None


def sources_of(payload: str) -> List[str]:
    """The paths a drop brings: Scope's own list, a uri-list (Nemo, Nautilus), one URL or path."""
    text = str(payload or "").strip()
    if text.startswith(SCOPE_PATHS):
        try:
            values = json.loads(text[len(SCOPE_PATHS):])
        except ValueError:
            return []
        values = values if isinstance(values, list) else []
    else:
        values = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    return [path for path in (_path_of(v) for v in values) if path]


class HeadlineModel:
    def __init__(self, api, link, start_path: str,
                 report: Optional[Callable[[Optional[str], str], None]] = None,
                 remember: Optional[Callable[[str], None]] = None) -> None:
        """api: a ScopeApi; link: the program's line to the lens (LensLink); report(project,
        person): told the active project on every change of it (for the clock, 3a);
        remember(place): told each new place (last_place.py: the next start goes back there)."""
        self._api = api
        self._link = link
        self._report = report
        self._remember = remember
        self._reported: Optional[tuple] = None
        self._seen_lens: Optional[tuple] = None  # the lens as last seen (follow)
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
        if self._remember is not None:
            self._remember(self._cwd)
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
        """Go where Scope or SunTree went since the Headline last set or saw the place; True
        too when they put the lens on, took it off or moved it (the place stays then, A3)."""
        place = self._link.follow()
        if place and self.go(place):
            return True
        # The state follow() just asked; asked again only from a link that does not keep it.
        state = getattr(self._link, "last_state", None)
        if state is None:
            state = self.lens("state")
        seen = (bool(state.get("active")), str(state.get("project_dir") or ""),
                str(state.get("target") or ""), tuple(state.get("lens") or ()))
        if self._seen_lens is None:
            self._seen_lens = seen
            return False
        if seen == self._seen_lens:
            return False
        self._seen_lens = seen
        self._tell_project()
        return True

    def lens(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """A lens request (LensLink.REQUESTS); the lens' state afterwards, {} when refused."""
        answer = self._link.call(method, params or {})
        if method != "state" and answer.get("ok"):
            self._tell_project()  # a lens on another project changes the active one
        return dict(answer.get("result") or {}) if answer.get("ok") else {}

    # --- dropping onto a folder (Designdocument Headline.md, 3; review 2026-11-18, H9) ----------

    def plan_drop(self, payload: str, target: str) -> Dict[str, Any]:
        """What a drop onto target would move; folders among it are asked about first (as in
        Scope). A suggested folder is born only when something is moved into it."""
        sources = sources_of(payload)
        folders = sum(1 for source in sources if Path(source).is_dir())
        return {"sources": sources, "folders": folders, "target": str(target)}

    def move(self, sources: List[str], target: str) -> Dict[str, Any]:
        """Move sources into target as Scope does (ScopeApi.move_entries: the ACLs, filing by
        date, an embryo born on the way); how many moved, the names of those that did not."""
        result = self._api.move_entries([str(s) for s in sources], str(target))
        failed = [Path(str(item.get("source") or item.get("target") or "")).name
                  for item in result.get("errors", [])]
        return {"moved": len(result.get("moved", [])), "failed": failed}

    # --- what it shows ------------------------------------------------------------------------

    def view(self) -> Dict[str, Any]:
        lens = self.lens("state")
        in_project = bool(lens.get("active") and lens.get("project_dir"))
        shown = str(lens.get("target") or "") if in_project else ""
        root = self._api.projects_root()
        return {
            "cwd": self._cwd,
            "name": Path(self._cwd).name,
            # The CWD's icon as in Scope: its own badge, a "P" when it is a project.
            "project": (Path(self._cwd) / META_DIR / "Project.md").is_file(),
            **self._badge(Path(self._cwd)),
            "projectsRoot": str(root) if root is not None else "",
            "lens": {
                "active": in_project,
                "projectDir": str(lens.get("project_dir") or "") if in_project else "",
                "target": shown,
            },
            "folders": self._folders(shown or self._cwd),
        }

    def climb(self) -> List[Dict[str, Any]]:
        """The steps from "/" down to where one is (the CWD's cascade). Those above the projects
        root are marked `above`: one may leave it, into /home say (2026-11-18), and sees where
        SEITON's projects end. A project's step carries its colour, as Scope's rows."""
        cwd = Path(self._cwd)
        root = self._api.projects_root()
        top = Path(root) if root is not None else None
        steps = [cwd, *cwd.parents]
        return [{"name": step.name or "/", "path": str(step),
                 "above": top is not None and step != top and step in top.parents,
                 **self._looks(step)} for step in reversed(steps)]

    def _looks(self, folder: Path) -> Dict[str, Any]:
        """How a folder is drawn in the dropdowns: project (its P), its colour, its badge."""
        project = (folder / META_DIR / "Project.md").is_file()
        colour = getattr(self._api, "_resolve_effective_project_color", lambda _f: None)
        return {"project": project, "color": (colour(folder) or "") if project else "", **self._badge(folder)}

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
