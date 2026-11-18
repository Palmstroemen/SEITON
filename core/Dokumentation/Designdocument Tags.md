# **SEITON Tags - Design Document (Draft)**

## **1. Purpose**
Tags add human-readable meaning to files and folders. They should be explicit words, not just colors, and can optionally carry color or icon hints.

---

## **2. Core Principles**
- Tags are always text labels (self-explanatory).
- Colors are optional and must never replace the label.
- Icons are optional and can reinforce meaning.
- Tags may optionally carry numeric values for classification (e.g., 0–100).

---

## **3. Tag Format**
A project suggests its tags in `.seiton/Tags.md`: the heading `# Tags`, then one tag per
line with `#` in front and no space after it (`core/tags.py`, `hash_line_tags`):

```
# Tags
#wichtig
#dringend
#in Arbeit
#erledigt
```

- A line `# …` (hashes, then a space) is a Markdown heading, not a tag.
- Other lines are ignored. Each tag counts once; they are shown sorted.
- Like other configs, `Tags.md` inherits: a subproject without one suggests the tags of the
  nearest parent project that has one.
- `Tags.md` is read only as its own file, not as a `# Tags` section of a `Config.md`.

Open (not built): a color and an icon per tag. An earlier draft wrote them as
`wichtig, rot, !`; the code does not read that form (such a line gives no tag).

---

## **4. Multi-Word Tags**
Multi-word labels are allowed and kept as-is:
- `in Arbeit`
- `zu prüfen`

No forced underscore format is required.

---

## **5. Storage**
Primary storage uses filesystem metadata:
- macOS/Linux: extended attributes (xattr)
- Windows/NTFS: to be evaluated

File tags live in the xattr `user.seiton.tags` (until November 2026 `user.myos.tags`; old
ones are moved over by `cli/migrate_name.py`), as a comma-separated list, a value written as
`tag=value` (`mytag set`). On filesystems without xattr there are no file tags; there is no
fallback. `.seiton/Tags.md` holds only the suggested tags (see 3), not the tags of files.

Folder tags live in a sidecar file on the tagged folder itself:
- `.seiton/myTags.md`, one `#tag` per line (Scope writes it; without tags it is removed)
- this sidecar does **not** make a folder a SEITON project (`Project.md` remains the project marker)

---

## **6. Open Questions**
- icon naming convention (emoji vs icon id)
- icon set selection and theming (global preference, not per project)
- whether tags can be scoped by project or global
- whether tags apply to folders, files, or both
- how numeric tag values are stored and visualized (e.g., Eisenhower/Disney quadrants, 2D charts)
- NTFS metadata mapping strategy

---

## **7. Summary**
Tags are text-first labels with optional color and icon hints. They remain readable without UI decoration and align with the SEITON “self-explanatory” principle.

---

## **8. MVP Checkpoint**
- File tags via xattr are the primary shipped behavior.
- Folder tags via the sidecar `.seiton/myTags.md` are read and written by Scope.
- The project's suggested tags (`.seiton/Tags.md`) are offered in Scope; the Nextcloud sync
  creates them as system tags there (`core/nextcloud_sync.py`).
- Scope's tag bar has three sections, each tag shown once in the first that applies:
  **This folder** (its own sidecar tags), **Subfolders** (tags of the listed subfolders,
  only while folders are shown) and **File tags**. A click filters the listing (2026-10-21).
- Reason: keep MVP focused and avoid premature divergence from Obsidian’s tag model (which is primarily note-centric, not native folder-tag-centric).
