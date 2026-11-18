---
window_width_px: 900
window_height_px: 650
window_x_permille: 78
window_y_permille: 44
note_style: cloud
---
# SEITON Design Document

Seiton (整頓) is Japanese for order: a place for everything, and everything in its place. That is exactly the idea of SEITON: an order that is easy to understand, one that anyone can grasp and use right away.

Until November 2026 the project was called MyOS; in some places that name still appears.

## Purpose
This document is the practical entry point for contributors. It explains:
- what SEITON is trying to achieve,
- how the current codebase is structured,
- which design principles should guide new changes.

The goal is fast orientation and consistent decisions.

## Product Direction
SEITON is a project-centric environment. It treats project context as a first-class concept rather than an afterthought on top of generic folders.

Key ideas:
- Human workflows are project-shaped, not file-shaped.
- Structure should evolve with usage, not be fully fixed upfront.
- Existing Unix tooling should continue to work.
- System behavior should be understandable and recoverable.

## Core Design Principles

### 1) Progressive Disclosure
Start simple. Reveal complexity only when needed.

Implications:
- New users get low cognitive load.
- Power users can still access advanced behavior.
- UI and filesystem views should avoid unnecessary noise.

### 2) Explicit Over Magical
Automation is welcome, but behavior must be predictable.

Implications:
- Deterministic transforms.
- Clear naming for generated/derived structures.
- Avoid hidden side effects across unrelated components.

### 3) Local-First and File-First
Project state lives in files that can be read, versioned, and audited.

Implications:
- Prefer Markdown/YAML/JSON over opaque storage.
- Keep metadata colocated with projects when practical.
- Preserve interoperability with external tools.

### 4) Backward-Compatible Evolution
Refactors should preserve behavior unless a change is intentional and documented.

Implications:
- Small, testable steps.
- Migration paths when formats or APIs change.
- Avoid "big bang" rewrites.

### 5) Modular Boundaries
Organize code by responsibilities, not by convenience.

Implications:
- UI composition, theme logic, tag context logic, and editor behavior should be separable.
- Shared logic should move to modules once patterns stabilize.
- Main entrypoints should orchestrate, not contain most logic.

## Current Architecture Overview

SEITON is the core with its tools, and a few pieces from the workshop beside it. Each part has
its own design document; this one only shows how they fit together.

| Part | What it is | Design documents |
|---|---|---|
| `core/` | the logic: projects, templates and embryos, ACLs, tags, filters, perspectives, trash, export/import, time tracking, colours; no Qt | `core/Dokumentation/` (one `Designdocument X.md` per topic) |
| `cli/` | the CLI tools (myls, myproject, mytag, myacl, myedit, myimport, myexport, myfilter) on the core | `cli/Dokumentationen/CLI.md` |
| `daemon/` | the session daemon: the lens shared by the programs, the FUSE drive "Perspektiven", the clock | `core/Dokumentation/Designdocument Perspectives.md`, `… Perspective Resolver MVP.md`, `… Time.md` |
| `apps/Scope/` | the file browser (QML) with its settings on the back | `apps/Scope/README.md`, `apps/Scope/Designdocument Setup.md`, `apps/Scope/Colour inventory.md` |
| `apps/Headline/` | the line at the top edge of the screen; the minimal view M of Scope as a tool of its own | `apps/Scope/Designdocument Headline.md` |
| `apps/Time/` | the screen of the time tracking | `core/Dokumentation/Designdocument Time.md` |
| `cloud/` | Nextcloud: the app `seiton`, the core as a service beside it | `cloud/nextcloud/Designdocument SEITON Core Service.md`, `cloud/nextcloud/README.md` |
| `installer/` | installing for one user (`install.sh`) | `installer/thumbnailer.md` (Markdown previews) |
| `examples/PostFix/` (workshop) | the Markdown editor, editing like Obsidian | `examples/PostFix/Designdokument.md` |
| `examples/SunTree/` (workshop) | the folder fan for quick dropping | `examples/SunTree/Designdocument Krone.md` |

The rule between them: logic goes into `core/` (testable without a screen), the programs only
show it and hand on what the user does. The programs talk to each other through the session
daemon (`daemon/`), never directly.

## Data and Configuration Model

