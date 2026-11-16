# SEITON Time - Design Document (Draft)

Draft of 16 November 2026. Time tracking per project: a small clock counts the time one spends
in a project, writes it into the project, and a parent project collects the time of its
children. It is part of SEITON, not of the workshop: it sits in the top bar of Scope, where one
switches projects.

It is also the first program with a role of its own ("Ein Zaun um die Arbeit", point 2): it
may write one folder in every project and nothing else (section 7).

## 1. The Picture

- In the top bar, next to the person (login, logout), there is a **clock button**. It shows
  whether the clock runs, and for which project: `Küche · 2:15`. Grey when it stands.
- One works in a project, the clock counts. One goes for lunch without logging out, and after
  5 minutes without mouse or keyboard the clock stops; those 5 minutes do not count.
- A video runs, nobody touches the mouse: now and then the clock asks "Still working on
  *Küche*?" One click, and it keeps counting (the dead man's button, section 4.3).
- A click on the clock button opens the **time screen**: start and stop by hand, add what was
  done away from the computer ("Baumarkt, 1½ h"), correct, and see the time of a project with
  its children, by person and period.

## 2. Where the Time Is Kept

Each person has one file per project:

```
Küche/
  0_Admin/
    Zeitaufwand/
      Oliver.md
      Anna.md
```

- **One file per person** (decided 2026-11-16): two people never write the same file, so the
  cloud never makes a conflicting copy. The time screen merges and filters them.
