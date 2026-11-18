Im /.seiton/-Ordner (bis November 2026 /.MyOS/) aber auch ausserhalb in beliebigen Foldern können Config.md-Files liegen, die vom System verwendet werden, um SEITON-Funktionalitäten bereitzustellen.
Beispiele: Templates.md, ACLs.md, Tags.md, Desk.md, usw.

Diese Config.md werden in einer gewissen Weise von SEITON interpretiert:

1. **Überschriften 1** werden wie einzelne Files interpretiert. Das ermöglicht uns 2, mehr oder alle Config-Files in nur einem einzigen File zusammenzufassen.
   
   Also ein File Templates.md (und weitere wie ACLs.md, Tags.md) hätte den gleichen Effekt wie eine Config.md, die so aufgebaut ist: 
# Templates
* Standard
* Website

# …
Überschriften der Ebene # 1 können also im Weiteren als ebensolche oder als einzelne MD-Files verstanden werden. 

   Stand heute (nachgeprüft 2026-11-18): Gebaut ist das nur für Abschnitte, die `ProjectConfig.resolve_effective_section` (core/project.py) liest, heute `Templates`: erst `.seiton/Templates.md`, dann `.seiton/Config.md`. `ACLs.md`, `Tags.md` und `Desk.md` werden nur als eigene Dateien gelesen, ein Abschnitt `# Tags` in einer Config.md wirkt nicht.

   `Tags.md` hat ein eigenes Format (siehe "Designdocument Tags.md", 3): die Überschrift `# Tags`, dann je Zeile ein Tag mit `#` davor, ohne Leerzeichen dazwischen:
# Tags
#wichtig
#in Arbeit
  


2. Einzelne Worte oder Listen von Keywords direkt nach Filebeginn oder nach einer BELIEBIGEN Überschrift werden als Properties oder Listen interpretiert. Eine Leerzeile, ein beliebiger Text bricht diese Interpretation.
   Ausnahme: In `ACLs.md` und `Desk.md` brechen Leerzeilen, Notizen und `<!-- Kommentare -->` einen Abschnitt nicht ab – sonst würden Regeln bzw. Einstellungen stillschweigend wegfallen (siehe "Designdocument ACLs.md", 2.3, und "Designdocument Desk.md", 5). In `Desk.md` dürfen Werte außerdem Leerzeichen enthalten (`PanelTheme: Linux Mint`), und die Taskleiste steht als Liste unter `## Taskbar`.
   
# Templates
Standard
wird als {Templates: Standard} interpretiert.

# Templates
* Standard
* Website
wird als {Templates: [Standard, Website]}

# Templates

* Standard
* Website
wird als NaN interpretiert.

Es ist noch nicht klar festgelegt, ob einzelne Worte (Properties) nicht auch immer als Listen mit nur einem Eintrag interpretiert werden sollen. Könnte einfacher sein. Also:

# Templates
Standard
wird als {Templates: [Standard]} interpretiert.


3. Auch Zeilen mit Keword: Liste, Liste2, Liste3 werden als Properties oder Listen interpretiert.

# ACLs
* Admin: Alfred
* Member: Bertha, Christian, ... 
wird als {ACLs:[{Admin:[Alfred], Member: [Bertha, Christian, ...]}]} interpretiert.

Der Interpreter oder Parser kann also ein solches Objekt bauen und zurückgeben: ACLs.Admin

Alles sehr ähnlich zu YAML aber ohne Einrückungen und über Überschriften strukturiert.


4. Auch Zwischenüberschriften sind erlaubt.
# Templates
* Standard
* Website

#### inherit
fix

könnte über Templates.inherit abgefragt werden.
