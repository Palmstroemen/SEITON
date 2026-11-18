# acl_nextcloud.py - a project's ACLs as Nextcloud Team folder rules ("advanced permissions")
#
# ACLs.md stays the source; this only computes what Nextcloud should hold (plan) and has no
# network. Findings behind it (ProjectLogbook, test of 2026-11-07):
# - Nextcloud's rules are per path and per user or group, inherited, and every permission
#   bit inherits on its own (mask). A rule here fixes every bit, so the nearest rule wins as
#   in MyOS.
# - Rules are per person (account), not per group: creating groups needs a Nextcloud admin.
#   A person's rights are the union of their roles, computed by ACLPolicy as everywhere.
# - Nextcloud needs read on every parent folder. Who has rights only deep down gets read on
#   the way there, and every other entry on the way is locked (else it would inherit read).
#   Security: entries created later in such a folder would inherit that read. So these
#   rules are marked - they leave share to be inherited (mask 15; share is denied at the
#   root for everyone, so the rights are the same) - and the server app myos_acl
#   (cloud/nextcloud) locks new entries of a folder with marked rules right away. Every
#   folder on the way gets a marked rule of its own, also where it would inherit the same.
# - Without a rule the Team folder's own permissions apply: everyone gets a rule at the root.

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from core.acl import RIGHTS_FILES, ACLPolicy, _nearest_rules, _normalize_path, _rule_base
from core.brand import META_DIR

# MyOS right -> Nextcloud permissions. execute and change have none; share is never given
# (it would pass files on beyond ACLs.md).
NEXTCLOUD_PERMISSIONS = ("read", "write", "create", "delete", "share")
_MAP = {"read": {"read"}, "write": {"write", "create"}, "delete": {"delete"}}
_ALL_RIGHTS = {"read", "write", "execute", "change", "delete"}


@dataclass(frozen=True)
class PlannedRule:
    path: str  # project-relative, "/" for the root
    kind: str  # "user" | "group"
    account: str  # Nextcloud user or group id
    allowed: FrozenSet[str]  # Nextcloud permissions; all others are denied
    traverse: bool = False  # read only to pass on the way down (marked, see above)


@dataclass
class Plan:
    rules: List[PlannedRule] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def local_tree(root: Path) -> Tuple[Callable[[str], bool], Callable[[str], List[str]]]:
    """exists(path) and children(path) for project-relative paths, from the local folder."""
    root = Path(root)

    def _disk(path: str) -> Path:
        return root.joinpath(*[part for part in path.split("/") if part])

    def exists(path: str) -> bool:
        return os.path.lexists(_disk(path))

    def children(path: str) -> List[str]:
        try:
            return sorted(entry.name for entry in os.scandir(_disk(path)) if entry.is_dir() or entry.is_file())
        except OSError:
            return []

    return exists, children


