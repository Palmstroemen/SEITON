# **SEITON Trash - Design Document**

## **1. Purpose**
Deleting in SEITON should be **undoable for a while**, without surprising other programs.
Before the trash Scope deleted permanently (`shutil.rmtree`). This document describes the
trash that replaced that; it is built (`core/trash.py`, Scope, `myproject trash`).

---

## **2. Decisions (2026-10-21)**
- **One trash per project:** `.seiton/Trash/` in the project the deleted entry belongs to —
  the nearest project of its parent folder, so a **subproject has its own trash** and takes
  it along when it is moved out; deleting a whole subproject puts it into its parent's
  trash. The project's own `.seiton` cannot be deleted this way. Outside projects SEITON
  uses the **system trash** (freedesktop, `gio trash`).
- **Deleting moves**, it does not mark: the entry leaves the project tree at once, so
  terminals, other file managers, backups, sync and search no longer see it at its old
  place. (Marking and hiding in place was rejected: everybody but Scope would still see
  the files; hidden folders are in use already.) Within one filesystem the move is a
  rename, instant also for big folders.
- **Retention is configurable:** `trash_days: 30` in `.seiton/Project.md`; a subproject
  without the key inherits it from its parent project (config rule `dynamic`), else 30.
- **Rights:** whoever had `delete` at the original place may see, restore and finally
  delete an entry of the trash. Deleted confidential folders are therefore not readable
  for everybody in the trash. Like all ACL checks this applies with `SEITON_ACL_MODE=enforce`;
  otherwise everyone sees the whole trash.
- **Display:** a trash button in the FilesPanel side panel, shown only while the trash of
  the current project holds something (simple first, power when used).

---

## **3. Layout (compatible with the freedesktop trash)**
```
<project>/.seiton/Trash/
    files/<name>                 the deleted file or folder
    info/<name>.trashinfo        where it came from
```
`<name>` is the original name, made unique (`Bericht.md`, `Bericht.md.2`, …) like the
freedesktop trash does. A `.trashinfo` is the freedesktop format plus one SEITON key:
```
[Trash Info]
Path=Familie/Ich/Steuer         (project-relative, URL-encoded, no leading / as in the freedesktop spec)
DeletionDate=2026-10-21T09:15:00
DeletedBy=oliver
```
So tools that know the freedesktop trash can read it; the path is the ACL path without its leading `/`.

---

## **4. Operations**
- **Delete:** check `delete` at the entry (ACL enforcement), move it to `files/`, write the
  `.trashinfo`, then turn emptied template folders back into embryos as today. Embryos
  cannot be deleted (they are not on disk).
- **Restore:** move back to `Path`; if something of that name exists there now, restore
  as `<name> (restored)` instead of overwriting. Missing parent folders are recreated
  (embryos are born on the way). "SEITON settings" (a project turned back into a folder,
  `core/project_unmake.py`) go back as the folder's `.seiton`: it is a project again. Only
  when the folder is no project now and nothing in its `.seiton` would be replaced; else
  they come back as a folder of that name.
- **Delete finally / empty trash:** permanent, confirmed, per entry or for all entries the
  user may delete.
- **Clean-up:** entries older than `trash_days` are removed when the project is opened
  (Scope context change) — no background service needed.
- **Moving across filesystems** (e.g. a project on a USB stick): the trash is on the same
  filesystem as the project, so deleting stays a rename. Only an entry on another
  filesystem inside the project (a mount point) is copied and removed.

---

## **5. Open Points**
- Built: the restore UI (Scope's trash dialog behind the side panel button: name, original
  place, date, who; restore / delete finally / empty) and the CLI `myproject trash` (list,
  restore, delete, empty `--yes`), both through `ScopeApi`, so the same rights apply.
- Sync/clouds: the trash travels with the project; whether synced deletions should land
  in every member's view is a question for the sharing model.
- Quotas: a large trash could fill a USB stick; maybe warn above a size.
