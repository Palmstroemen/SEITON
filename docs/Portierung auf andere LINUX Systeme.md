# Portierung auf andere Linux-Systeme

Stand 2026-11-16. Nichts davon ist gebaut. SEITON ist auf Linux Mint 21 (Ubuntu 22.04, Cinnamon,
X11) entstanden. Hier steht, was es braucht, damit es auf möglichst vielen anderen Linux-Systemen
läuft: openSUSE, Fedora, Arch, Manjaro und andere.

**Kurz:** Die Distribution ist der kleinere Teil. Mehr Arbeit machen zwei andere Fragen: welcher
Desktop läuft (Cinnamon, GNOME, KDE, XFCE …) und ob er unter X11 oder Wayland läuft.

## 1. Die Distribution: wenig Aufwand

SEITON ist Python mit PySide6 und FUSE. Das läuft auf jeder heutigen Distribution. Unterschiedlich
ist nur, wie man es installiert.

- **Paketnamen.** `install.sh` kennt nur `apt-get`. Nötig ist eine kleine Weiche für `dnf`
  (Fedora), `zypper` (openSUSE) und `pacman` (Arch, Manjaro).
- **libfuse 2.** `fusepy` braucht libfuse 2, nicht libfuse 3. Das Paket heißt je nach Distribution
  `fuse`, `fuse2` oder `fuse-libs`. Auf neueren Systemen ist es oft nicht vorinstalliert.
- **pip ins System ist verboten (PEP 668).** Arch, Manjaro, Fedora, Debian 12 und Ubuntu 24.04
  lehnen `pip install --user` ab („externally managed environment“). Auf Mint 21 fällt das nur
  deshalb nicht auf, weil es auf Ubuntu 22.04 beruht. Spätestens mit Mint 22 trifft es auch uns.
  Die Lösung ist ein eigenes venv für SEITON, etwa `~/.local/share/seiton/venv`. Das ist ohnehin
  sauberer: Jede Installation hat ihre eigene, bekannte PySide6-Version und wird nicht von
  System-Qt oder anderen pip-Paketen gestört (vgl. die Abstürze von PostFix auf dem ACER mit
  einer neueren Qt-Version, 2026-11-16).

Aufwand: etwa ein bis zwei Tage für einen Installer, der auf allen Distributionen gleich arbeitet.
Getestet wird er in VMs oder Containern der vier Familien (Debian/Ubuntu, Fedora, openSUSE, Arch).

## 2. Der Desktop: mittlerer Aufwand

- **Desk** (Hintergrund, Theme, Leiste) kennt heute Cinnamon, GNOME und KDE
  (`core/desktop_backends`, Wahl nach `XDG_CURRENT_DESKTOP`). Es fehlen XFCE (`xfconf-query`) und
  MATE (`gsettings`, ähnlich wie Cinnamon), vielleicht noch Budgie. Pro Desktop ist das ein Backend
  mit Tests, etwa ein Tag. Ohne passendes Backend bleibt Desk aus, SEITON läuft trotzdem.
- **Thumbnailer** für die Vorschau von `.md`-Dateien (`installer/install-thumbnailer.sh`). Er folgt
  dem freedesktop-Standard, das reicht für Nemo, Nautilus und Caja. KDEs Dolphin braucht einen
  eigenen KIO-Thumbnailer, das wäre ein Extra.

## 3. Wayland: der eigentliche Brocken

Fedora, Ubuntu mit GNOME und KDE Plasma 6 laufen heute standardmäßig unter Wayland. Dort geht
einiges nicht, was SEITON unter X11 benutzt.

| Was | Wo | Unter Wayland |
|---|---|---|
| SunTree zieht den Mauszeiger | `QCursor.setPos` (SunTree, auch `apps/Scope/Scope.py`) | verboten: Programme dürfen den Zeiger nicht versetzen |
| Globales Tastenkürzel Strg+Alt+Space | `pynput` | geht nicht; nur über den Desktop selbst oder das XDG-Portal „GlobalShortcuts“ |
| Fenster finden und platzieren | `wmctrl`, `xdotool` (Obsidian-Einbettung in PostFix, Tutorial) | nur unter X11 |

Das ist kein Portieren mehr, sondern eine Designfrage, vor allem bei SunTree: Die weiche Krone
(examples/SunTree/Designdocument Krone.md) muss ohne gezogenen Zeiger auskommen. Je nach Lösung rechne ich
ein bis zwei Wochen.

Übergang: „Unter Wayland bitte die X11-Sitzung wählen“. Das bieten die meisten Desktops beim
Anmelden noch an.

## 4. Verteilen

- **Flatpak und Snap passen schlecht.** SEITON braucht FUSE, ändert Desktop-Einstellungen und
  schaut ins ganze Home-Verzeichnis, also genau das, was eine Sandbox verhindern soll.
- **Zuerst:** ein Installer für alle Distributionen (Paketweiche plus eigenes venv, siehe 1).
- **Später:** echte Pakete über den **openSUSE Build Service** (OBS). Er baut aus einer
  Beschreibung `.deb`, `.rpm` und Arch-Pakete für viele Distributionen.

## 5. Aufwand im Überblick

| Ziel | Aufwand |
|---|---|
| Läuft auf openSUSE, Fedora, Arch, Manjaro unter X11 mit Cinnamon, GNOME oder KDE | 2–3 Tage |
| dazu XFCE und MATE in Desk | + 2 Tage |
| dazu Wayland vollwertig | 1–2 Wochen, mit Designentscheidung bei SunTree |
| dazu Pakete über OBS | + 2–3 Tage |

## 6. Vorschlag für den ersten Schritt

Der Installer für alle Distributionen mit eigenem venv. Er räumt das PEP-668-Problem ab, das mit
Mint 22 auch auf den eigenen Rechnern kommt, und legt die Qt-Version für SEITON fest. Danach die
fehlenden Desk-Backends, zuletzt Wayland.

## Offen

- Wie SunTree unter Wayland ohne gezogenen Zeiger arbeitet.
- Welche Qt-Version SEITON festlegt, und wie ein Update davon läuft.
- Ob libfuse 2 auf Dauer bleibt, oder ob wir auf libfuse 3 umsteigen (`pyfuse3` statt `fusepy`).