### Project-Level
- A project is a folder with `.seiton/Project.md`; everything SEITON keeps about it lies in its
  `.seiton` folder (`core/Dokumentation/Designdocument Projects.md`).
- `.seiton/Tags.md` is used as project scope tag filter/list.
- New document tags can be synced into scope tags.
- Scope tag changes can trigger propagation hooks through `core.project` signaling.
- `.seiton/ACLs.md` holds the project's rights. Why the plural, although it is one file (asked
  2026-11-15): technically every object has its own ACL (every file and folder in Linux and
  Windows, every path with rules in Nextcloud), and this file describes the ACLs of many
  folders at once; SEITON also turns it into rules per path. So the name stays. If it is ever
  renamed, then to a name a layperson understands (`Rights.md`, `Access.md`), not for one
  letter. Old projects would need a time in which both names are read, as with MyOS.

### User-Level
- Settings in `~/.config/seiton/seiton.conf` (`core/settings.py`), colour schemes beside them in
  `~/.config/seiton/schemes/`, templates in `~/.seiton/Templates`.

### Document-Level, Vault-Level
- Front matter, colour definitions and the Obsidian-compatible tag colour registry are PostFix's:
  `examples/PostFix/Designdokument.md`.

## Contributor Guidance

### Where to Put New Logic
- Rules, file formats, anything that decides: `core/`, with a test in `core/tests/unit`.
- What the user sees: the program's QML and its backend (`apps/Scope/Scope.py`, `apps/Headline/`, …), which
  only call the core.
- Between programs: the session daemon (`daemon/`).
- Inside PostFix: see its own design document.
- UI strings are English in the code; German comes from the `*_de.ts` files
  (`scripts/update_translations.py`).

### What Not to Do
- Do not re-centralize large feature logic in an entry point (`main.qml`, `main.py`).
- Do not mix parsing/business logic into pure UI widget classes.
- Do not break existing save/sync flows without explicit migration notes.

### Safe Change Pattern
1. Look first, then write a test that fails (TDD).
2. Make one focused change.
3. Run the tests from the repository root (`python3 -m pytest`, or one folder) and a minimal smoke test.
4. Commit in small increments; only then proceed to the next step.

This is especially important because large PySide refactors can create transient crash-prone states.

## Scope Drag-and-Drop Status

Current Scope behavior is intentionally conservative and safety-oriented.

### Implemented
- Multi-selection in `FilesPanel`:
  - `Ctrl+Click` toggles item selection.
  - Rectangle selection (marquee) on free panel area.
- Batch drag payloads from current selection.
- Drop targets in Scope folder views and file panel folders.
- Batch move backend with structured result reporting:
  - `moved`
  - `skipped`
  - `errors`
- Safety prompt only when at least one moved item is a folder.
- Human-readable post-move report messages (English).

### Interaction Policy
- File-only moves execute directly (no confirmation dialog).
- Folder-involved moves require confirmation.
- Moving into invalid targets is blocked and reported.

### Follow-up Refinement Targets
- Optional OR/AND toggle visibility polish in the tag rail if needed.
- Additional UI affordances for move progress and undo strategy.
- Broader integration tests for mixed source payloads (folders + files).

