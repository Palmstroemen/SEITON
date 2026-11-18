# SEITON Recents - Design Document (Fragment)

Status (checked 2026-11-18): this file has been a fragment since its first commit
(2026-02-21): sections 1-8 (the `Recent.md` format the notes below interpret) are missing.
Nothing of the recents model is built: there is no `Recent.md` and no `.cache/recent.*`.
What exists: the key `RecentPolicy` in `Desk.md`, which is read but does nothing yet (see
"Designdocument Desk.md", 5), and the option `myls --recent=N`, whose method is still an
empty stub (prints nothing).

Interpretation notes:

- `Scope`: `project` (MVP default), later `perspective`.
- `Strategy`:
  - `os-delta` (MVP baseline),
  - `event-first` (future hybrid; SEITON events preferred, OS delta fallback).
- `Limit`: max entries shown/stored in active view.
- Include/exclude rules are optional and can be inherited.

---

## 9. Relationship to Desk.md

Recents should not be embedded into `Desk.md` runtime state.

`Desk.md` may reference how recents are displayed (UI preference), but activity data should remain in dedicated recents storage.

Suggested boundary:

- `Desk.md`: visual/environment profile.
- `Recent.md`: recents policy.
- `.cache/recent.*`: recents runtime data.

---

## 10. Future Evolution (Post-MVP)

1. Add direct SEITON activity events (PostFix/Scope/CLI open/save) for higher precision.
2. Use OS recent list as fallback/import source only.
3. Add optional confidence scoring (`source_weight`, `session_match`).
4. Add perspective-aware recents (`scope: perspective`).
5. Support desktop-environment adapters (KDE, GNOME) without changing SEITON recents model.

---

## 11. Security and Privacy Considerations

- Process recents as data, never as executable instructions.
- Restrict to local file paths by default.
- Do not expose entries beyond current ACL/project boundaries.
- Allow user to clear project recents quickly.
- Log parse/import failures safely (no crashes on malformed external entries).

---

## 12. Summary

MVP recents in SEITON should use a practical snapshot-delta approach against OS recents, filtered strictly to project scope and merged into a project-local data store.

This provides immediate value with low complexity while preserving a clean migration path toward precise event-based recents later.