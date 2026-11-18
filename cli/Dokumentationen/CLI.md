# **SEITON CLI Overview**

SEITON has one command, `seiton`, like `git` or `gh` (`cli/seiton.py`). Alone, or with a path or a task (`--setup`, `--search`, `--clipboard`), it starts Scope; with a command it runs that tool: `ls`, `project`, `tag`, `acl`, `edit`, `filter`, `export`, `import`, `drive`. `seiton help` lists them. A folder called like a command opens with a path (`seiton ./tag`); a word that is neither is said, with the closest command.

`./install.sh` puts `seiton` into `~/.local/bin`, beside `seiton-clock` and `seiton-time`. In the repository: `python3 cli/seiton.py <command>`; each tool lives in `cli/seiton_<command>.py`. Every command knows `--help`; exit 1 = error, 2 = wrong arguments.

Of the tools only `seiton acl` knows the ACL mode `enforce`; the others act with the rights of the file system (see "Designdocument ACLs.md").

## **seiton ls**
List files with SEITON-aware views.

Examples:
- `seiton ls .`
- `seiton ls --extended` (embryo status; `--color`: embryos in light blue)
- `seiton ls --tags`
- `seiton ls --roentgen` (x-ray: files of small folders, while the terminal's height suffices; `--roentgen 10`: 10 lines). Files seen through show where they lie: `r1.pdf   (in Rechnungen/2024)`

Not built: `--recent` prints nothing yet, `--all` shows only the extended view.

---

## **seiton project**
Project management.

Examples:
- `seiton project create /path/to/folder`
- `seiton project create --new /path/to/new-folder` (makes the folder first)
- `seiton project remove /path/to/project` (an ordinary folder again, as the crossed-out P in Scope; with settings of its own it asks for `--keep-own`: they go into the parent project's trash)
- `seiton project tidy .` (born template folders that hold nothing of the user become embryos again)
- `seiton project trash list .` (the trash of the project the path lies in)
- `seiton project trash restore NAME --in .` / `seiton project trash delete NAME --in .` (`NAME` as `trash list` shows it)
- `seiton project trash empty --in . --yes` (delete everything in the trash for good; cannot be undone)

Not there: making a project an ordinary folder again (in Scope: the crossed-out P button).

---

## **seiton export**
Export a subtree from a project.

Examples:
- `seiton export /path/inside/project --out /tmp/export`
- `seiton export /path/inside/project --out /tmp/export --zip`

---

## **seiton import**
Import an export package. Without `--target` it goes back to its place, when that is still a project (restore). With `--target` it comes into that folder as a project of its own, named as the exported project (adopt): with its settings and its ACLs, which always travel with the project - inside another project it is a child with its own rights beside the mother's. It never mixes with a folder of that name already there.

Examples:
- `seiton import /tmp/export/package` (back to its place)
- `seiton import /tmp/export/package --target ~/Projekte` (as `~/Projekte/<project>`)
- `seiton import /tmp/export/package --conflict overwrite`

`--mode auto|restore|adopt` (auto: restore without a target, else adopt), `--conflict skip|overwrite` (files already there: kept or replaced; the settings in a `.seiton` there are always kept).

---

## **seiton filter**
Filter utilities.

Examples:
- `seiton filter list .` (filters from the path upwards; `--verbose`: where each comes from)
- `seiton filter resolve .`
- `seiton filter resolve . --manual /path/to/Filter.md`
- `seiton filter show .` (the effective filter in detail)
- `seiton filter activate /path/to/Filter.md` (a manual filter, it holds until `clear`)
- `seiton filter clear`

---

## **seiton tag**
Tags of files and folders. A file's tags are its extended attributes (with an optional value: `wichtig=60`); a folder's are the ones Scope shows and filters by, in its `.seiton/myTags.md`, plain tags without a value (`set` refuses them). `seiton ls --tags` shows both.

Examples:
- `seiton tag list file.txt`
- `seiton tag add file.txt dringend`
- `seiton tag set file.txt wichtig=60`
- `seiton tag remove file.txt dringend`
- `seiton tag clear file.txt`

For folders seiton tag reads and writes the xattr, Scope reads folder tags from `.seiton/myTags.md`: the two do not see the same folder tags yet.

---

## **seiton acl**
ACLs: who may do what, and every rule of a project. Read-only; edit rules with `seiton edit acl` or in Scope/PostFix. With `SEITON_ACL_MODE=enforce` only people who may read ACLs.md see them.

Examples:
- `seiton acl show Finanz/Archiv` (roles and people with their rights here; per role `here` or `from /Finanz`: the folder whose rule decides)
- `seiton acl check Anna Finanz delete` (prints yes/no; exit 0 = allowed, 1 = not, 2 = error)
- `seiton acl check Anna Finanz` (all rights of Anna there)
- `seiton acl rules .` / `seiton acl rules . --json` (every rule, `## Folder` rules resolved into each subproject, paths as written in ACLs.md, `[]` = `none`; the input for adapters, e.g. to a cloud)
- `seiton acl sync --plan .` (the rules a Nextcloud Team folder with "advanced permissions" should hold, per person; settings in `.seiton/Nextcloud.md`, see below; no network)
- `seiton acl sync --dry-run .` (reads the Team folder and its rules over WebDAV and shows what would change: `+` new, `~` changed, `-` goes because it is not from ACLs.md; sends nothing. Login from `SEITON_NEXTCLOUD_USER` and `SEITON_NEXTCLOUD_PASSWORD`, best an app password; the account needs "manage advanced permissions" and should be able to read the whole folder)
- `seiton acl sync .` (shows the same, asks, sends the rules path by path, deepest first, and reads them back to check; `--yes` sends without asking, needed without a terminal. Rules not from ACLs.md go. Needs `group:`; with the server app `cloud/nextcloud/seiton` new entries on the way are locked at once, see `cloud/nextcloud/README.md`. Uploads each project's embryos first - a folder per embryo in `.seiton/Embryos/` with what its birth copies, and `.seiton/Embryos.json` to know what is up there - for the row of SEITON folders in the Files app; each embryo may be read by who may read the folder it becomes, as Scope shows it. What manages rights and the sync in a `.seiton` - `ACLs.md`, `ACLs-history`, `Nextcloud.md`, the embryos - only who has `change` on that `ACLs.md` may write, so the syncing account needs it. With the SEITON core service next to Nextcloud the same runs there after each change, see `cloud/nextcloud/README.md`)

`.seiton/Nextcloud.md`:
```
# Nextcloud
url: https://cloud.example.org
folder: Projekte         (the Team folder, as it shows in the account's files)
group: Projekte          (the groups the Team folder is given to, comma-separated: locked out at the root)

# Accounts
Anna Huber: anna.h       (person in # Users: Nextcloud account; people without one get no rules)
```

---

## **seiton edit**
Open a config section of the project in `$EDITOR` (`tags`, `templates`, `acl`, `config`). seiton edit writes nothing itself: a file that is not there yet is made when the editor saves it. Until then the project inherits, and seiton edit says from which file (a file of its own ends the inheritance; an `ACLs.md` of its own gives only the rights written in it).

Examples:
- `seiton edit tags .`
- `seiton edit templates /path/to/project`
- `seiton edit acl /path/to/project`

---

## **seiton-clock, seiton-time**
The time tracking (see "Designdocument Time.md").

- `seiton-clock` starts the clock with its role: it mounts the drive of its role and runs the clock in bubblewrap. `--projects-root PATH`: the folder holding the projects (else the first root below the home folder). `--no-sandbox`: without bubblewrap and role drive (development). A second start does nothing while a clock runs. `./install.sh --clock` starts it at login.
- `seiton-time` opens the time screen (`apps/Time/TimeScreen.py`).

---

## **migrate_name**
Moves projects and the user's settings from a former name (MyOS until 2026-11-14) to SEITON: `.MyOS` becomes `.seiton`, `~/.config/MyOS` becomes `~/.config/seiton`. Not installed as a launcher.

Examples:
- `python3 cli/migrate_name.py ~/Projekte` (only shows the plan)
- `python3 cli/migrate_name.py --apply ~/Projekte` (does it)
- `python3 cli/migrate_name.py --apply --config` (the user's settings folder too)

---

## **seiton drive** (developer tool)
Mounts the flipped perspective FUSE adapter as a separate filesystem. Not installed; the lens drive in daily use is mounted by the perspective daemon (`cli/perspective_daemon.py`).

Example:
- `seiton drive --projects-root /data/Projekte --mount-point /mnt/seiton-structure --foreground`

Notes (MVP):
- no small-project fallback behavior yet
- adapter is thin: mapping semantics come from the core perspective resolver
