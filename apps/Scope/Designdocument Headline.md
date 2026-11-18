# Headline - Scope's Minimal View as a Tool of Its Own

Started 2026-11-17. The minimal view M inside Scope was a trial (2026-10-25 to 10-26, E4 in the
ProjectLogbook); now it becomes a tool of its own, made "nice and round". M inside Scope stays
as it is until the Headline replaces it (state 2026-11-18: M is still in Scope).

What is built and what not: section 4, Steps. Sections 1 to 3a describe the picture, not all of
it is there yet.

## 1. The Picture

The Headline is SEITON at the screen's edge: where one is (the project, the current folder), the
project's standard folders, the perspectives, a few buttons. One click there, and one is in the
right folder, or has the lens on at the right place.

It lives in one of two places, chosen in its own settings (the Setup button of its tools), as a
taskbar can be:

| Place | Looks like | Folders shown |
|---|---|---|
| **The top edge** | one line across the whole width | in a row, as many as fit; the rest behind a » at the end |
| **The taskbar** | a button with SEITON's box; a click opens a panel above it, as the start menu does | in a vertical list |

At the top edge, as with a taskbar, either of two (Setup):

- **Always there:** the line keeps its room; maximised windows stop below it.
- **Hides itself** (the default since 2026-11-18): the line slides in from above when the pointer
  touches the top edge (at once, over the whole width), over all other windows, and slides out
  about 0.5 s after the pointer has left it (ProjectLogbook, E4 step 2). It keeps no room.

