# SEITON Time - Design Document (Draft)

Draft of 16 November 2026. Time tracking per project: a small clock counts the time one spends
in a project, writes it into the project, and a parent project collects the time of its
children. It is part of SEITON, not of the workshop. It first was to sit in the top bar of Scope;
since 17 November 2026 it is a program of its own that shows in the Headline as a widget
(apps/Scope/Designdocument Headline.md, 3a), where one switches projects.

It is also the first program with a role of its own ("Ein Zaun um die Arbeit", point 2): it
may write one folder in every project and nothing else (section 7).

## 1. The Picture

- In the Headline there is the clock's **widget**. It shows whether the clock runs, and for
  which project: `Küche · 2:15`. Calm when it stands.
- One works in a project, the clock counts. One goes for lunch without logging out, and after
  5 minutes without mouse or keyboard the clock stops; those 5 minutes do not count.
- A video runs, nobody touches the mouse: now and then the clock asks "Still working on
  *Küche*?" One click, and it keeps counting (the dead man's button, section 4.3).
- A click on the widget opens the **time screen**, a small window of the time tracking itself:
  start and stop by hand, add what was
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

| Datum      | Von   | Dauer | Art          | Notiz    |
|------------|-------|-------|--------------|----------|
| 2026-11-16 | 09:12 | 2:28  | auto         |          |
| 2026-11-16 | 13:05 | 1:30  | nachgetragen | Baumarkt |
| 2026-11-17 |       | 0:45  | nachgetragen | Telefonat mit Huber |
```

- One row per stretch of time: **when it began and how long it lasted** (decided 2026-11-16).
  There is no "To": it would say the same twice, and on the night the clocks change it would
  confuse (02:30 comes twice in autumn, not at all in spring). The duration is what counts; the
  end is From plus Dauer, computed where it is shown.
- **Von** may be empty for an added row ("0:45, Telefonat").
- **Art**: `auto` (counted by the clock), `manuell` (started and stopped by hand),
  `nachgetragen` (entered afterwards), `korrigiert` (an `auto` row changed by hand).
- **The columns and kinds are written in the user's language** (German as above; English:
  `Date | From | Time | Kind | Note`, kinds `auto`, `manual`, `added`, `corrected`). SEITON reads
  both, whatever language the file was begun in; it keeps the language of a file it adds to.
- **Local time, readable** (decided 2026-11-16): `09:12`, without an offset. Only when the
  computer's time zone is not the person's usual one (holidays abroad) does Von carry it:
  `09:12+09:00`. Sums never depend on it, because they add durations. Built so far: an offset
  in a file is read and written again; the clock never writes one. That comes later, with a
  setting for the person's usual time zone.
- A stretch does not run over midnight: the clock closes it at 24:00 and opens the next day's,
  so the sums per day are simple.
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

The project of the Headline: it writes the active project on every change
(`core/clock_sources.write_active`, `$XDG_RUNTIME_DIR/seiton/active-project.json`), and the clock
reads it every 15 s. Without a running Headline the clock sees no project. Switching the
project closes the running stretch and opens one in the new project. No project active: the
clock stands.

### 4.2 Activity

- The clock asks the session how long no input came (the **idle time**), every 15 s. It does
  not record keys or the mouse, it only asks "how long since the last input?".
- Idle time above the **pause limit** (5 minutes, set on the time screen): the stretch is
  closed at the last input. The idle minutes do not count.
- The next input opens a new stretch in the same project (automatic resume, can be switched off
  on the time screen; then the clock waits for a click).
- Short gaps are not stretches: if a new stretch begins less than 1 minute after the last one
  ended in the same project, the two become one row.
- A stretch shorter than a minute is a glance, not time (passing through a project on the way
  to another): it is not written.

Where the idle time comes from depends on the session (an adapter each, `IdleSource`):

| Desktop | Source (`core/clock_sources.py`), the first that answers is kept |
|---|---|
| Cinnamon | Muffin's idle monitor (`org.cinnamon.Muffin.IdleMonitor`, X11 and Wayland) |
| GNOME | Mutter's idle monitor (`org.gnome.Mutter.IdleMonitor`) |
| KDE | the freedesktop screensaver (`GetSessionIdleTime`) |
| any X11 | the XScreenSaver extension (as `xprintidle` does), last |
| Tests | a fake bus and a fake clock |

Tried on the test machine (Cinnamon, X11, 16 November 2026): Muffin and XScreenSaver give the
same idle time; the freedesktop screensaver does not answer there.

### 4.3 Video and the dead man's button

A video player tells the system not to start the screensaver (an *idle inhibitor*). The clock
asks the session manager whether the session's going idle is inhibited
(`org.gnome.SessionManager.IsInhibited` with the flag 8, "idle"; Cinnamon and GNOME), or KDE's
power management (`HasInhibit`). Seen on the test machine: a browser playing a video holds
"Video Wake Lock" with the flag 8; playing only audio it holds the flag 4 (suspend), so music
alone does not keep the clock counting. The clock sees that:

- idle time above the pause limit **and** an inhibitor active: the clock does not stop, it
  asks: its question in the widget, "Still working on *Küche*?" with "Yes" and "No".
- **Yes**: it keeps counting, and asks again after the next pause limit.
- **No**, or no answer within 2 minutes: the stretch ends at the moment it asked.
- Without inhibitor information (a desktop that does not tell), the clock stops as in 4.2.

### 4.4 By hand

- **Stop** on the time screen: the clock stands until **Start**, even with input. The button
  shows that it was stopped by hand (an outline instead of grey).
- **Start** in a stand: counts as `manuell`, and the pause limit still applies.
- **Add**: date, project (the active one preselected, any project one may write), From (may stay
  empty) and a duration, a note. Example: shopping for the project in town. Built so far: date,
  duration and note, into the active project; choosing the project and From are not offered
  yet.
- **Correct, delete**: only one's own rows. A changed `auto` row becomes `korrigiert`.

### 4.5 A crash or a switched-off computer

The running stretch lives on the computer, not in the project, in
`~/.local/state/seiton/clock.json` (project, person, From, last activity). It is written each
minute. It reaches the project file when it closes. After a crash, the next start closes it at
its last activity. So the project file changes only when a stretch closes, not every minute,
and the cloud does not sync a file that keeps changing.

## 5. The Time Screen

Opened by a click on the widget in the Headline; a small window of the time tracking itself
(`apps/Time/TimeScreen.py`, `apps/Time/main.qml`, `apps/Time/model.py`), with the person's own rights, not the
sandboxed clock's (decided 2026-11-17; first planned as a page like Setup in Scope's top bar).
It talks to the running clock as the Headline does: it reads the clock's view and drops
commands.

- **Now**: the active project, today's time in it, Start/Stop.
- **Entries**: one's own rows of the active project, newest first; edit, delete, **Add**.
  Choosing another project: not built yet.
- **Overview**: the active project with its children (section 3), by period (today, this week,
  this month, all); sums per project and per person. Not built yet: choosing another project,
  filtering by person and kind, an own range, export as CSV for an invoice.
- **Rounding** (for invoices) is only done in the overview and the export, never in the file
  (decided 2026-11-16): none, or to 5, 10, 15 or 30 minutes, upwards or to the nearest, per
  stretch or per day.
- **Settings** (a tab of its own): pause limit, automatic resume, the dead man's button on/off,
  the rounding step, and what the widget shows beside the projects worked on last. Kept in
  `core/settings.py`, section Time; upwards/nearest and per stretch/day are there
  (`Time/roundMode`, `Time/roundPer`) but not on the screen yet. The clock takes changes when
  it starts anew.

Setup (Scope) has no "Time" part: the settings are on the time screen.

## 6. Parts

| Part | Where | What |
|---|---|---|
| The file | `core/time_log.py` | read and write a person's file; rows, kinds, merging of short gaps, midnight |
| Collecting | `core/time_log.py` | a project with its children, filters, sums |
| The clock | `core/clock.py` | the states (stands, runs, paused, asks, stopped by hand), driven by events and a clock; no Qt, no system calls |
| Sources | `core/clock_sources.py` | `IdleSource` (X11, Wayland, fake), inhibitors, the active project |
| The program | `daemon/clock_daemon.py` (`seiton-clock`) | runs the clock every 15 s, writes its widget's view |
| The launcher | `cli/seiton_clock.py` | mounts the role's drive, starts the clock in its sandbox (section 7.2); one clock per user |
| The widget | `core/clock_widget.py`; shown by the Headline (apps/Scope/Designdocument Headline.md, 3a) | its view (`view.json`) and command files, a small ledger of the projects worked on last |
| The screen | `apps/Time/` | the time screen as its own window with its settings (section 5) |

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

Built 16 November 2026 (step 4). The clock does not write the projects directly:

1. **Its own drive.** `cli/seiton_clock.py` mounts a perspective drive of the clock's own
   (`core/role_drive.py`) at `$XDG_RUNTIME_DIR/seiton-drives/seiton-clock`. Every access on it
   must be allowed by the role (`Programs.md`, `core/programs.py`) and by the person's ACLs, the
   role asked first. Which program asks is told by the mount point, not by a process number: the
   clock only ever sees this drive.
2. **No fallback.** The general drive shows the project itself (or the nearest folder above)
   where a department folder is missing, for "Save as" in LibreOffice. For a role that would show
   more than the role allows (all of `0_Admin` in a project without `Zeitaufwand`). The drive of
   a role shows a missing folder empty and bears it when something is saved into it.
3. **Ways through projects.** A way in the drive goes on through a project to its subprojects
   (`/0_Admin/Zeitaufwand/Projekte/Firma/7_Arbeit/Kunde Huber`), after what the department
   folder holds; this holds for every drive (decided 2026-11-16).
4. **The sandbox** (`core/sandbox.py`, bubblewrap): the system read-only; home, `/tmp` (and
   with it the X11 socket), the runtime folder and the projects root hidden; the code read-only
   again; a cleared environment without `DISPLAY`. Inside, at `/tmp/seiton`:
   - `0_Admin/Zeitaufwand`: the role's folder from its drive, read and write;
   - `state`: the clock's state (`~/.local/state/seiton`), read and write;
   - `run`: the folder of `active-project.json`, read only;
   - `widget`: the widget's folder (`$XDG_RUNTIME_DIR/seiton-clock`: `view.json`, the commands
     the Headline drops), read and write;
   - and the session bus.
5. **One root.** The clock serves the projects root it was started with (`--projects-root`,
   else the first root below the home). An active project in another root (A11: `~/Dokumente`
   and `~/Projekte`) counts as no project: the clock does not show time it could not write.
   Serving several roots - a drive per root, or one drive over all - is a step of its own
   (review 2026-11-18, Z5).
6. **Written in place.** Through the drive the person may write their own file
   (`/0_Admin/Zeitaufwand/{Self}.md`), nothing beside it, so the clock writes the file itself
   anew instead of a helper file swapped in (review 2026-11-18, Z6).

   The projects root is hidden even where it lies inside the code (`SEITON_Test` in the
   repository): a kept folder would show it again.

   bwrap does not pass signals on. The clock is the sandbox's first process (`--as-pid-1`),
   bwrap tells the launcher its pid (`--info-fd`), and the launcher sends it SIGTERM when it is
   ended itself (logout): the clock then closes its running stretch at its last activity.

A new project appears in the perspective by itself; no rule and no mount has to change. This is
"what is a data silo today becomes a perspective with rights" made real: the clock sees the
time files of all projects, as its own silo, and they still lie in the projects.

Tried on the test machine (16 November 2026), with a plain folder standing in for the drive:
inside, the home holds only the way to the code, `.ssh` is not there, no X11 socket and no
`DISPLAY`, the code and `run` are read-only, the hidden `SEITON_Test/Projekte` is empty (8 entries
outside), the idle time comes over the session bus, and the clock writes its rows through the
bound folder. The drive itself could not be mounted from the development tool (its processes run
with `no_new_privs`, so the setuid `fusermount` is refused); that is to be tried from a normal
session.

### 7.3 What the prototype does not close

- **X11** is not needed where the desktop's idle monitor answers over D-Bus (Cinnamon, GNOME,
  KDE): the sandbox has no X socket. Only the last resort, the XScreenSaver extension, would need
  it, and on X11 any client with the socket can read the keyboard (the hole Flatpak has on X11).
  The sandbox does not give it.
- **D-Bus**: idle time and inhibitors are asked over the session bus. Without a filter
  (Flatpak's `xdg-dbus-proxy`) the clock could also talk to other services. A filter is a later
  step.
- **Outside the home**, the system is visible read-only, except what is hidden (`/tmp`, the
  runtime folder, the projects root). Other disks under `/media` or `/mnt` are to be hidden too.
- A program started past SEITON is not in the fence.

### 7.4 What the ACLs need

The clock writes as the person. In many projects a person may not write `0_Admin` (in the
standard template only the folder's own role may). The rule needed is **"everyone writes their
own time file"**: a right on a file named after oneself. This is new in the ACLs:

```markdown
## Everyone
- /0_Admin/Zeitaufwand/{Self}.md: read, write
```

`## Everyone` holds rules for every person in `# Users`, and `{Self}` is the asking person, as
`{Folder}` is the folder's role (decided 2026-11-16; "Designdocument ACLs.md", 2.5). Reading
the others' files is then a normal right (for example the project's admin reads all of
`0_Admin/Zeitaufwand/`).