- **The person** is the one SEITON already knows in this project: `core/identity.py`,
  `acl_user_for(project)` (the first of one's own names the project lists, else the login name).
  The file name is that name, as written in `# Users`.
- **`0_Admin`**, because the time spent is a matter of running the project, like its goals and
  its planning. The templates get the folder `0_Admin/Zeitaufwand` (section 7.2 needs it as a
  template folder); in older projects it is born when the first entry is written.

### 2.1 The file

A Markdown table, readable and editable without SEITON:

```markdown
# Zeitaufwand Oliver

| Date       | From  | To    | Time | Kind  | Note     |
|------------|-------|-------|------|-------|----------|
| 2026-11-16 | 09:12 | 11:40 | 2:28 | auto  |          |
| 2026-11-16 | 13:05 | 14:35 | 1:30 | added | Baumarkt |
```

- One row per stretch of time. **Kind**: `auto` (counted by the clock), `manual` (started and
  stopped by hand), `added` (entered afterwards), `corrected` (an `auto` row changed by hand).
- **Time** is From to To, written for the reader; the reader of the file (SEITON) computes it
  again and trusts From and To. A row may have only a duration and no From/To ("added, 1:30").
- **Local time**, with the offset only when it is not the one of the file's first row, as
  `09:12+02:00` (holidays in another time zone). Open: section 10.
- A stretch does not run over midnight: the clock closes it at 24:00 and opens the next day's.
- Sorted by date and From. Rows the person wrote by hand stay where they are; SEITON adds new
  rows at the end and sorts only when it rewrites the file from the time screen.

## 3. Parents and Children

A project inside a project is its child (`ProjectFinder`, a `.seiton/Project.md` below). The
time of a project is:

- **its own**: the files in its `0_Admin/Zeitaufwand`;
- **plus that of its children**, down to the last grandchild.

Each stretch lives in exactly one file, the one of the project that was active (section 4.1),
so nothing is counted twice. The time screen shows the parent's sum and opens to the children:

```
Firma                 128:40
  Kunde Huber          42:15
    Küche              30:00
  Kunde Maier          61:10
  (Firma itself)       25:15
```

The parent reads its children's files; it never copies them. Who may see a child's time is
decided by the child's ACLs, as for any file (section 7.2).

## 4. How the Clock Counts

### 4.1 The active project

The project of the top bar: the one chosen there, or the nearest project above the folder
Scope stands in (`resolve_cwp`). Switching the project closes the running stretch and opens
one in the new project. No project active: the clock stands.

### 4.2 Activity

- The clock asks the session how long no input came (the **idle time**), every 15 s. It does
  not record keys or the mouse, it only asks "how long since the last input?".
- Idle time above the **pause limit** (5 minutes, set in Setup): the stretch is closed at the
  last input. The idle minutes do not count.
- The next input opens a new stretch in the same project (automatic resume, can be switched off
  in Setup; then the clock waits for a click).
- Short gaps are not stretches: if a new stretch begins less than 1 minute after the last one
  ended in the same project, the two become one row.

Where the idle time comes from depends on the session (an adapter each, `IdleSource`):

| Session | Source |
|---|---|
| X11 | the XScreenSaver extension (as `xprintidle` does) |
| Wayland | `ext-idle-notify` or the desktop's idle monitor (GNOME: Mutter IdleMonitor, KDE: KIdleTime) |
| Tests | a fake source and a fake clock |

### 4.3 Video and the dead man's button

A video player tells the system not to start the screensaver (an *idle inhibitor*,
`org.freedesktop.ScreenSaver.Inhibit`). The clock sees that:

- idle time above the pause limit **and** an inhibitor active: the clock does not stop, it
  asks: a small notice at the clock button, "Still working on *Küche*?" with "Yes" and "No".
- **Yes**: it keeps counting, and asks again after the next pause limit.
- **No**, or no answer within 2 minutes: the stretch ends at the moment it asked.
- Without inhibitor information (a desktop that does not tell), the clock stops as in 4.2.

### 4.4 By hand

- **Stop** on the time screen: the clock stands until **Start**, even with input. The button
  shows that it was stopped by hand (an outline instead of grey).
- **Start** in a stand: counts as `manual`, and the pause limit still applies.
- **Add**: date, project (the active one preselected, any project one may write), From–To or a
  duration, a note. Example: shopping for the project in town.
- **Correct, delete**: only one's own rows. A changed `auto` row becomes `corrected`.

### 4.5 A crash or a switched-off computer

The running stretch lives on the computer, not in the project, in
`~/.local/state/seiton/clock.json` (project, person, From, last activity). It is written each
minute. It reaches the project file when it closes. After a crash, the next start closes it at
its last activity. So the project file changes only when a stretch closes, not every minute,
and the cloud does not sync a file that keeps changing.

## 5. The Time Screen

Opened by the clock button; a page like Setup, so it fits in the top bar form of Scope.

- **Now**: the active project, today's time in it, Start/Stop.
- **Entries**: one's own rows of the active project (or any chosen one), newest first; edit,
  delete, **Add**.
- **Overview**: a project with its children (section 3), filtered by person, period (week,
  month, own range) and kind; sums per project and per person. Later: export as CSV for an
  invoice.

Setup gets a "Time" part (General tab): pause limit, automatic resume, the dead man's button
on/off.

## 6. Parts

| Part | Where | What |
|---|---|---|
| The file | `core/time_log.py` | read and write a person's file; rows, kinds, merging of short gaps, midnight |
| Collecting | `core/time_log.py` | a project with its children, filters, sums |
| The clock | `core/clock.py` | the states (stands, runs, paused, asks, stopped by hand), driven by events and a clock; no Qt, no system calls |
| Sources | `core/clock_sources.py` | `IdleSource` (X11, Wayland, fake), inhibitors, the active project |
| The program | `daemon/clock_daemon.py` (`seiton-clock`) | runs the clock, tells the top bar over a socket what it shows |
| The button and the screen | `Scope/` (top bar form) | the clock button, the time screen, the Setup part |

The clock is a program of its own rather than a part of Scope: it has to run when no Scope
window is open, and it gets a role of its own (section 7).

## 7. The Role of the Clock

### 7.1 What it may

The clock may:

- **write** `0_Admin/Zeitaufwand/` in every project;
- **read** which project is active, and the idle time;
- nothing else: no other folder, no home directory.

This rule is written down once, readable, where SEITON keeps the user's programs
(`~/.config/seiton/Programs.md`, new):

```markdown
# Programs

## Zeiterfassung
- Program: seiton-clock
- /0_Admin/Zeitaufwand/: read, write
```

The path is a path in every project, as in `ACLs.md`. That is the point of fixed folders: one
rule fits all projects, including those that do not exist yet.

### 7.2 How it is enforced

The clock does not write the projects directly. It gets **the perspective** `0_Admin/Zeitaufwand`
from the FUSE drive (`core/perspective_fuse.py`), where `/0_Admin/Zeitaufwand/Projekte/Küche`
is `Projekte/Küche/0_Admin/Zeitaufwand`. SEITON starts it with bubblewrap:

- the drive's perspective `0_Admin/Zeitaufwand` bound in, read and write;
- its state folder (`~/.local/state/seiton`), read and write;
- the system read-only, an empty home, no projects folder.

The drive's department paths are made of template folders (`core/perspective_drive.py`), so
`Zeitaufwand` has to be one (section 2). For a project without the folder, the drive already
bears a missing department folder on the way when saving; step 4 checks that this holds one
level deeper too.

A new project appears in the perspective by itself; no rule and no mount has to change. This is
"what is a data silo today becomes a perspective with rights" made real: the clock sees the
time files of all projects, as its own silo, and they still lie in the projects.

The drive checks each write with the person's ACLs (`may(path, action)`), as for every program.
So the clock cannot write where the person may not.

### 7.3 What the prototype does not close

- **X11**: to ask the idle time the clock needs the X socket, and on X11 any client with it can
  read the keyboard. This is the same hole Flatpak has on X11. On Wayland the idle time comes
  over a protocol that tells nothing else.
- **D-Bus**: inhibitors are asked over the session bus. Without a filter (Flatpak's
  `xdg-dbus-proxy`) the clock could also talk to other services. The prototype names it; a filter
  is a later step.
- A program started past SEITON is not in the fence.

### 7.4 What the ACLs need

The clock writes as the person. In many projects a person may not write `0_Admin` (in the
standard template only the folder's own role may). The rule needed is **"everyone writes their
own time file"**: a right on a file named after oneself. This is new in the ACLs:

```markdown
## Folder
- /0_Admin/Zeitaufwand/{Self}.md: read, write
```

`{Self}` is the person, as `{Folder}` is the folder's role today. Reading the others' files is
then a normal right (for example the project's admin reads all of `0_Admin/Zeitaufwand/`).
Open: section 10.

## 8. Later: the Phone

Not part of the first steps, written down so the design leaves room for it:

- **Switching projects on the phone**, for holidays or for work on the road from one job to the
  next. The phone writes the active project into the person's own place in the cloud, and the
  clock and the top bar follow.
- **Photos by the time line**: the Nextcloud app already uploads photos into a folder. SEITON
  puts each photo, by the time it was taken, into the project that was active then (the time
  files are the time line): `9_Dokumentation/92_Bilder`. A photo from a time without a project
  stays in the inbox.
- **Receipts**: photographed in the app as a receipt, they land in
  `4_Finanz/44_Rechnungen/Eingang` of the active project, and the time screen can add the trip
  as an `added` stretch.
- A small app of its own comes after that: switch project, start/stop, photograph a receipt.

## 9. Steps

Each step with its tests first (fake clock, fake idle source, tmp projects).

1. **The file and collecting** (`core/time_log.py`): read, write, merge gaps, midnight, a parent
   with its children, filters.
2. **The clock** (`core/clock.py`): all states and transitions, the pause limit, the dead man's
   button, by hand, crash recovery from `clock.json`.
3. **The sources**: X11 idle time and inhibitors on the test machine (Cinnamon, X11); Wayland
   after that.
4. **The program** `seiton-clock` and its role: the perspective `0_Admin/Zeitaufwand` from the
   FUSE drive, the start in bubblewrap, `Programs.md`; `{Self}` in the ACLs.
5. **The button and the time screen** in the top bar form of Scope, once that form is ready;
   the Setup part.
6. Later: the phone (section 8).

## 10. Open Questions

1. **Time zones**: local time with an offset only where it changes (as above), or always the
   offset? Readability against travel.
2. **Column names**: in the user's language (German files have `Datum | Von | Bis | Dauer | Art |
   Notiz`) and SEITON reads both, or one fixed language?
3. **`{Self}` in the ACLs**: is a right on "one's own file" the right new concept, or should the
   standard template simply let every member write `0_Admin/Zeitaufwand/`?
4. **Several computers**: the same person works on two computers at once (rare). Both clocks
   write the same person's file. Each computer its own file (`Oliver (Laptop).md`), or accept
   the rare conflict?
5. **Granularity for invoices**: rounding (to 15 minutes?) only in the overview and export, never
   in the file?
