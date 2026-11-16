# SEITON

A new OS paradigm for Linux: project-centric desktop and filesystem.

Seiton (整頓) is Japanese for order: a place for everything, and everything in its place. That is exactly the idea of SEITON: an order that is easy to understand, one that anyone can grasp and use right away.

**SEITON** is an experimental Linux desktop concept that puts the user and their projects at the center. The goal is an intuitive, context-sensitive environment where everything revolves around your current project and its structure.

Until November 2026 the project was called MyOS; in some places that name still appears.

## Project Status

**Current phase:** MVP implementation — core API, Scope GUI, CLI tools, and blueprint layer are in place and iteratively hardened. Not a complete operating system; early experiments with FUSE, QML file browser, tagging, and workflow tools.

For a concise status snapshot and priorities, see [docs/STATUS.md](docs/STATUS.md). For the operational roadmap and open questions, see [ProjectLogbook.md](ProjectLogbook.md).

---

## What is SEITON?

- **Project-based desktop:** Multi-project environment for a single user. Each project can have its own desktop, launcher, and app configuration; open windows stay tied to their respective projects.

- **Standardized project structures:** Projects offer predefined but initially hidden folders (templates/embryos) that only materialize when used (e.g. first file moved in).

- **Deep Obsidian integration (vision):** Obsidian as the default note editor in a distraction-free mode; every project as an Obsidian Vault.

- **Permissions and localization:** Folder names and access rights can be customized per project and language.

---

## Vision

The building blocks exist but are fragmented. SEITON aims to unify them into one clean, intuitive environment with sensible defaults and a gentle learning curve.

---

## Repository Structure

| Path | Description |
|------|--------------|
| **core/** | API, FUSE/blueprint layer, project config, ACLs, tagging, design docs |
| **Scope/** | QML file browser (Templates + Projects rows, tags, CWD/CTD) |
| **PostFix/** | From the workshop: Markdown editor with tag sidebar, Obsidian-compatible |
| **SunTree/** | From the workshop: the folder fan for quick dropping |
| **cli/** | CLI tools (myls, myproject, mytag, myedit, myfilter, etc.) |
| **docs/** | Documentation index, development guide, conventions, security |
| **Vision/** | Concept and GUI notes (e.g. CWD/CWP/CTD) |
| **Learning SEITON/** | Tutorial and learning content (DE/EN) |
| **SEITON_Test/** | Test/demo project structure |

Design documents live under `core/Dokumentation/`. Entry points: [Designdokument.md](Designdokument.md), [docs/INDEX.md](docs/INDEX.md).

---

## From the Workshop

SEITON is Scope with its core, the CLI and the lens. Beside it lie a few pieces that sketch where
the idea could go. They are not needed for SEITON, and SEITON runs without them:

- **PostFix**: a Markdown editor with tags and rights in the sidebar. Scope opens notes in it by
  default; on Scope's back (General, Notes) you can switch that off, then notes open in Obsidian
  or the system's editor.
- **SunTree**: the folder fan (Ctrl + Alt + Space). Without it, Scope's back shows no SunTree tab.
- **Markdown previews for file browsers**: the thumbnailer behind Scope's previews, offered to
  Nautilus, Nemo and Dolphin too; `install.sh` asks before installing it.

---

## Quick Start

**Run the Scope file browser (requires Qt/QML and Python backend):**
```bash
python3 Scope/Scope.py
```

**Run tests:**
```bash
python3 -m pytest core/tests/unit cli/tests PostFix/tests -v
```

**CLI examples:**
```bash
python3 cli/myls.py SEITON_Test/Projekte/ --extended
python3 PostFix/cli.py path/to/file.md
```

Setup, dependencies, and contribution guidelines: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