## 8. Later: the Phone

Not part of the first steps, written down so the design leaves room for it:

- **Switching projects on the phone**, for holidays or for work on the road from one job to the
  next. The phone writes the active project into the person's own place in the cloud, and the
  clock and the Headline follow.
- **Photos by the time line**: the Nextcloud app already uploads photos into a folder. SEITON
  puts each photo, by the time it was taken, into the project that was active then (the time
  files are the time line): `9_Dokumentation/92_Bilder`. A photo from a time without a project
  stays in the inbox.
- **Receipts**: photographed in the app as a receipt, they land in
  `4_Finanz/44_Rechnungen/Eingang` of the active project, and the time screen can add the trip
  as a `nachgetragen` stretch.
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
5. **The widget and the time screen** (decided 2026-11-17): the time tracking is a program of its
   own that puts itself into the Headline as a widget, and may be missing or replaced; the
   Headline writes the active project; the time screen is the time tracking's own window, with
   the person's rights, and holds its settings (apps/Scope/Designdocument Headline.md, 3a). The last
   three projects worked on with their time, and "More", in the Headline's panel.
6. Later: the phone (section 8).

## 10. Decisions (16 November 2026)

1. **Time zones**: readability. Local time, an offset only away from home (section 2.1; the
   offset is not written yet).
2. **Columns**: `Datum | Von | Dauer | Art | Notiz`, no "Bis": it is redundant, and it confuses
   when summer time begins or ends. In the user's language, SEITON reads German and English.
3. **`{Self}`** in the ACLs, in a new section `## Everyone` (section 7.4).
4. **Several computers** at once: one file per person all the same; the rare conflict is
   accepted. When the cloud leaves a conflict copy (`Oliver (conflicted copy ...).md`), the time
   screen shows it and offers to merge it. Built so far: the overview says how many conflict
   copies there are and counts them apart; merging is not built.
5. **Rounding**: configurable, only in the overview and the export (section 5).
