# Test Machine

Several people play through the tutorial one after the other on one computer
(`scripts/testrun.py`, decided 2026-10-26). Each tester gets a fresh copy of the tutorial,
writes comments into one note, and at the end clicks **"✅ Bin fertig – Rechner für den
nächsten Tester vorbereiten"** in lesson 16. Their work is collected, everything is reset,
and lesson 1 opens for the next tester.

## Setting it up (once)

1. Linux with an X11 session (Cinnamon, GNOME on Xorg, ...), one user account for all testers.
2. The repository, e.g. `~/SEITON`, installed with `./install.sh` (system packages, its venv,
   launchers, and the templates Standard, Person, Firma, Development to `~/.seiton/Templates`,
   which the exercises need: the suggested folders in lesson 7, the P button). For the
   tutorial's example data also `sudo apt install ffmpeg wmctrl` and
   `~/.local/share/seiton/venv/bin/pip install reportlab`. The steps below run with SEITON's
   Python, `PY=~/.local/share/seiton/venv/bin/python`.
   Copying it from a development machine: never copy the lens drive `SEITON_Test/Perspektiven`
   (a mounted drive), e.g. `rsync -a --exclude Perspektiven`.
3. A plain `~/Templates` is never taken (on Linux it is the desktop's folder for new
   documents).
4. Open the tutorial at every login, PostFix as the program for Markdown notes (a double click on
   a lesson opens PostFix with its links, not a text editor), and SunTree (lesson 15) ready for
   Ctrl+Alt+Space:
   ```
   $PY scripts/testrun.py install
   $PY SunTree/install_autostart.py ~/SEITON-Tutorial/DE
   ```
5. Make the first copy and open lesson 1: `$PY scripts/testrun.py start`.
6. Check: lesson 1 shows in PostFix; in lesson 7, "▶ Übung öffnen" opens Scope and the file
   browser side by side, with the pale suggested folders (then the templates are found);
   "💬 Kommentar zu dieser Lektion" opens "Meine Kommentare".

## What a tester sees

The tutorial is its own root (`Learning SEITON/.seiton`: Standard template, no ACLs of its
own), so "Zum Projekt machen" (the P button) works in the lessons although no "Projekte" lies
above it. Projects made in the lessons get the example rights of the Standard template
(`templates/Standard/.seiton/ACLs.md`: `## Folder`, `## Everyone`, the role `Buchhaltung` on
`4_Finanz`): the rights panel shows after the first folder is born (lesson 7), not only in
lesson 11.

- PostFix with lesson 1 of the copy (`~/SEITON-Tutorial`, German). The repository is never
  touched.
- Under every lesson "💬 Kommentar zu dieser Lektion": it opens the note "Meine Kommentare"
  as a sticky note and adds a heading for the lesson.
- Exercise links ("▶ Übung öffnen") open Scope in the exercise folder.
- At the end of lesson 16 "✅ Bin fertig": asks first, with an optional name.

## What "Bin fertig" does

1. Closes the Scope and PostFix windows showing the copy (other windows stay).
2. Collects into `~/SEITON-Testergebnisse/<date>_<time>_<name or Tester_N>/`:
   - `Meine Kommentare.md` - the comments,
   - `Änderungen.md` - every note added, changed (with a diff) or gone (moved or deleted),
   - `Neu/`, `Geändert/` - those files themselves,
   - `Einstellungen/` - the tester's SEITON and PostFix settings,
   - `Zusammenfassung.md` - name, start, end, counts.
   PostFix's window place in a note's front matter (`window_...`) is no change.
3. Deletes the copy and makes a fresh one; resets `~/.config/seiton` and `~/.config/PostFixDev`.
4. Opens lesson 1.

By hand: `$PY scripts/testrun.py finish --name "Anna"` (add `--no-restart` to only
collect and reset), `$PY scripts/testrun.py prepare` (reset without collecting).
`SEITON_TUTORIAL_DIR` and `SEITON_RESULTS_DIR` move the copy and the results.

## Safety

- `prepare` only deletes a folder it made itself (marker file `.seiton-tutorial-copy`).
- The copy is built from the lessons as last committed (`git archive HEAD`), not from the
  working files: a lesson opened in the repository itself (PostFix saves window places into
  notes) never reaches a tester. Without git the working files are copied.
- "Bin fertig" and "Kommentar" only work in notes inside such a copy, and "Bin fertig" asks.
- Exercise links only open folders inside their own lesson.
- Scope opened by an exercise link starts without the lens drive "Perspektiven" (at a
  lesson's project it would mount it inside the copy). Should a drive still be mounted in
  the copy, "Bin fertig" unmounts it before collecting and deleting - or deletes nothing.

## Known limits

- The classic file browser opened by lesson 7 stays open after "Bin fertig" (on the old,
  deleted folder); testers close it themselves.
- Resetting `~/.config/seiton` also takes the clock's widget registration the installer wrote
  (`headline/widgets/clock.json`): after the first "Bin fertig" the Headline shows no time
  widget until `./install.sh` runs again. The time screen still opens (`seiton-time`).
- The links work in PostFix only (not in Obsidian); English lessons have no comment links.
- Following "zur nächsten Lektion" shows the next lesson in the same PostFix window, but
  editing still applies to the note opened first - comments therefore go into their own note.

