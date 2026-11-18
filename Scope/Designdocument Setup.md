# Scope - Setup on the Back

The settings of MyOS's programs - Scope, the Headline (the minimal view M, becoming a tool of
its own docked at the top of the screen) and SunTree - are made on the back of Scope.
Decided on 2026-10-26.

## 1. The Picture

- **⚙ Setup** (in M's tools, later wherever Scope's top bar items go) flips Scope over: the
  window turns about its vertical axis (about 0.9 s: slow enough to be seen), and its back shows the settings. ⚙ on
  the back flips it back. Nothing opens or closes - the settings are the back of the thing
  they set. Both ways it turns in the same sense - one swing, and the panel turns through -
  and "⚙ Done" stands top left on the back, where ⚙ is on the front.
- **Tabs** on the back: **General**, **Scope**, **Headline**, **SunTree**.
- A change takes effect at once where it can (light/dark), and is kept: Scope today forgets
  light/dark and the language when it closes.

## 2. The Tabs

| Tab | Holds | When |
|---|---|---|
| General | light / dark, language, how pale embryos are - for the user "suggested MyOS folders" (live preview: a present folder beside a suggestion in each style, text, small and large icon, drawn as Scope's rows draw them; Scope follows at once, SunTree when it appears, 2026-10-26), and their badges, with a slider of their own (70 % by default); the colours: follow the system, or a scheme of one's own (section 5) | step 1; colours: steps 2, 3 |
| Scope | everything the rows' display menus held (the menus are gone, 2026-10-26): left one picture of a row as it really looks (the path bar's segments pushed together like tabs, its folders with a suggestion and a hidden one, the preview below), right check items and choices it follows - the two rows on/off (the projects row off by default; M keeps its CWD button), for both rows alike the path bar, suggested MyOS folders, hidden folders, the preview and its background, the folder style of each row, the preview's behaviour (reopen at once, timing soft / balanced / quick) | built |
| Headline | what concerns the docked tool: its tools, docking | with the Headline |
| SunTree | the crown's values (SunTree/Designdocument Krone.md, 5): line T, inner radius, Enter, Leave, fish-eye, softness, edge | step 1 |

Each value shows its default and can be set back to it.

**The small crown** (2026-10-26): left on the SunTree tab, a half crown with sample folders,
drawn with SunTree's own arithmetic (`Scope/CrownPreview.qml` on `SunTree/js/Crown.js`). Softly
glowing lines show the borders - inner radius (grey), line T (amber), where drawing in begins
(the field's edge, turquoise) and where it ends (the next level's start, magenta); each slider
has a dot in its line's colour. The exit at the edge is the rim running on past the first and
last folder, towards the stem (green).

One plays with it oneself (2026-10-26, a dive played at every change confused): the hand over
it moves the pointer as in SunTree - from the hollow out to the rim through a level and a half,
up and down through the folders - and the fan follows with the softness set; the hand shows
as a ring, the pointer SunTree would put as a dot. Moving a border
plays nothing, the line just moves. Over a slider its demo plays, in a loop: for the borders
the pointer goes where the value counts and the line pulses; over the magnifier the fan
breathes open and closed around the value set; over softness the hand (a ring) glides up and
down and the fan with its pointer follows - far behind and not to the ends when soft, close
to the hand when direct (jumps showed too little: the fan had caught up before the next); over the exit the pointer goes to the first folder
and the green rim pulses. Taking a slider stops it - the fan just follows the slider - and it
stays quiet until the mouse has left the row. A new value never starts anything by itself.
Half the stem is hinted on its left, the CWD oval's round end in the hollow, so one sees at
once what it is.

**Words for the user** (2026-10-26): crown, drawing in and line T mean nothing to the user. On
the tab SunTree is "the folder fan for quick dropping" and drawing in is "the change"; the
design documents keep their words. The sliders go from the inside out, as their lines lie in
the small fan, then the three that are no line; a line under each says what it does:

| Setting | Name | Says |
|---|---|---|
| inner | Size of the middle | the empty middle at the stem: every level starts there, back there the fan lets go |
| leave | Landing | how far among the subfolders one already is after the change |
| lineT | Way per level | how far the mouse moves outward until the folder fills the fan and one goes a level deeper |
| enter | Change begins | how deep in the folder the pointer is when the change into its subfolders begins |
| lens | Magnifier | how much the folder under the pointer is enlarged already at the start of a level |
| softness | Softness | how fast everything follows the hand (not in the small fan) |
| edge | Exit at the edge | how far one pushes past the first or last folder until the fan lets go (not in the small fan) |

## 3. One Settings File for All