## Minimal Smoke Test Checklist
- Start Scope on test data (not on one's own projects): rows, embryos, a drop on an embryo bears it.
- Put a lens on (double click on a SEITON folder), move to another project, take it off.
- The Headline shows the project and its standard folders; the clock counts.
- Open a note from Scope (PostFix, or the editor set on Scope's back).
- Verify startup still feels fast.

## Design Quality Bar
A change is "good enough" when:
- behavior is at least as stable as before,
- module boundaries are clearer after the change,
- startup and interaction latency do not regress noticeably,
- a new contributor can find the right place to modify behavior in under a few minutes.

## Ideas from FreeDMS (not decided)
FreeDMS (https://github.com/Palmstroemen/FreeDMS, 2016) was the first attempt at SEITON, built
from shell scripts and `.desktop` buttons placed in the folders. Much of it lives on in SEITON:
standard folders, embryos instead of empty folders, X-ray, folders as lenses for roles and
programs, project-specific desktops (Desk). The ideas below are not in SEITON yet. They are
collected here to think about, not to build (2026-11-15).

### 1) A folder says what belongs in it
In FreeDMS every standard folder had a `Read.me`: what goes here, what does not, and where it
goes instead (for example, `_finance` said that private time sheets and expenses go into the
person's own folder in `_team`). Hierarchies are never quite consistent: do insurances belong
to finance or to legal? The answer stood where the question comes up.
- In SEITON: a short `About.md` in the template folder's `.seiton` (beside its icons), not a
  visible file in every folder. It would be inherited like the folder itself.
- Where it is shown: as a tooltip on folders and embryos in Scope and SunTree. It matters most
  at the moment of dropping something, before the folder exists.
- "Not here, but in …" could become a link that leads straight to the right folder.

### 2) Ending a project: Keep and archive
FreeDMS had `_keep_this` folders throughout the project. Whatever was worth keeping (the best
pictures, a finding, a piece of documentation) was gathered there, during the project or just
before its "funeral". ARCHIVE THIS PROJECT copied everything kept into the parent project's
`_check_this` folder to be looked through, packed the project into a zip and removed it.
- SEITON has export (zip), trash and "a project becomes a folder again", but no end of a
  project. A project's life has no last step yet.
- In SEITON, "keep" could be a tag instead of extra folders. When a project is closed, what is
  tagged keep goes to the parent project for review. The rest is packed, with its `.seiton` and
  ACL history, into the parent's archive (where? `9_Dokumentation/95_Archiv`?).
- Open: whether an archive can still be searched and seen through lenses, whether it can be
  unpacked to come back to life, and what happens to the rules on Nextcloud.

### 3) The admin's place: tools and a watch list
FreeDMS put the admin's tools into `_admin/_tools`: create a subproject, add or remove folders,
manage the team, find files, archive. Most of them were workarounds for a file browser that did
not know about projects; in SEITON they belong in Scope (P button, embryos) and in the CLI.
Two ideas remain:
- `_check_this`: the admin collected links to things to check regularly (time sheets, reports,
  status). In SEITON this could be a tag or a saved filter shown in `0_Admin`, without links that
  break.
- `0_Admin` as the cockpit: the project's settings (rights, templates, cloud) where a person
  looks for them, as files or a view, instead of only hidden in `.seiton`.

### 4) Vertical communication between projects
FreeDMS saw a company as a project with departments as subprojects. Reports go up, notices go
down, one level at a time. In `_admin` there were two folders:
- `_communication_to_subadmins`: seen by the admins of this project and of its direct
  subprojects, not by their teams;
- `_communication_to_subprojects`: seen by all members of the direct subprojects.

In every subproject a link `_from_top_project` pointed there. Nothing passed further down by
itself: each admin decided what to pass on to the next level.
- In SEITON this is a question of rights plus a view, not of links (links do not survive
  Nextcloud). A folder in the parent's `3_Kommunikation` is readable by the people of the direct
  subprojects. The subproject shows it in its own `3_Kommunikation` as "from the parent
  project", faint like an embryo.
- For this, `ACLs.md` would need roles like "people of the direct subprojects" or "admins of the
  direct subprojects", which it does not have today.

### 5) Team: a folder per person and roles across levels
- From the TEAM file, FreeDMS created a folder in `_team` for each person, with `_my_admin`
  (time sheets, expenses, contracts, payments). Only that person and the admin could see it.
  When someone left, their folder was packed. In SEITON this could follow `ACLs.md` `# Users`:
  a folder in `2_Team/22_Mitarbeiter` per person, with rules only for that person and the admin.
- The rights sketch had a "master": the admin of the parent project, who keeps rights in every
  subproject. Today a subproject with its own `ACLs.md` uses only that file, so the parent's
  admin is out unless listed again. Also: someone removed from a team was removed from every
  subproject (offboarding in one step), and a role for outside people.

### 6) Smaller ideas
- Browsing beyond folder borders: after the last picture of a folder, the viewer shows the next
  folder's name as a picture and then its first picture (photos sorted by year and month).
- Files that come with tags from the sender (a ticket, a bill, the terms) find their folder on
  their own: an airline's bill goes to `4_Finanz`. Today SEITON would need a person or AI for that.
- Programs as roles: a finance program gets exactly the finance folders of all projects (a lens
  for programs, not only for people), plus a small interface: "all `4_Finanz` below here",
  "save into `4_Finanz` of this project, create it if needed".

---

This document should evolve with the architecture. Keep it concise, practical, and implementation-aligned.