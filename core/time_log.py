# time_log.py - the time spent on a project, one file per person
#
# See "Designdocument Time.md", sections 2, 3 and 5. A person's time in a project lies in
# 0_Admin/Zeitaufwand/<person>.md, a Markdown table of stretches: when one began and how long
# it lasted (no "To": it would say the same twice, and it confuses when summer time begins or
# ends). The columns are German or English; both are read, and a file keeps its language.
# A parent's time is its own plus that of its children, read where it lies, never copied.
# Rounding (for invoices) is only done in the sums, never in the file.

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Union

from core.brand import META_DIR

TIME_DIR = Path("0_Admin") / "Zeitaufwand"
KINDS = ("auto", "manual", "added", "corrected")
LANGUAGES = ("de", "en")

# The columns in the order a new file has them, and their names per language.
COLUMNS = ("date", "start", "duration", "kind", "note")
COLUMN_NAMES = {
    "de": {"date": "Datum", "start": "Von", "duration": "Dauer", "kind": "Art", "note": "Notiz"},
    "en": {"date": "Date", "start": "From", "duration": "Time", "kind": "Kind", "note": "Note"},
}
KIND_NAMES = {
    "de": {"auto": "auto", "manual": "manuell", "added": "nachgetragen", "corrected": "korrigiert"},
    "en": {"auto": "auto", "manual": "manual", "added": "added", "corrected": "corrected"},
}
TITLES = {"de": "Zeitaufwand", "en": "Time"}

_COLUMN_OF = {name.lower(): (column, language)
              for language, names in COLUMN_NAMES.items() for column, name in names.items()}
_KIND_OF = {name.lower(): kind for names in KIND_NAMES.values() for kind, name in names.items()}
_START = re.compile(r"^(\d{1,2}):(\d{2})(?:([+-])(\d{2}):(\d{2}))?$")
_DURATION = re.compile(r"^(\d+):([0-5]\d)$")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
# What a cloud makes of a file two computers changed at once: Nextcloud's client in English
# and German.
_CONFLICT = re.compile(r"^(?P<person>.+?) \((?:conflicted copy|Konflikt)[^)]*\)$", re.IGNORECASE)


@dataclass(frozen=True)
class Stretch:
    """One row: a stretch of time on one day."""
    day: date
    start: Optional[time]  # local time; None for an added stretch without a beginning
    duration: timedelta
    kind: str  # one of KINDS
    note: str = ""
    offset: Optional[timedelta] = None  # only away from home (a time zone not the usual one)


@dataclass(frozen=True)
class TimeLog:
    """What a file says: its stretches, its language, and the rows that could not be read."""
    stretches: List[Stretch]
    language: str
    problems: List[str]


@dataclass(frozen=True)
class Entry:
    """A stretch with the person and project it belongs to."""
    stretch: Stretch
    person: str
    project: Path
    conflict: bool = False  # read from a cloud's conflict copy
    source: Optional[Path] = None


@dataclass(frozen=True)
class Rounding:
    """How the sums are rounded: step in minutes (0: not at all), "up" or "nearest", per stretch
    or per day (and person and project)."""
    step: int = 0
    mode: str = "up"
    per: str = "stretch"

    def __post_init__(self) -> None:
        if self.step not in (0, 5, 10, 15, 30):
            raise ValueError(f"rounding step {self.step!r}: 0, 5, 10, 15 or 30 minutes")
        if self.mode not in ("up", "nearest"):
            raise ValueError(f"rounding mode {self.mode!r}: up or nearest")
        if self.per not in ("stretch", "day"):
            raise ValueError(f"rounding per {self.per!r}: stretch or day")

    def apply(self, duration: timedelta) -> timedelta:
        if not self.step:
            return duration
        step = self.step * 60
        seconds = duration.total_seconds()
        if self.mode == "up":
            steps = math.ceil(seconds / step)
        else:
            steps = math.floor(seconds / step + 0.5)
        return timedelta(seconds=steps * step)


# --- where ---------------------------------------------------------------------------------

def time_file(project: Union[str, Path], person: str) -> Path:
    """A person's file in a project."""
    # Security: the person's name becomes a file name; it must not lead out of the folder.
    name = str(person or "").strip()
    if not name or "/" in name or "\\" in name or name.startswith(".") or "\0" in name:
        raise ValueError(f"not a person's name for a file: {person!r}")
    return Path(project) / TIME_DIR / f"{name}.md"


