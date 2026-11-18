# SEITON Project Status

**Last updated:** 2026-11-18
**Phase:** MVP implementation with focus on stable core flows
**Branch:** `main`

Until November 2026 the project was called MyOS. `MYOS_` variables are still read; projects
under `.MyOS` and `~/.config/MyOS` move over with `python3 cli/migrate_name.py --apply`
(`core/name_migration.py`, former names in `core/brand.py`).

## Summary

SEITON has moved beyond early prototyping. Core components are implemented and iteratively hardened:

- **Scope** — QML file browser: Templates + Projects rows, path bar, CWD/CTD navigation, tag filtering, DnD, multi-selection, context menu; settings on its back (General, Scope, SunTree; `Scope/Designdocument Setup.md`)
- **Headline** — the line at the top edge of the screen: where one is, the project's standard folders, the perspectives, the clock; docked, as a panel like a start menu, or as a Cinnamon applet (`Scope/Designdocument Headline.md`)
- **Time tracking** — a clock counts the time per project, writes it into the project, and parent projects collect their children's time; the clock has a role of its own in the sandbox (`core/Dokumentation/Designdocument Time.md`)
- **CLI tools** — myls, myproject, mytag, myacl, myedit, myimport, myexport, myfilter
- **Blueprint layer** — Embryo materialization one level at a time (including nested embryos); unused born folders turn back into embryos
- **ACLs** — rules per folder in `.seiton/ACLs.md`, roles, `## Everyone` and `{Self}`, a sandbox for programs with a role of their own
- **Filters & Perspectives** — Filter runtime (include/exclude/flatten; `Filter.md` acts by itself, `.seiton/Filters/` only when chosen with `myfilter`); the lens as one session in the perspective daemon, shared by Scope, SunTree and the Headline, with the FUSE drive "Perspektiven"
- **Nextcloud** — `myacl sync` turns `ACLs.md` into Team folder rules; the app `seiton` locks new entries at once and shows the SEITON folders and the perspectives in Files; the core runs beside Nextcloud as a service (`cloud/nextcloud/Designdocument SEITON Core Service.md`)
- **Desk** — The desktop follows the projects: per-project themes (apps, taskbar) and wallpaper (KDE, Cinnamon, GNOME), changes saved automatically; project icon. Taskbar programs not yet
- **Sort** — `Sort.md` runtime for automatic project sorting
- **Tagging** — Project-scoped tags, color registry, security-tested
- **Installer** — `./install.sh` installs SEITON for one user (venv, menu, launchers, templates); asks for SunTree, Headline, clock and Markdown previews
- **From the workshop** (SEITON runs without them): **PostFix**, a Markdown editor that edits like Obsidian (CodeMirror 6); **SunTree**, the folder fan for dropping things into folders; **ClipboardTool**, a CopyQ integration that saves text clips as Markdown

Test suite: `python3 -m pytest` from the repository root (every test folder, see `pytest.ini`) — 1950 passing, 12 skipped, 1 expected failure (2026-11-18). Two benchmarks are left out; run them with `-m benchmark`. The tests in `cloud/nextcloud/tests` need a test server and skip without one.

## Current Priorities

The order comes from [Roadmap.md](Roadmap.md) ("Jetzt"):

1. Evaluating the test machine: does someone still use SEITON after a week? (`docs/TEST-MACHINE.md`)
2. One entry case: the small business (customer, numbered invoice as PDF, open invoices, reminder)
3. The method on one page (`docs/Vision/Die Methode auf einer Seite.md`)

Besides: fixing what the review of 2026-11-18 found (`docs/Prüfung 2026-11-18.md`).

## Recent Milestones (Nov 2026)

- MyOS is now SEITON, with `cli/migrate_name.py` for old projects and settings (2026-11-14)
- Installer for one user; SEITON runs without the workshop pieces (2026-11-16)
- Time tracking, steps 1–4, and the Headline, steps 1–4 with its widgets (2026-11-16/17)
- ACLs: `## Everyone` and `{Self}` (2026-11-16)
- Nextcloud: `myacl sync`, the app (then `myos_acl`, now `seiton`), the core as a service with a shadow tree, rights kept live, the perspectives in Files, SEITON tags as Nextcloud tags (2026-11-07 to 11-12)
- PostFix: the Obsidian-like editor is the default (2026-11-07)
- Scope: colour schemes on its back, chosen and edited (2026-11-06)

## Earlier Milestones (Oct 2026)

- Embryo birth materializes only the folder itself; visible subfolders stay embryos until first use
- Born template folders that hold nothing of the user turn back into embryos after delete/move (cascading upwards); `myproject tidy` does the same for folders emptied outside SEITON
- Deleting is undoable: entries go to the trash of their project (`.seiton/Trash/`, freedesktop layout, `trash_days` in Project.md, default 30), outside projects to the system trash; CLI `myproject trash list|restore|delete|empty`
- UI strings are English in the code; German (default UI language) comes from `*_de.ts` translations, kept complete by tests (`scripts/update_translations.py`)
- ACLs: rules in ACLs.md are project-relative; per role the nearest rule wins, `none` locks a role out; subprojects without own ACLs.md inherit the parent's; right `delete` (not implied by `write`)

## Known Open Points

- The review of 2026-11-18 lists what is still wrong or unfinished: `docs/Prüfung 2026-11-18.md`
- Legacy and duplicate-logic candidates in Scope: `Scope/.Legacy-Code-Kandidaten.md`, `Scope/.FolderBrowser-DoppelKandidaten.md`
- `main.qml` (~3500 lines) and `FolderBrowser.qml` (~4800 lines) are large; further splitting pending

## Operational Details

For the full operational roadmap, open questions, and learnings, see [ProjectLogbook.md](ProjectLogbook.md).