The panel from the taskbar may later come at the top edge too (a click on the line's SEITON box),
for whoever prefers the folders as a list.

## 2. What It Shows

**The top line**, left to right:

1. SEITON's box: the panel (section 1), Setup.
2. The current folder (CWD) as a button; hovering opens the path to climb (the cascade, as M's
   CWD dropdown today, up to the projects root).
3. The project's standard folders, in a row, with their badges; suggested ones (embryos) pale, as
   in Scope; as many as fit, the rest behind ».
4. The perspectives of the root (the favourites of Designdocument Perspective Resolver MVP.md,
   A11): an entry each; a click puts the lens on there, a click on the active one takes it off.
5. Right: the buttons - clipboard, search, light/dark (M's tools today, apps/Scope/CwdTools.qml).
6. Far right: the **widgets** other programs have put in (section 3a), and the **person**
   (login, logout). The first widget is the time tracking: `Küche · 2:15`, grey when the clock
   stands; its question ("Still working on *Küche*?") appears at it; a click opens its time
   screen.

**The panel** (from the taskbar), top to bottom:

1. The path to where one is, each part clickable.
2. The project's standard folders as a list (icon, badge, name); the lens' frame where it is on.
3. The perspectives.
4. A row of buttons: clipboard, search, new project, Setup.
5. The widgets and the person, as in the line. A widget may bring a short list: the time
   tracking shows the last three projects worked on with their time, `Küche 2:30`,
   `Dachboden 12:40`, `Auto 0:20`, and "More"; a click on one goes there, "More" opens the time
   screen with all of them, to see and correct.

Both show the same: one model, two ways of drawing it.

## 3. How It Is Built

- **A program of its own**, as SunTree is: `apps/Headline/` beside `apps/Scope/` and `examples/SunTree/`, started at
  login. It shares where one is with Scope and SunTree through the session of the lens
  (`daemon/lens_link.py`): change the folder in one, and the others follow.
- **Popups are windows of their own.** In M today the dropdowns and the cascade are items in
  Scope's window (`floatingPool`): in a line 30 px high they would be cut off at its edge. Each
  dropdown, cascade and menu becomes a small window of its own.
- **They take no clicks from each other** (2026-11-17, seen on the desktop): the dropdowns and
  the cascade are tool tip windows, not popups - on X11 a second popup took every click, and
  one could never click back in the way up. They close once the pointer has left them and the
  line for about 0.6 s, or after a choice; a whole row takes the click, as in a menu. Only the
  panel is a popup (a click outside closes it); it has no cascade.
- **They open towards the room.** Where the Headline sits tells the direction: from the top edge
  down, from a taskbar at the bottom up, at the left or right towards the middle. Qt gives the
  screen and the room left by the panels (`QScreen.geometry`, `availableGeometry`); from them,
  and from where the anchor is, the direction follows. One rule for every popup.
- **One model, two drawings:** what to show (path, standard folders with badges and embryos,
  perspectives, buttons) is worked out once, in Python on `ScopeApi` (`core/scope_api.py`), as
  Scope's rows do; the line and the panel only draw it.
- **Not FolderBrowser.** `apps/Scope/FolderBrowser.qml` (4,700 lines) carries Scope's two rows with
  everything they can (vertical view, preview, search field, rename, dragging). The Headline gets
  small components of its own that draw the model; what both need (a folder's icon with badge
  and embryo look, the lens' frame) is split out of FolderBrowser into shared files, so Scope and
  the Headline look alike.
- **Dragging onto a folder** (to file something there) works in the line and in the panel, as in
  Scope and SunTree: what is dropped is moved there through `ScopeApi.move_entries` (the ACLs,
  filing by date), a suggested folder is born by it, folders are asked about first. Built
  2026-11-18 (review H9): the CWD button, the standard folders, the rows of the dropdowns and the
  panel's path and folders take drops (`HeadlineModel.plan_drop/move`, `apps/Headline/DropAsk.qml`).
- **A click alone bears no embryo** (decided 2026-11-17, for Scope, SunTree and the Headline
  alike): a suggested folder comes into being only by a drop onto it, or by making something in
  it (right click: new note, new folder). Going there, looking at it, putting the lens on it
  leave the disk as it was (`core/tests/unit/test_embryo_click_bears_nothing.py`).

### The desktop

| What | X11 (Cinnamon, today) | Wayland (later, see docs/Portierung auf andere LINUX Systeme.md) |
|---|---|---|
| Line keeps its room | window type dock (`_NET_WM_WINDOW_TYPE_DOCK`) and `_NET_WM_STRUT_PARTIAL`, set with python-xlib | layer-shell (KDE, wlroots); not on GNOME |
| Line hides itself | a thin window at the edge waits for the pointer | the same through layer-shell |
| The button in the taskbar | a Cinnamon applet (JavaScript): only a button with the box; a click tells the Headline to open its panel at the button | KDE: a plasmoid (QML); GNOME: an extension; XFCE: a plugin - each only a button |

Until the applet is there, a launcher pinned to the taskbar and the shortcut open the panel at the
pointer.

The applet tells the Headline through a small socket or D-Bus where its button is and which edge
the panel stands on; the Headline opens the panel there, towards the room.

## 3a. Widgets: Time Tracking and Others (decided 2026-11-17)

The time tracking is a program of its own, not a part of SEITON's Headline: it puts itself into
the Headline as a widget. It may be missing, or be replaced by another time tracking; then its
place stays empty, or the other one stands there. So the Headline does not know the clock, it
knows widgets.

**What the Headline gives every widget:** where one is. On every change of project it writes the
active project (`core/clock_sources.write_active`, `$XDG_RUNTIME_DIR/seiton/active-project.json`;
`apps/Headline/model.py` calls it on each change of project). Whoever wants, reads it - the clock
does every 15 s.

**How a widget comes in** (built 2026-11-17 with the clock, `apps/Headline/widgets.py`):

- **It registers** with a small file in `~/.config/seiton/headline/widgets/<name>.json`: its
  name, where its view lies, the command that opens its own screen. The installer of the widget
  writes it, the uninstaller takes it away; the Headline shows what is registered (in Setup, tab
  Headline: on/off, order - not built yet).
- **It shows** what its view file says (a folder of its own in `$XDG_RUNTIME_DIR/<name>/`,
  `view.json`): a short text (`Küche · 2:15`), a state (calm, active, asking), a tooltip, perhaps a
  question with answers ("Still working on *Küche*?" - Yes / No), perhaps a short list (the
  projects worked on last, each with its text and its path). The widget rewrites the file when
  something changes; the Headline watches it.
- **Its project once** (2026-11-18): a widget about a project names it (`project`, its path)
  and gives its text without it (`short`, `2:15`). While the Headline is in that project, which
  stands already at the left of the line, it shows the short text and names the project in the
  tooltip; elsewhere the full text.
- **As an icon in the CWD's tab** (2026-11-18): a widget may name an icon the Headline draws
  (`icon`, so far `stopwatch`). It then sits as that icon at the end of the CWD's tab instead of
  a button at the right: it beats like a heart while active (the line is mostly hidden: one sees
  at once that it counts), is pale while calm, red and struck through with `warn` (the clock
  stopped by hand). Its text is the tooltip - the clock says its time there as a duration
  ("DesertGreener: heute 2:15 h"), not like a time of day. A click opens its screen. At the right
  only its question stands, while it asks; so the right stays free and no standard folder hides.
- **It is told** what the user did by command files dropped into the same folder (`yes`, `no`,
  `start`, `stop`); the widget looks for them. In the clock's sandbox only this folder is
  writable (`cli/seiton_clock.py`, its binds).
- **Its screen is its own.** A click on the widget runs its command: the time screen (Now,
  Entries, Overview; Designdocument Time.md, 5) is a small window of the time tracking itself,
  with the person's own rights (it edits and deletes rows in `core/time_log.py`, written anew and
  swapped in with `os.replace`), not the sandboxed clock and not the Headline. Its settings
  (pause limit, automatic resume, the dead man's button, rounding; already in `core/settings.py`,
  section Time) are on that screen.
- **No widget, no gap:** if none is registered or its view is missing or stale, nothing shows.

**Who starts the clock:** the installer's autostart entry (`./install.sh --clock`). Built
besides: the Headline's tool "Time tracking" opens the time screen even when no clock runs, and
the time screen can start the clock (`apps/Time/TimeScreen.py`, `startClock`). Not built: a grey
"Clock not running" widget whose click starts it - without a clock, its widget does not show.

## 4. Steps

1. **The Headline as a program with its model and its own popup windows:** a window of its own,
   the top line drawn from the model (CWD, standard folders, buttons), the CWD dropdown and the
   cascade as windows that open towards the room. Tested offscreen, as Scope (TDD, harnesses).
2. **The top edge:** always there (dock, strut) or hiding itself; set in its own settings
   (since 2026-11-18; before, a tab in Scope's Setup).
   Built 2026-11-17: `apps/Headline/x11_dock.py` (dock type, strut), the setting `Headline/dock`
   (keep, hide), read anew every second; hiding, the line is a 2 px edge that opens at once and
   goes 0.5 s after the pointer left, not while a dropdown is open. Since 2026-11-18 it slides
   in and out (150 ms, the window see-through meanwhile) and hiding is the default.
2a. **Widgets:** write_active; registering, view, command files (section 3a); the clock as the
   first widget, with its time screen as its own window, and its start at login.
   Built 2026-11-17: `apps/Headline/widgets.py` and the active project (part 1);
   `core/clock_widget.py`, the clock's view and commands, the time in all beside the projects
   worked on last (part 2); `apps/Time/`, the time screen (part 3); `seiton-clock` without a root
   takes the first below the home folder (one level, else two: `core.scope_api.roots_below`), one clock per user (a lock), `./install.sh --clock`
   starts it at login (part 4). Not yet tried with FUSE and bubblewrap on the desktop.
3. **The panel:** the same model as a vertical list, with the perspectives and the buttons;
   opened at the pointer (launcher, shortcut).
   Built 2026-11-17: `apps/Headline/Panel.qml` - the path, the standard folders, the root's
   perspectives (`.seiton/Perspectives.md`; a click puts that lens on, on the worn one takes it
   off), "Open in Scope"; it opens towards the room (above a taskbar upwards) and a click
   outside closes it. One Headline per user (`apps/Headline/instance.py`, as PostFix): a later start,
   `Headline.py --panel`, hands "open the panel" to the one running, at the pointer or at an
   anchor (for the applet). Setup: "Where" - the top edge, or from the taskbar (no line then).
   Built since: the widgets in the panel (with their question, the last three, "More") and a
   row of buttons (`apps/Headline/Tools.qml`: Open in Scope, Setup, Search, Clipboard, Time tracking,
   Light / dark). Still open in the panel: the person, new project.
4. **The Cinnamon applet:** the button in the taskbar that opens the panel above itself.
   Built 2026-11-17: `apps/Headline/cinnamon/seiton-headline@seiton/` - a button with SEITON's box;
   a click runs `seiton-headline --panel --anchor x,y,w,h` with where the button is (device
   pixels, the Headline turns them into Qt's logical ones). The installer writes the launcher
   `seiton-headline`, a menu entry "SEITON Panel" (`--panel`, to pin to any taskbar), on Cinnamon
   the applet (the user adds it: right click on the panel, Applets), and with `--headline` the
   Headline at login; uninstalling takes all of it.
4a. **The line, state 2026-11-18:** built are the CWD button with the cascade, the standard
   folders with », the widgets (the question with its answers; hiding itself, the line comes
   out while a widget asks - review 2026-11-18, H8). The buttons
   lie for now on top of the CWD dropdown (`apps/Headline/Tools.qml`, as M's tools). Still open in the
   line: SEITON's box, the perspectives, the person. Suggested folders (embryos) show pale and
   do nothing on a click; a drop onto them bears them (section 3). Not yet tried on the real
   desktop: a drag from Nemo onto the dock line, and onto the panel (a popup).
5. Later: KDE's plasmoid; Wayland.

### Its own settings (decided 2026-11-18)

The Headline is a program of its own and SEITON's visual component, always there: the master for
everything else. Scope is only a first file browser for SEITON; others may follow. So the
Headline keeps its own settings, not a tab in Scope's Setup: `apps/Headline/SettingsWindow.qml`, opened
by the Setup button of its tools. It holds where it sits, how it sits at the top edge, and
SEITON's look (light, dark), which Scope and SunTree follow. What is SEITON-wide beyond that (the
language, the paleness of suggested folders, asking before moving folders) is still in Scope's
Setup for now ("More settings in Scope") and should move here in time. Its window may set only
its own keys (`HeadlineBackend.OWN_SETTINGS`); a change takes effect at once.

## 5. Open

- The name: "Headline" fits the top edge, less a panel from the taskbar (docs/Vision/Namen der
  Werkzeuge.md is choosing Japanese names).
- What shows when one is not in a project (no root found below, A11): the roots? nothing?
- Whether the line also shows the projects of the current level (the "shelf" of E4).
- Several screens: the line on one, or on each.