- `~/.config/seiton/seiton.conf` (until November 2026 `~/.config/MyOS/MyOS.conf`), groups
  `General`, `Scope`, `Headline`, `SunTree`. Scope writes it; SunTree reads it each time it appears, so a change on the back
  of Scope shows the next time SunTree is called (it runs as a program of its own).
- `core/settings.py` holds the settings with their defaults and ranges in one place; both
  programs read through it. Values out of range or of the wrong kind fall back to the
  default (the file can be edited by hand).
- Scope's own `Scope.conf` (list columns, sorting) stays as it is.

## 4. Steps

1. `core/settings.py`, the flip with the tabs **General** (light/dark, language) and
   **SunTree** (its values); SunTree reads them on appearing; Scope keeps light/dark and the
   language. **Built** (2026-10-26): `Scope/SetupPage.qml` is the back
   (the Scope tab says what will come there; the Headline's tab left on 2026-11-18 - it keeps its
   own settings, `Headline/SettingsWindow.qml`); ⚙ in M's tools and, until the top
   bar goes, in the top bar flips it (a `Rotation` of the window's content about the vertical
   axis, the back taking over at the quarter turn); Scope's backend offers `setting`,
   `setSetting`, `settingDefault`, `settingLimits`, `resetSetting`; SunTree reads its group
   in `turnedTo` (`crownSettings`).
2. Colour schemes to choose: the 34 colours move out of Scope's `main.qml` into scheme files
   (Dark, Light). **Moved** (2026-11-06, nothing looks different): `core/schemes/dark.json` and
   `light.json`, read through `core/color_schemes.py`; `main.qml` keeps its names and takes the
   values from `schemeColors`. **Scattered colours gathered** (2026-11-06): the back's own colours,
   selection, drop highlight, the lens frame and the ACL dialogs are in the schemes; the components
   no longer keep defaults of their own. The middle of the FilesPanel is `filesPanelCenter`, one
   per scheme: it was a veil of 20 % over the frame (white on dark, black on light), so both themes
   met in a middle grey, and it lay over the files, dulling them too. Now it lies under them and
   the project's colour shows through it (0.52).
   Fixed on purpose: tag colours and chips, ACL chips (their text is worked out from their colour),
   badges, signal reds, the lines of the small crown (the sliders' marks show the same colours).
   **SunTree and the small crown on the scheme** (2026-11-06): 31 colours of their own in the
   schemes (`crown…`, `stem…`, `notice…`, `lens…`), not listed on General. SunTree reads the scheme
   each time it appears (`colorScheme`), as it does its values; the frame of its lens is the
   `lensFrame` of the list. Dark looks as before, Light is new. A project looks the same in every
   scheme, so text on a project's colour turns black or white where the scheme's would be unreadable
   (contrast under 3). The CWD glows as Scope marks it (`FBUtils.cwdMarkColor`). The notice after a
   drop stays dark in both schemes, so it stands out on a light desktop.
   **The choice on General** (2026-11-06): under Appearance a small Scope for each scheme, a click
   puts it on; `General/darkTheme` still says which, until a third scheme makes `General/colorScheme`
   worth it.
3. Colour schemes to edit: change colours, keep them as a scheme of one's own. **Begun**
   (2026-11-06): under the choice eleven colours in four groups (window: background, text; files area:
   background; markings: selected files, dropping on a folder, frame of the lens; folder rows:
   their two backgrounds, path bar, folders, current folder and frame), each one line: its name
   and its little box; no way back beside it, "Reset all colours" under the list. A click on the box opens Qt's colour picker
   (colour field, hue, Hex/RGB/HSV/HSL, opacity for the two see-through colours; not the native one, so it is the same everywhere and Scope
   follows while picking; sliders would be a mess at ten colours or more). A drag on the box
   fine-tunes: right lighter, left darker, up more saturated, down less (300 px the full way, the
   box stays where it is, a drag opens no picker, opacity stays). It counts at once
   and for the scheme worn alone, kept in `~/.config/seiton/schemes/<scheme>.json` over the shipped
   file (`core/color_schemes.py`). To come: a scheme of one's own.
   **Steps 2 and 3 go on as section 5** (decided 2026-11-15): no third shipped scheme; the
   colours follow the system, and the eleven boxes become the place for schemes of one's own.
   The frame of the FilesPanel has the colour of the current folder's tab (`folderCwpTint`, for a
   project its colour), no mix; the tab is that colour at its foot and a little lighter at its
   top. The side texts (`textMuted`, `textSoft`) are worked out from `text` and `bg`.
