# ToDo für SunTree

SunTree ist nur zum Ablegen: er zeigt Ordner, keine Dateien, und hat keine Suche (entschieden 2026-10-25).
Die weiche Krone: siehe "Designdocument Krone.md" und die Skizze prototype/Krone.html.
Stand: 2026-11-18, abgeglichen mit dem Code und der Prüfung vom 18.11. (ST1 bis ST7).

[ ] Hoover Automatik hinzufügen (nicht geprüft, was genau gemeint war)
[x] Manifestierte Embryos weiterhin nur im TemplatesBrowser anzeigen. Geborene Standardordner stehen nur links, die rechte Hälfte zeigt sie nicht (listFoldersAt, test_the_right_half_shows_no_settings_folders).
[ ] +Folder (new Folder) hinzufügen und halb transparent gestalten. Im Backend gibt es createFolder, aber keinen Knopf und keinen Test.
[ ] +Notiz (new Notiz) hinzufügen und halb transparent gestalten. Im Backend gibt es createNote, aber keinen Knopf und keinen Test.
[x] Umbau auf Kontextmenü (transparent, disappear): "One action, then gone" und "No background" im Designdocument Krone.
[ ] Icons hinzufügen
[x] Clipboard oben im Stamm (Ablegen darauf). Offen: SunTree nimmt einen anderen Clipboard-Ordner als Scope (Prüfung ST4).
[ ] Esc bricht SunTree nicht ab, er lässt nur die Krone los (Anwendung 7, Prüfung ST5).
[ ] Anwendung 5: aus dem Clipboard in einen Ordner der Krone ziehen.
[ ] Anwendung 6: einen Ordner in Scope öffnen (Mittelklick oder Taste).
[ ] Misslungenes Ablegen und misslungenes Rückgängig melden (Prüfung ST6).
[ ] Über ./install.sh gestartet steht SunTree im Home-Ordner, nicht an der Projekte-Wurzel (Prüfung ST3).
