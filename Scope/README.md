# Scope — SEITON File Browser

QML-based file browser for SEITON: project and template navigation, tags, and file operations.

## Overview

- **Two browser rows:** Templates (standard folders / embryos) and Projects (CWP and subprojects). Each row can show a path breadcrumb and folder list. The Projects row is off by default (setting `Scope/projectsRow`, switched in Setup).
- **Concepts:** CWD/CWP (current working directory/project) and CTD (current target directory) for preview and file list. See [docs/Vision/GUI Filebrowser.md](../docs/Vision/GUI%20Filebrowser.md) for definitions and [main.qml](main.qml) comment block for code mapping.
- **X-ray** (on by default, button in the side panel): files of small folders are shown in their place while the list fits the FilesPanel without scrolling (`core/xray.py`); a large, faint folder lies behind them, the tooltip says where they lie. Recomputed on folder change and when a resize has settled.
- **Sorting by date** (`core/filing.py`, see `core/Dokumentation/Designdocument Sort.md`): a folder with `.seiton/Sort.md` shows its loose files in virtual year/month folders (faint) and files them into real ones once it holds more than `NewLevelFrom` files; filed when listed, at start and daily. For now a rule is written by hand (`.seiton/Sort.md`): "Enable sorting" is in the backend (`enableSorting`), but no button calls it yet.
- **Rename:** F2 renames the entries selected in the FilesPanel; folders in the browser rows: hold the mouse button, or right click → Rename.
- **P-Button:** works on the one entry selected in the FilesPanel, else (nothing selected) on the folder it shows; it never switches to another folder on its own. A folder that can become a project: strong “P” (the new project gets its templates' `.seiton` files). A project that can become an ordinary folder again: crossed-out “P” (a top project only without settings of its own; else with settings of its own Scope asks, and they go into the parent project's trash as “SEITON settings”, see `core/project_unmake.py`). Greyed out otherwise (outside the projects tree, templates, embryos, several entries). The tooltip names the folder. Project folders carry a small “P” badge.
- **Files area:** File list with tag filter, multi-selection, drag & drop, context menu. Optional side panel with folder/file tags; a button opens the project's `.seiton` folder, and inside it a Leave button (↑) steps out again.
- **Dialogs:** All dialogs are in `Scope/Dialogs/` (e.g. move, rename, batch rename, create folder, delete, trash, open with, remove project, ACL person and role). Main window only instantiates them.
- **Setup:** the back of Scope (`SetupPage.qml`, see [Designdocument Setup.md](Designdocument%20Setup.md)): settings of Scope, the Headline and SunTree.
- **Headline:** the minimal view M of Scope is replaced by the Headline, its own program at the top edge (`Headline/`, see [Designdocument Headline.md](Designdocument%20Headline.md)).

## Run

Start the Python backend and QML UI:

```bash
python3 Scope/Scope.py
```

Requires Qt 6 through PySide6 (installer/requirements.txt: 6.10; the QML imports QtQuick 6.9) and the `core` API (Scope.py bridges to `core.scope_api`). `./install.sh` sets up both; the installed launcher is `seiton`.

UI strings are English; German comes from `i18n/scope_de.ts` (see `docs/DEVELOPMENT.md`).

## Layout

- **main.qml:** Application window, theme, CWP/CTD state, `standardFolders` / `subProjects`, and the two `FolderBrowser` instances (Templates, Projects) plus `FilesPanel`. Path helpers live in `js/PathUtils.js` and `js/FolderBrowserUtils.js`.
- **FolderBrowser.qml:** Reusable folder bar (path segments, folder list, preview, drag/drop). Used for both template and project rows.
- **FolderItem.qml:** Single folder/item chip (text, smallIcon, largeIcon); opacity follows `fillColor.a` when half-transparent.
- **FilesPanel.qml:** File list, tag panel (adapts to tag width), P/settings/Leave buttons, tag chips.
- **CwdTools.qml:** the tools row below the CWD.
- **SetupPage.qml:** Setup, the back of Scope.

## Backend

`Scope/Scope.py` loads the core API and exposes it to QML as `backend`. It provides e.g. `listChildren`, `listTemplates`, `listEntriesFiltered`, `moveEntry`, `createProject`, and project/config helpers.
