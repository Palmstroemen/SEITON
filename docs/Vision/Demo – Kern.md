# Demo – Kern

Entwurf vom 18. November 2026, noch nicht durchgespielt. Der Teil, der in jeder Fassung gleich
ist. Jede Zielgruppe hat eine kurze eigene Datei mit Aufhänger, eigenen Beispieldaten, einer
eigenen Szene und dem Schluss; die Szenen hier stehen dazwischen. Entstanden aus „Demo in drei
Minuten“ (3.11.2026, damals ganz durchgespielt). Was beim Durchspielen zu prüfen ist, steht in
[eckigen Klammern].

## Die Fassungen

| Datei | Für wen | Aufhänger | Eigene Szene | Stand |
|---|---|---|---|---|
| Demo in drei Minuten | alle, privat | die Steuererklärung | alles vom Urlaub beim Urlaub | durchgespielt 3.11., wird auf den Kern umgestellt |
| Demo für Behörden | Verwaltungen, EU OS, openDesk | die Migration zieht das Chaos mit | Rechte in einer Zeile, Nextcloud setzt sie durch | Entwurf |
| Demo für Firmen | kleine und mittlere Betriebe | ein neuer Kunde, ein neuer Mitarbeiter | die Abteilung ist die Brille, die jemand dauerhaft trägt | Entwurf |
| Demo für Schulen | Schulen, Bildungsträger | jedes Jahr neue Klassen | jede Klasse ein Projekt aus derselben Vorlage | geplant (eine Schul-Vorlage fehlt noch) |
| Demo für Militär | Bundesheer und andere Streitkräfte | die Übergabe an die nächste Besetzung | Ordnung und Rechte ohne Cloud, auch abgeschottet und auf dem Stick | geplant |
| Demo für Vereine | Vereine, Ehrenamt | der Kassier wechselt | Projekte reisen: die Übergabe | Idee |

## Für alle Fassungen

**Bildschirm:** links Scope, rechts Nemo. Rechts ist „die Vergangenheit“, links „die Zukunft“;
dieses Bild trägt jede Demo. [Die Rolle der Headline klären: Sie ist inzwischen das Hauptprogramm.]

**Die Wörter:** blasse Ordner (nicht „Embryos“), Standardordner, Brille. „Perspektive“ nur beim
Laufwerk, weil es so heißt. Die Zielgruppen dürfen eigene Wörter dazunehmen (Behörden:
„Abteilung“).

**Demo-Daten:** je Fassung ein eigener Ordner, vor jeder Vorführung frisch gebaut, mit einem
kurzen Pfad (Scope zeigt die Pfadleiste ab `/`). [Heute baut `scripts/make_demo_data.py` nur die
Privat-Geschichte, mit `04_Finanz` und `08_Dokumentation`; die Standard-Vorlage heißt inzwischen
`4_Finanz` und `9_Dokumentation`. Das Skript bekommt einen Datensatz je Fassung.]

**Zustand vor dem Start:** Scope läuft im Ordner `Projekte` der Demo, ohne Brille. Das Laufwerk
„Perspektiven“ liegt daneben; Nemo und der Speichern-Dialog von LibreOffice führen es unter
„Geräte“. Nur dieses eine Scope läuft (sonst gibt es zwei Laufwerke „Perspektiven“).

## Die Szenen des Kerns

Jede Fassung erzählt sie mit ihren eigenen Daten und Sätzen; hier steht, was gezeigt wird.

### K1. Ordner, die warten

- **Handgriff:** einen gewöhnlichen Ordner auswählen, auf **P** klicken („zum Projekt machen“),
  hinein.
- **Was passiert:** Der Ordner bekommt sein P, drinnen stehen blasse Standardordner. Rechts in
  Nemo ändert sich nichts.
- **Kernsatz:** „Die gibt es noch nicht. Sie warten nur.“

### K2. Ein Ordner wird geboren

- **Handgriff:** eine Datei auf einen blassen Standardordner ziehen.
- **Was passiert:** Links wird er kräftig, rechts in Nemo taucht er auf, mit der Datei darin.
- **Kernsatz:** „Er ist da, wenn ich ihn brauche, und er heißt in jedem Projekt gleich.“

### K3. Die Brille

- **Handgriff:** die Brille eines Standardordners aufsetzen (etwa `4_Finanz`) und durch die
  Projekte gehen; dann in Nemo `Perspektiven/4_Finanz/Projekte`. [Die Handgriffe nach dem Umbau
  von Scope und der Headline neu festlegen.]
- **Was passiert:** Über alle Projekte nur dieser eine Standardordner, in Scope wie im Laufwerk.
- **Kernsatz:** „Kein zweiter Ordnerbaum, keine Kopie. Derselbe Bestand, umgedreht.“
- **Für das Video (Ideen, 19.11.):** Die Brille ist eine kurze Szene, kein Thema für sich. Jede
  Fassung erzählt sie mit ihrem eigenen Beispiel; dazwischen dürfen ein, zwei Bilder kurz als
  Collage-Schnipsel stehen, damit es wirklich jeder versteht.
  - Beispiele je Fassung: Behörden die Finanzabteilung über alle Vorhaben; Schulen die
    Mathe-Lehrerin über alle Klassen; Militär S4 (Logistik) über alle Einheiten, denn die
    Stabsgliederung S1 bis S6 ist schon eine Reihe von Standardordnern; Firmen die Buchhaltung
    (die Werkstatt-Rechnung); Vereine der Kassier über alle Veranstaltungen.
  - Bilder: die Tabelle (Projekte Zeilen, Standardordner Spalten, die Brille liest eine Spalte);
    das Regal von zwei Seiten (Werkstatt und Finanzbüro, „Brillen und die runde Halle“); die
    Schubladen (in jedem Schrank dieselbe Schublade, alle gehen zugleich auf); die Folien
    („Transparentpapier“); der Schlüssel (sperrt in jedem Projekt dieselbe Tür, passt zu den
    Rechten).

### K4. Jedes Programm kann es

- **Handgriff:** in LibreOffice „Speichern unter“, links „Perspektiven“, dann Standardordner,
  `Projekte`, ein Projekt ohne diesen Ordner, speichern.
- **Was passiert:** Im Projekt ist der Ordner neu geboren, die Datei liegt darin.
- **Kernsatz:** „LibreOffice weiß nichts von SEITON.“

## Was nie vorkommt

- **Was nicht gebaut ist:** Suche über alle Projekte mit der Brille, Mailprogramme, die selbst
  ablegen, die lokale KI. Höchstens als Ausblick nach der Demo, als solcher benannt.
- **Das Energie-Argument:** erst mit Messung.

## Was schiefgehen kann

- **Ein Doppelklick wird ein Einfachklick:** vorher üben, sonst wirkt die Brille unzuverlässig.
- **Das Laufwerk fehlt in Nemo:** Scope wurde nach Nemo neu gestartet; Nemo einmal neu laden.
- **Nach der Demo hängt das Laufwerk noch:** Solange LibreOffice die Datei offen hat, bleibt es
  eingehängt; LibreOffice zuerst schließen.

## Für die Videofassung

- **Untertitel:** Der Text steht im Bild, die Stimme ist optional.
- **Zoom:** bei der Geburt (K2) und beim Rahmen der Brille in der Pfadleiste (K3).
- **Schnitte:** zwischen den Szenen schneiden statt warten.
