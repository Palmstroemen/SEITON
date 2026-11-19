# SEITON

**A structure for your files that belongs to you.** Every project gets the same standard folders,
and they only appear when you need them.

<!-- Teaser video, about 60 seconds: goes here once it is made. -->

Seiton (整頓) is Japanese for order: a place for everything, and everything in its place.

## Three moments

**A folder is born.** Every computer has `Documents`, `Pictures` and `Music`; nobody asks where a
photo goes. SEITON does that for every project: `0_Admin`, `1_Info`, `4_Finanz`, `5_Recht`,
`9_Dokumentation` and the rest. They wait inside the project as pale folders. Drop a file on one,
and it becomes real, in Scope and in every other file manager.

**The lens.** Put on the lens of a standard folder, say `4_Finanz`, and you see that one folder
across all your projects. No copy, no second folder tree: the same files, seen the other way round.
Through the `Perspektiven` drive every program can do this; LibreOffice knows nothing of SEITON
and saves into the right project anyway.

**Rights in one line.** In a project's `.seiton/ACLs.md`:

```
## Buchhaltung
- /4_Finanz/: read, write
```

The accounting role works on the finances of every project and subproject, and on nothing else.
Anyone can read it, no admin console needed. A Nextcloud with the SEITON app enforces it on the
server.

## What stays when you leave

Ordinary folders and a few Markdown files in a hidden `.seiton` folder. Remove SEITON, and a tidy
directory tree remains, readable on any system. MIT licence.

## Who it is for

Administrations moving to Linux and Nextcloud, schools, companies, clubs, and anyone whose files are
spread over too many places. One structure for all of them, even when each uses its own template.

## Project Status

**A prototype, being hardened.** Built: the core with its API, Scope (the file browser), the
Headline (the line at the top of the screen: project, standard folders, lenses), time tracking, the
CLI, the perspectives drive and the Nextcloud app (Nextcloud 32 to 35). About 2000 automated tests.
Not a complete operating system.

Honest limits: on the desktop, rights are enforced by SEITON's own tools (Scope, CLI, the drive),
not yet by the file system itself; in Nextcloud the server enforces them. Until November 2026 the
project was called MyOS; in some places that name still appears.

For a status snapshot and priorities, see [docs/STATUS.md](docs/STATUS.md); for the roadmap and
open questions, [docs/ProjectLogbook.md](docs/ProjectLogbook.md).

---

## Repository Structure

| Path | Description |
|------|--------------|
| **core/** | API, FUSE/blueprint layer, project config, ACLs, tagging, design docs |
| **apps/** | SEITON itself: |
| **apps/Scope/** | QML file browser (Templates + Projects rows, tags, CWD/CTD) |
| **apps/Headline/** | The line at the top edge of the screen: project, standard folders, perspectives |
| **apps/Time/** | Time tracking per project (the clock and its screen) |
| **daemon/** | The session daemon: the perspectives drive, the shared lens, the clock |
| **cloud/** | Nextcloud: the app `seiton` and the core as a service |
| **examples/** | Apps that use SEITON, from the workshop: |
| **examples/PostFix/** | Markdown editor with tag sidebar, Obsidian-compatible |
| **examples/SunTree/** | The folder fan for quick dropping |
| **examples/ClipboardTool/** | CopyQ commands that save clips as Markdown files |
| **assets/** | SEITON's icons and brand images |
| **templates/** | The templates SEITON ships (Standard, Person, Firma, Development) |
| **installer/** | The installer (`install.sh` starts it) and its requirements |
| **cli/** | The command `seiton` and its tools (seiton ls, seiton project, seiton tag, seiton acl, ...) |
| **docs/** | Design entry point, roadmap, logbook, status, development guide, conventions, security |
| **docs/Vision/** | Concept and GUI notes (e.g. CWD/CWP/CTD) |
| **Learning SEITON/** | Tutorial and learning content (DE/EN) |
| **SEITON_Test/** | Local test data for the GUI (not in the repository) |

Design documents live under `core/Dokumentation/`. Entry points: [docs/Designdokument.md](docs/Designdokument.md), [docs/INDEX.md](docs/INDEX.md).

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
`seiton` (with its commands: `seiton help`) and `seiton-postfix` to `~/.local/bin`, and the templates to
`~/.seiton/Templates`. It asks whether SunTree, the Headline and the clock of the time tracking should start at
login and whether the file browsers should show Markdown previews (`--suntree`, `--headline`,
`--clock`, `--thumbnailer`; `--yes` asks nothing).
Update: `git pull` and `./install.sh` again. Remove: `./install.sh --uninstall` (settings and
templates stay).

## Quick Start

**Run Scope from the repository without installing (needs the packages of `installer/requirements.txt`):**
```bash
python3 apps/Scope/Scope.py
```

**Run tests** (every test folder, from the repository root):
```bash
python3 -m pytest
```

**CLI examples** (installed: `seiton ls ...`; `seiton help` lists the commands):
```bash
python3 cli/seiton.py ls "Learning SEITON/DE/Lektion10" --extended
python3 examples/PostFix/cli.py path/to/file.md
```

Setup, dependencies, and contribution guidelines: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