# --- reading -------------------------------------------------------------------------------

def _cells(line: str) -> List[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [cell.strip().replace("\\|", "|") for cell in _CELL_SPLIT.split(inner)]


def _header(line: str):
    """The columns of a header row and its language, or None when the row is no header."""
    if not line.lstrip().startswith("|"):
        return None
    found = [_COLUMN_OF.get(cell.lower()) for cell in _cells(line)]
    if not found or None in found:
        return None
    columns = [column for column, _language in found]
    if "date" not in columns or "duration" not in columns:
        return None
    # No column has the same name in both languages, so the names tell the language.
    german = sum(1 for _column, language in found if language == "de")
    return columns, ("de" if german * 2 >= len(found) else "en")


def _is_rule(line: str) -> bool:
    return bool(line.strip()) and set(line.strip()) <= set("|-: ")


def _parse_start(text: str):
    if not text:
        return None, None
    match = _START.match(text)
    if not match:
        raise ValueError(text)
    hours, minutes, sign, off_h, off_m = match.groups()
    start = time(int(hours), int(minutes))
    offset = None
    if sign:
        offset = timedelta(hours=int(off_h), minutes=int(off_m))
        if sign == "-":
            offset = -offset
    return start, offset


def _parse_duration(text: str) -> timedelta:
    match = _DURATION.match(text)
    if not match:
        raise ValueError(text)
    return timedelta(hours=int(match.group(1)), minutes=int(match.group(2)))


def _row(columns: Sequence[str], line: str) -> Stretch:
    cells = _cells(line)
    if len(cells) != len(columns):
        raise ValueError(line)
    values = dict(zip(columns, cells))
    kind = _KIND_OF.get(values.get("kind", "auto").lower() or "auto")
    if kind is None:
        raise ValueError(values.get("kind"))
    start, offset = _parse_start(values.get("start", ""))
    return Stretch(day=date.fromisoformat(values["date"]), start=start,
                   duration=_parse_duration(values["duration"]), kind=kind,
                   note=values.get("note", ""), offset=offset)


def _table(lines: Sequence[str]):
    """(header index, columns, language, index after the table's last row), or None."""
    for index, line in enumerate(lines):
        header = _header(line)
        if header is None:
            continue
        end = index + 1
        while end < len(lines) and lines[end].lstrip().startswith("|"):
            end += 1
        return index, header[0], header[1], end
    return None


def parse(text: str) -> TimeLog:
    lines = text.splitlines()
    table = _table(lines)
    if table is None:
        return TimeLog([], "de", [])
    index, columns, language, end = table
    stretches: List[Stretch] = []
    problems: List[str] = []
    for line in lines[index + 1:end]:
        if _is_rule(line):
            continue
        try:
            stretches.append(_row(columns, line))
        except (ValueError, KeyError):
            problems.append(line.strip())
    return TimeLog(stretches, language, problems)


def read(path: Union[str, Path]) -> TimeLog:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return TimeLog([], "de", [])
    return parse(text)


# --- writing -------------------------------------------------------------------------------

def _minutes(duration: timedelta) -> int:
    """Whole minutes for the file, to the nearest (half a minute up): neither gives nor takes,
    rounding for invoices is done in the sums."""
    return max(0, math.floor(duration.total_seconds() / 60 + 0.5))


def _format_duration(duration: timedelta) -> str:
    minutes = _minutes(duration)
    return f"{minutes // 60}:{minutes % 60:02d}"


def _format_start(stretch: Stretch) -> str:
    if stretch.start is None:
        return ""
    text = stretch.start.strftime("%H:%M")
    if stretch.offset is not None:
        minutes = int(stretch.offset.total_seconds() // 60)
        sign = "-" if minutes < 0 else "+"
        text += f"{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"
    return text


def _language(language: str) -> str:
    if language not in LANGUAGES:
        raise ValueError(f"language {language!r}: de or en")
    return language


def _format_row(columns: Sequence[str], language: str, stretch: Stretch) -> str:
    values = {
        "date": stretch.day.isoformat(),
        "start": _format_start(stretch),
        "duration": _format_duration(stretch.duration),
        "kind": KIND_NAMES[language][stretch.kind],
        "note": stretch.note.replace("|", "\\|").replace("\n", " "),
    }
    return "| " + " | ".join(values[column] for column in columns) + " |"


def render(person: str, stretches: Iterable[Stretch], language: str) -> str:
    language = _language(language)
    names = COLUMN_NAMES[language]
    lines = [f"# {TITLES[language]} {person}", "",
             "| " + " | ".join(names[column] for column in COLUMNS) + " |",
             "|" + "---|" * len(COLUMNS)]
    lines += [_format_row(COLUMNS, language, stretch) for stretch in stretches]
    return "\n".join(lines) + "\n"


def add(project: Union[str, Path], person: str, stretch: Stretch, *, language: str) -> Path:
    """Add a stretch at the end of the person's table; a new file is begun in `language`, an
    existing one keeps its language, its column order and everything written around the table."""
    return add_to_file(time_file(project, person), person, stretch, language=language)


def _last_row(lines: Sequence[str], index: int, end: int, columns: Sequence[str]) -> Optional[Stretch]:
    """The table's last row, when it is a readable one (a row written by hand stays as it is)."""
    if end - 1 <= index or _is_rule(lines[end - 1]):
        return None
    try:
        return _row(columns, lines[end - 1])
    except (ValueError, KeyError):
        return None


def add_to_file(path: Path, person: str, stretch: Stretch, *, language: str, atomic: bool = True) -> Path:
    """add() into a given file (the clock in its sandbox reaches the projects through its drive).
    atomic: written beside it and swapped in; without, the file itself is written anew - on the
    drive the person may write their own file ({Self}.md), not a helper file beside it."""
    if stretch.kind not in KINDS:
        raise ValueError(f"kind {stretch.kind!r}")
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    lines = text.splitlines()
    table = _table(lines)
    if table is None:
        addition = render(person, [stretch], language)
        text = (text.rstrip("\n") + "\n\n" + addition) if text.strip() else addition
    else:
        index, columns, file_language, end = table
        last = _last_row(lines, index, end, columns)
        joined = join_gaps([last, stretch]) if last is not None else []
        if len(joined) == 1:
            # Right after the last row (a glance elsewhere, stop and start): one row, not two (Z4).
            lines[end - 1] = _format_row(columns, file_language, joined[0])
        else:
            lines.insert(end, _format_row(columns, file_language, stretch))
        text = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not atomic:
        path.write_text(text, encoding="utf-8")
        return path
    temporary = path.with_name(f".{path.name}.writing")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)
    return path


def _rewrite(path: Path, old: Stretch, new: Optional[Stretch]) -> bool:
    """Replace (new) or take away (None) the first row equal to old; everything else in the file
    stays. Written anew and swapped in. False when there is no such row."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    lines = text.splitlines()
    table = _table(lines)
    if table is None:
        return False
    index, columns, language, end = table
    for at in range(index + 1, end):
        if _is_rule(lines[at]):
            continue
        try:
            stretch = _row(columns, lines[at])
        except (ValueError, KeyError):
            continue
        if stretch != old:
            continue
        if new is None:
            del lines[at]
        else:
            if new.kind not in KINDS:
                raise ValueError(f"kind {new.kind!r}")
            lines[at] = _format_row(columns, language, new)
        temporary = path.with_name(f".{path.name}.writing")
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(temporary, path)
        return True
    return False


def change(path: Union[str, Path], old: Stretch, new: Stretch) -> bool:
    """Correct a row (the time screen, with the person's own rights)."""
    return _rewrite(Path(path), old, new)


def remove(path: Union[str, Path], stretch: Stretch) -> bool:
    """Take a row away (the time screen, with the person's own rights)."""
    return _rewrite(Path(path), stretch, None)


# --- the day and the gaps ------------------------------------------------------------------

def split_days(start: datetime, duration: timedelta, *, kind: str, note: str = "",
               offset: Optional[timedelta] = None) -> List[Stretch]:
    """A stretch that runs over midnight as one stretch per day."""
    parts: List[Stretch] = []
    left = duration
    current = start
    while True:
        midnight = datetime.combine(current.date() + timedelta(days=1), time(0, 0))
        if current.tzinfo is not None:
            midnight = midnight.astimezone()  # the real midnight: a day may have 23 or 25 hours
        piece = min(left, midnight - current)
        parts.append(Stretch(day=current.date(), start=current.time(), duration=piece,
                             kind=kind, note=note, offset=offset))
        left -= piece
        if left <= timedelta(0):
            return parts
        current = midnight


def _begin(stretch: Stretch) -> datetime:
    return datetime.combine(stretch.day, stretch.start or time(0, 0))


def join_gaps(stretches: Iterable[Stretch], gap: timedelta = timedelta(minutes=1)) -> List[Stretch]:
    """Stretches of the same day, kind and note that follow within `gap` become one."""
    ordered = sorted(stretches, key=lambda s: (s.day, s.start is None, s.start or time(0, 0)))
    joined: List[Stretch] = []
    for stretch in ordered:
        if joined:
            last = joined[-1]
            if (last.start is not None and stretch.start is not None and last.day == stretch.day
                    and (last.kind, last.note, last.offset) == (stretch.kind, stretch.note, stretch.offset)):
                end = _begin(last) + last.duration
                if _begin(stretch) - end <= gap:
                    new_end = max(end, _begin(stretch) + stretch.duration)
                    joined[-1] = replace(last, duration=new_end - _begin(last))
                    continue
        joined.append(stretch)
    return joined


# --- parents and children ------------------------------------------------------------------

def _is_project(folder: Path) -> bool:
    return (folder / META_DIR / "Project.md").is_file()


def _projects(project: Path, children: bool) -> List[Path]:
    found = [project]
    if not children:
        return found
    for current, dirs, _files in os.walk(project):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        folder = Path(current)
        if folder != project and _is_project(folder):
            found.append(folder)
    return found


def _files(project: Path) -> List[tuple]:
    """(path, person, conflict) of the time files of one project, originals first."""
    folder = project / TIME_DIR
    try:
        names = [p for p in folder.iterdir() if p.is_file() and p.suffix == ".md"
                 and not p.name.startswith(".")]
    except OSError:
        return []
    files = []
    for path in names:
        match = _CONFLICT.match(path.stem)
        files.append((path, match.group("person") if match else path.stem, bool(match)))
    return sorted(files, key=lambda f: (f[2], f[0].name.lower()))


def time_files(project: Union[str, Path], *, children: bool = True) -> List[Path]:
    """The time files of a project (and with `children` of all below it), conflict copies too."""
    return [path for folder in _projects(Path(project), children) for path, _p, _c in _files(folder)]


def collect(project: Union[str, Path], *, children: bool = True) -> List[Entry]:
    """The time of a project: its own, and with `children` that of all projects below it."""
    entries: List[Entry] = []
    for folder in _projects(Path(project), children):
        for path, person, conflict in _files(folder):
            for stretch in read(path).stretches:
                entries.append(Entry(stretch=stretch, person=person, project=folder,
                                     conflict=conflict, source=path))
    return entries


def conflicts(project: Union[str, Path]) -> List[Path]:
    """The cloud's conflict copies in a project's own time folder."""
    return [path for path, _person, conflict in _files(Path(project)) if conflict]


def only(entries: Iterable[Entry], *, person: Optional[str] = None, since: Optional[date] = None,
         until: Optional[date] = None, kinds: Optional[Set[str]] = None) -> List[Entry]:
    """The entries of one person, a period (both days included) and some kinds."""
    return [e for e in entries
            if (person is None or e.person == person)
            and (since is None or e.stretch.day >= since)
            and (until is None or e.stretch.day <= until)
            and (kinds is None or e.stretch.kind in kinds)]


def total(entries: Iterable[Entry], rounding: Optional[Rounding] = None) -> timedelta:
    rounding = rounding or Rounding()
    entries = list(entries)
    if rounding.per == "stretch":
        return sum((rounding.apply(e.stretch.duration) for e in entries), timedelta(0))
    days: Dict[tuple, timedelta] = {}
    for e in entries:
        key = (e.stretch.day, e.person, e.project)
        days[key] = days.get(key, timedelta(0)) + e.stretch.duration
    return sum((rounding.apply(d) for d in days.values()), timedelta(0))


def sums(entries: Iterable[Entry], *, by: str, rounding: Optional[Rounding] = None) -> Dict:
    """Sums per project or per person, in the order they first appear."""
    if by not in ("project", "person"):
        raise ValueError(f"sums by {by!r}: project or person")
    groups: Dict = {}
    for e in entries:
        groups.setdefault(e.project if by == "project" else e.person, []).append(e)
    return {key: total(group, rounding) for key, group in groups.items()}