def read_nextcloud_md(path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    A project's .MyOS/Nextcloud.md: (settings of "# Nextcloud", lower-case keys, e.g. url,
    folder, group; people of "# Accounts", lower-case person -> account, "Anna Huber: anna.h").
    """
    sections: Dict[str, Dict[str, str]] = {"nextcloud": {}, "accounts": {}}
    section = None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return {}, {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip().lower()
        elif section in sections and ":" in stripped:
            key, _, value = stripped.lstrip("-* ").partition(":")
            if key.strip() and value.strip():
                sections[section][key.strip().lower()] = value.strip()
    return sections["nextcloud"], sections["accounts"]


def plan(
    policy: ACLPolicy,
    accounts: Dict[str, str],
    exists: Callable[[str], bool],
    children: Callable[[str], List[str]],
    base_groups: Iterable[str] = (),
    readable: Iterable[Tuple[str, Optional[str]]] = (),
    protected: Iterable[str] = (),
    apart: Iterable[Tuple[str, ACLPolicy]] = (),
) -> Plan:
    """
    The Nextcloud rules for policy (ACLPolicy.for_tree of the project, whose root is the
    Team folder's root): per person with an account, rules only where their rights change.
    base_groups, the groups the Team folder is given to, get a rule without rights at the
    root, so only the people's own rules let anyone in. readable: (path, reader) pairs - path
    (with all below, up to a deeper pair) may be read besides by who may read reader, by
    everyone with rights in the project when reader is None: the embryos the Files app shows,
    each for who may read where it is born (core/cloud_embryos.readable_paths); those not
    there yet are skipped. protected: the rights and sync
    files of .MyOS folders (rights_files): only who may change the rights there (change on that
    .MyOS/ACLs.md) may write them, everyone else keeps at most read. apart: the subprojects
    with an ACLs.md of their own (core.acl.rules_apart): there their rules decide, not policy's.
    """
    result = Plan()
    # Each part of the tree with the rules that govern it: the project, and every subproject
    # with an ACLs.md of its own (its rule paths relative to it).
    scopes = [("/", policy, _mappable_rules(policy, result.notes))]
    scopes += [(prefix, sub, _mappable_rules(sub, result.notes)) for prefix, sub in apart]
    copied = [rule for _prefix, scope, rules in scopes
              for rule in [*(r for role_rules in rules.values() for r in role_rules), *scope.everyone]]
    if any("change" in rule.rights or "*" in rule.rights for rule in copied):
        result.notes.append("change is not copied: who may manage the rules is set for the whole Team folder")
    missing: Set[str] = set()
    for group in base_groups:
        result.rules.append(PlannedRule("/", "group", group, frozenset()))
    people = sorted({person for _prefix, scope, _rules in scopes for person in scope.users})
    for person in people:
        account = accounts.get(person)
        if not account:
            named = next(scope for _prefix, scope, _rules in scopes if person in scope.users)
            result.notes.append(f"{named.display_name(person)} has no Nextcloud account in # Accounts: no rules")
            continue
        # A person's rule lists per part of the tree: one per role, and the "## Everyone"
        # rules with {Self} as this person (C5) - as at home, the person gets their union.
        mine = [(prefix, [rules.get(role, []) for role in scope.users.get(person, ())]
                 + [[rule for rule in scope.everyone_rules(person) if _mappable(rule.path)]])
                for prefix, scope, rules in scopes]
        for path, allowed, way in _person_rules(mine, exists, children, missing, list(readable), list(protected)):
            result.rules.append(PlannedRule(path, "user", account, allowed, traverse=way))
    for path in sorted(missing):
        result.notes.append(f"{path} is not there yet: its rules follow when it exists")
    return result


# In a .MyOS folder: what manages the rights and the sync (ACLs.md as in MyOS, where change
# grants writing it; its history, the cloud settings, the embryos seiton acl sync uploads).


def rights_files(paths: Iterable[str]) -> List[str]:
    """The RIGHTS_FILES among paths (project-relative): entries right inside a .MyOS folder."""
    found = []
    for path in paths:
        parent, _, name = path.rpartition("/")
        if name in RIGHTS_FILES and parent.rpartition("/")[2] == META_DIR:
            found.append(path)
    return sorted(found)


def _mappable(path: str) -> bool:
    """Whether Nextcloud can hold a rule on path: a plain path, /folder/** or /*."""
    plain = path[:-3] if path.endswith("/**") else path
    return path == "/*" or not re.search(r"[*?\[]", plain)


def _mappable_rules(policy: ACLPolicy, notes: List[str]) -> Dict[str, list]:
    """Rules per role that Nextcloud can hold (_mappable); the others with a note, also those
    of "## Everyone" (kept apart: their {Self} is filled in per person in plan)."""
    kept: Dict[str, list] = {}
    for role, role_rules in sorted(policy.permissions.items()):
        for rule in role_rules:
            if _mappable(rule.path):
                kept.setdefault(role, []).append(rule)
            else:
                notes.append(f"{policy.display_name(role)}: {rule.path} is a pattern Nextcloud cannot hold: left out")
    for rule in policy.everyone:
        if not _mappable(rule.path):
            notes.append(f"Everyone: {rule.path} is a pattern Nextcloud cannot hold: left out")
    return kept


def _nextcloud(our_rights: Iterable[str]) -> FrozenSet[str]:
    rights = set(our_rights)
    if "*" in rights:
        rights = set(_ALL_RIGHTS)
    return frozenset(p for right in rights for p in _MAP.get(right, ()))


def _parents(path: str) -> List[str]:
    """Strict ancestors of path, root first."""
    parts = [part for part in path.split("/") if part]
    return ["/" + "/".join(parts[:depth]) if depth else "/" for depth in range(len(parts))]


def _child(path: str, name: str) -> str:
    return ("" if path == "/" else path) + "/" + name


def _below(path: str, top: str) -> bool:
    return path == top or path.startswith(top + "/")


def _within(prefix: str, path: str) -> str:
    """path ("/" for the root) as seen from prefix, the root of a part of the tree."""
    if prefix == "/":
        return path
    rest = path[len(prefix):]
    return rest if rest else "/"


def _person_rules(
    scopes: List[Tuple[str, List[list]]], exists, children, missing: Set[str],
    readable: List[Tuple[str, Optional[str]]] = (), protected: List[str] = (),
) -> List[Tuple[str, FrozenSet[str], bool]]:
    """scopes: (prefix, the rules of each of the person's roles there) - "/" the project, then
    the subprojects with rules of their own; the deepest prefix above a path decides it."""
    opened: Dict[str, bool] = {}  # readable path -> read for this person, once they have rights at all

    def own_rights(path: str) -> Set[str]:
        prefix, role_rules = max(((p, r) for p, r in scopes if _below(path, p) or p == "/"), key=lambda s: len(s[0]))
        key = _normalize_path(_within(prefix, path))
        found: Set[str] = set()
        for rules in role_rules:
            for rule in _nearest_rules(rules, key):
                found |= set(rule.rights)
        return found

    def our_rights(path: str) -> Set[str]:
        found = own_rights(path)
        tops = [top for top in opened if _below(path, top)]
        if tops and opened[max(tops, key=len)]:  # the deepest pair decides
            found.add("read")
        return found

    def may_change(path: str) -> bool:
        acls = path.rsplit(f"/{META_DIR}/", 1)[0] + f"/{META_DIR}/ACLs.md"
        return bool({"change", "*"} & our_rights(acls))

    def rights(path: str) -> FrozenSet[str]:
        allowed = _nextcloud(our_rights(path))
        if any(_below(path, top) and not may_change(top) for top in protected):
            allowed = allowed & {"read"}
        return allowed

    bases = {"/"}
    for prefix, role_rules in scopes:
        if prefix != "/" and exists(prefix):
            bases.add(prefix)  # where other rules begin
        for rules in role_rules:
            for rule in rules:
                base = _rule_base(rule.path) or "/"
                base = base if prefix == "/" else (prefix if base == "/" else prefix + base)
                if exists(base):
                    bases.add(base)
                else:
                    missing.add(base)
    if any(rights(base) for base in bases):
        for path, reader in readable:
            if exists(path):
                opened[path] = reader is None or bool({"read", "*"} & own_rights(reader))
        bases.update(opened)
        bases.update(path for path in protected if exists(path))
    granted = [base for base in bases if rights(base)]
    walk = set(bases)
    for base in bases:
        walk.update(_parents(base))
    traverse = {p for base in granted for p in _parents(base) if "read" not in rights(p)}
    for path in traverse:
        walk.update(_child(path, name) for name in children(path))

    planned: List[Tuple[str, FrozenSet[str], bool]] = []
    target: Dict[str, FrozenSet[str]] = {}
    for path in sorted(walk, key=lambda p: (p.count("/") if p != "/" else 0, p)):
        own = rights(path) | ({"read"} if path in traverse else set())
        target[path] = frozenset(own)
        parent = _parents(path)[-1] if path != "/" else None
        # Below a rule on the way every entry gets its own: the server app locks what is new there.
        if parent is None or path in traverse or parent in traverse or target[path] != target[parent]:
            planned.append((path, target[path], path in traverse))
    return planned


# Nextcloud's permission bits; a planned rule fixes all of them, a rule on the way all
# but share.
BITS = {"read": 1, "write": 2, "create": 4, "delete": 8, "share": 16}
FULL_MASK = 31
TRAVERSE_MASK = FULL_MASK & ~BITS["share"]


def mask_of(rule: PlannedRule) -> int:
    return TRAVERSE_MASK if rule.traverse else FULL_MASK


def bits(allowed: Iterable[str]) -> int:
    return sum(BITS[p] for p in set(allowed))


@dataclass(frozen=True)
class Change:
    path: str
    kind: str
    account: str
    before: Optional[object]  # the rule Nextcloud holds (core.nextcloud_dav.ExistingRule), None: new
    after: Optional[FrozenSet[str]]  # the planned permissions, None: the rule goes


def diff(planned: Iterable[PlannedRule], tree) -> List[Change]:
    """What would change in Nextcloud (tree: core.nextcloud_dav tree) to hold the planned
    rules; rules not planned (not from ACLs.md) would go."""
    existing = {(path, r.kind, r.account): r for path, entry in tree.items() for r in entry.rules}
    wanted = {(r.path, r.kind, r.account): r for r in planned}
    changes = []
    for key in sorted(set(existing) | set(wanted)):
        before, rule = existing.get(key), wanted.get(key)
        if before is not None and rule is not None and (before.mask, before.permissions) == (mask_of(rule), bits(rule.allowed)):
            continue
        changes.append(Change(*key, before=before, after=None if rule is None else rule.allowed))
    return changes


def updates(planned: Iterable[PlannedRule], changes: Iterable[Change]) -> List[Tuple[str, List[PlannedRule]]]:
    """
    What to send for changes: Nextcloud replaces all rules of a path at once, so per changed
    path its whole planned list (empty: all its rules go). Deepest paths first, so the
    account that syncs keeps its way down until the parents are done.
    """
    planned = list(planned)
    paths = {change.path for change in changes}
    ordered = sorted(paths, key=lambda p: (-(p.count("/") if p != "/" else 0), p))
    return [(path, [rule for rule in planned if rule.path == path]) for path in ordered]
