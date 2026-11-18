# SEITON

A new OS paradigm for Linux: project-centric desktop and filesystem.

Seiton (整頓) is Japanese for order: a place for everything, and everything in its place. That is exactly the idea of SEITON: an order that is easy to understand, one that anyone can grasp and use right away.

**SEITON** is an experimental Linux desktop concept that puts the user and their projects at the center. The goal is an intuitive, context-sensitive environment where everything revolves around your current project and its structure.

Until November 2026 the project was called MyOS; in some places that name still appears.

## Project Status

**Current phase:** MVP implementation. The core API, Scope, the Headline, the time tracking, the CLI tools, the perspectives drive and a first Nextcloud integration are in place and being hardened. Not a complete operating system.

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
| **Headline/** | The line at the top edge of the screen: project, standard folders, perspectives |
| **Time/** | Time tracking per project (the clock and its screen) |
| **daemon/** | The session daemon: the perspectives drive, the shared lens, the clock |
| **cloud/** | Nextcloud: the app `seiton` and the core as a service |
| **PostFix/** | From the workshop: Markdown editor with tag sidebar, Obsidian-compatible |
| **SunTree/** | From the workshop: the folder fan for quick dropping |
| **templates/** | The templates SEITON ships (Standard, Person, Firma, Development) |
| **installer/** | The installer (`install.sh` starts it) and its requirements |
| **cli/** | CLI tools (myls, myproject, mytag, myedit, myfilter, etc.) |
| **docs/** | Documentation index, development guide, conventions, security |
| **Vision/** | Concept and GUI notes (e.g. CWD/CWP/CTD) |
| **Learning SEITON/** | Tutorial and learning content (DE/EN) |
| **SEITON_Test/** | Local test data for the GUI (not in the repository) |

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
  Nautilus, Nemo and Dolphin too; the installer asks before installing it.

---

## Install

For one user, from the git folder (Debian/Ubuntu/Mint, Fedora, openSUSE, Arch/Manjaro; X11 session):

```bash
git clone git@github.com:Palmstroemen/SEITON.git
cd SEITON
./install.sh
```

It installs the missing system packages (after asking, with sudo), puts SEITON's Python packages
into a venv of its own (`~/.local/share/seiton/venv`), adds SEITON to the menu, the launchers
`seiton`, `seiton-postfix` and the CLI tools to `~/.local/bin`, and the templates to
`~/.seiton/Templates`. It asks whether SunTree, the Headline and the clock of the time tracking should start at
login and whether the file browsers should show Markdown previews (`--suntree`, `--headline`,
`--clock`, `--thumbnailer`; `--yes` asks nothing).
Update: `git pull` and `./install.sh` again. Remove: `./install.sh --uninstall` (settings and
templates stay).

## Quick Start

**Run Scope from the repository without installing (needs the packages of `installer/requirements.txt`):**
```bash
python3 Scope/Scope.py
```

**Run tests** (every test folder, from the repository root):
```bash
python3 -m pytest
```

**CLI examples:**
```bash
python3 cli/myls.py "Learning SEITON/DE/Lektion10" --extended
python3 PostFix/cli.py path/to/file.md
```

Setup, dependencies, and contribution guidelines: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