4. The **Scope** and **Headline** tabs, as the top bar is taken away.
   Begun (2026-10-26): light/dark and the language left the top bar (they are on General); the
   two rows (projects, MyOS folders) are switched on the Scope tab and kept in the settings
   file (`Scope/projectsRow`, `Scope/templatesRow`) - views of their own are to come; "Files
   50 %" (a transparency test) is gone with the files panel's half transparency; "Give project
   a theme" and "Enable sorting" (slipped in from development) are gone - a sort rule is now
   put in by hand (`.MyOS/Sort.md`). Then (2026-10-26): the filter moved to the Scope tab (a
   button showing the active filter opens its menu), narrow mode is gone, the edge-dock switch
   is gone (its code waits for the Headline). Left in the bar: ⚙, far left, and M. (⚙ cannot go
   into the window's title bar: the window manager draws it; a title bar of Scope's own would
   have to redo moving, resizing and snapping - perhaps with the Headline.)

## 5. Colours: Follow the System (decided 2026-11-15)

How it is done today: light, dark or automatic (by time of day) and high contrast are set once in
the system, and apps follow; personal taste is one accent colour, from which the rest is worked
out (Apple, Windows, GNOME, KDE, Material You). Many themes side by side (dark, high contrast,
green, blue …) that do not fit together are left to tinkerers. SEITON does the same.

- **Scope and SunTree follow the system.** "System" is the default and stands first: light or
  dark, high contrast and the accent colour come from the freedesktop portal
  (`org.freedesktop.appearance`), the rest of the palette from Qt (`QPalette`; full under KDE,
  approximate under GNOME). No switching by time of our own: the system does that, the program
  follows. For now only Scope and SunTree take the desktop's colours, not the whole desktop.
- **A few base values, the shades worked out.** Base values: background and text, the accent,
  the project's colour. From them the many shades follow by rules, worked out in OKLCH so they
  fit together under any system colour and stay readable:

  | Shade | from |
  |---|---|
  | path bar, tabs | background, a little lighter or darker |
  | suggested folders (embryos) | text, with the paleness set on General |
  | selection, dropping on a folder, frame of the lens | accent |
  | current folder, frame of the FilesPanel | project colour |
  | side texts | text and background (so already) |
  | SunTree's crown and the small crown | the same base values |

  Which of today's colours is a base value, derived or fixed: `Scope/Colour inventory.md`.
  High contrast is no scheme of its own: the same rules with wider steps. The 34 fixed colours
  of `dark.json` and `light.json` become base values and rules; what still has to be fixed by
  hand stays as an exception.
- **The project colour is the room.** It tints Scope as today; instead of the fixed 52 % in the
  middle of the FilesPanel a slider says how strongly a room colours (the test run showed that at
  52 % white cannot be reached). Light or dark never changes with the room.
- **Schemes of one's own, one level lower.** Under "System" any number of schemes of one's own,
  each a file in `~/.config/seiton/schemes/`. One begins from "System", from today's Light or
  Dark or from another scheme of one's own.
  - A scheme of one's own has **one set of colours, fixed**: no light and dark side, so it does
    not follow the time of day.
  - It follows **nothing of the system**, not the accent either: one may tinker freely, with base
    values and, on top, each shade (today's eleven boxes).
  - **Default** puts a colour back to what the system gives.
- **Checked (2026-11-15)** on Linux Mint 21.3, Cinnamon, X11, PySide6 6.10.2 from pip:
  - The palette is read right from the GTK theme (Mint-L-Darker-Aqua): window `#f9f9f9`, text
    `#303030`, highlight `#6cabcd`.
  - `colorScheme` says **Dark** for a light theme: the portal says "no preference", and Qt then
    guesses from the theme's name ("Darker" means only the dark header bar).
  - `QPalette.Accent` is not set (black): Mint 21.3's portal gives no accent and no contrast. The
    theme's accent is in `Highlight`.
  - Contrast: `contrastPreference` is `NoPreference`.
  - `QT_QPA_PLATFORMTHEME=qt5ct` is set, but there is no such plugin for Qt 6; Qt falls back to its
    GTK3 plugin without a word (so does `xdgdesktopportal`). Pip's PySide6 can load only the
    plugins it brings (GTK3, portal): under KDE the full Plasma palette would come only through the
    portal.
  - Qt listens to the portal's changes; whether Scope follows a theme switched while it runs is
    not tried yet (it would mean switching the desktop's theme).
- **So:** light or dark from the palette itself (window background lighter than text = light);
  `colorScheme` only when the portal says light or dark outright. Accent: `Accent` when set,
  else `Highlight`. Base values from `QPalette`: `Window`, `WindowText`, `Base`, `Text`,
  `Highlight`.

## 6. Open

- Later on the Headline: signing in / switching user, switching off.
- Answered (2026-11-06): SunTree takes its colours from the scheme too.
