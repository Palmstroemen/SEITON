# Demo für Behörden

Entwurf vom 18. November 2026, noch nicht durchgespielt. Für Menschen, die Arbeitsplätze auf
Linux und Nextcloud umstellen: IT-Leitungen, Digitalministerien, EU OS, openDesk. Etwa vier
Minuten. Die Szenen K1 bis K4 stehen in „Demo – Kern“; hier steht, was diese Fassung anders macht.
Was beim Durchspielen zu prüfen ist, steht in [eckigen Klammern].

## Worum es geht

**Der eine Satz:** Die Ordnung auf dem neuen Arbeitsplatz: Projekte, Rechte und die Cloud
dahinter, in Dateien, die jeder lesen kann.

**Der Aufhänger:** Ihr tauscht Windows gegen Linux, Office gegen LibreOffice, SharePoint gegen
Nextcloud. Die Ablage zieht mit um, und mit ihr das Chaos.

**Für wen:** Leute, die Migrationen planen und Rechte verwalten. Sie kennen NTFS-Rechte, Teams
und SharePoint. Sie fragen: Hält das bei 30.000 Plätzen, ist es offen, und was bleibt übrig,
wenn wir es wieder wegnehmen?

**Eigene Wörter:** „Abteilung“ für einen Standardordner quer durch alle Projekte (`4_Finanz` ist
die Finanzabteilung); „Rechte“ statt „ACLs“, außer beim Dateinamen `ACLs.md`.

## Vorbereitung

Wie im Kern, dazu:

- **Demo-Daten:** zwei, drei Referate oder Vorhaben als Projekte, etwa `Förderprogramm Wohnen`,
  `Schulbau Nord`, dazu ein gewachsener Ordner mit gemischten Akten. [Datensatz anlegen.]
- **Eine Nextcloud mit SEITON** (siehe „SEITON auf Nextcloud – Anleitung für den Admin“). Das
  Demo-Projekt liegt in einem Team-Ordner und wird mit dem Desktop-Client synchronisiert.
- **In `ACLs.md`** eine Sachbearbeiterin der Buchhaltung mit Konto, etwa Anna Huber mit der
  Rolle `Buchhaltung` auf `4_Finanz`. [Scope zeigt dann links das Zugriffs-Panel; die Szenen des
  Kerns damit durchspielen.]
- **Ein zweites Browserfenster**, privat, als Anna angemeldet.

## Ablauf

| Zeit | Szene | Daten und Sätze dieser Fassung |
|---|---|---|
| 0:00–0:20 | Das Durcheinander | eine alte Netzfreigabe in Nemo: „So sieht die Ablage nach jeder Migration aus. Neues System, alte Ordner.“ |
| 0:20–0:40 | K1 | `Schulbau Nord` wird ein Projekt: „Dieselben Standardordner wie in jedem anderen Projekt, und doch keine leeren Hüllen im Baum.“ |
| 0:40–1:05 | K2 | ein Bescheid auf `5_Recht`: „Die Pfade sind maschinenlesbar. Suche, Skripte, Backup und Rechte können sich daran festhalten.“ |
| 1:05–1:40 | K3 | die Brille `4_Finanz`: „Die Sicht der Finanzabteilung über alle Vorhaben.“ |
| 1:40–2:10 | K4 | ein Dokument aus LibreOffice: „Ihr müsst keine Fachanwendung umbauen.“ |
| 2:10–2:50 | B1 | Rechte in einer Zeile |
| 2:50–3:40 | B2 | dieselben Rechte in der Nextcloud |
| 3:40–4:00 | B3 | was übrig bleibt |

### B1. Rechte in einer Zeile

- **Bild:** Scope, links das Zugriffs-Panel; dann `.seiton/ACLs.md` im Editor.
- **Handgriff:** die Zeilen zeigen:

      ## Buchhaltung
      - /4_Finanz/: read, write

  dazu unter `# Users`: `Anna Huber: Buchhaltung`.
- **Text:** „So stehen die Rechte da. Eine Zeile sagt: Die Buchhaltung bearbeitet in jedem
  Projekt die Finanzen, sonst nichts. Das gilt in jedem Projekt, in jedem Unterprojekt und über
  die Vorlage in jedem künftigen. In Teams müsstet ihr dafür in jedem Team den Finanzordner von
  Hand abkoppeln. Lesen kann diese Datei jeder, auch ohne Admin-Konsole.“

### B2. Dieselben Rechte in der Nextcloud

- **Bild:** links Scope, rechts der Browser, als Anna angemeldet, im Team-Ordner.
- **Was passiert:** Anna sieht in den Projekten nur `4_Finanz`. Den Rest sieht sie nicht, nicht
  einmal als gesperrte Ordner.
- **Handgriff:** in `ACLs.md` eine Zeile dazu, etwa Leserecht der Buchhaltung auf `5_Recht`,
  speichern. Der Desktop-Client lädt sie hoch.
- **Was passiert:** Nach wenigen Sekunden sieht Anna `5_Recht`. [Zeit messen: Sync-Client plus
  Kerndienst.]
- **Handgriff:** im Browser links die Ansicht „Perspectives“: Anna sieht `4_Finanz` über alle
  Projekte, wie die Brille am Desktop.
- **Text:** „Dieselbe Datei, und jetzt setzt Nextcloud die Rechte selbst durch, auf dem Server.
  Keine zweite Rechteverwaltung, kein Abgleich von Hand. Das Projekt bringt seine Rechte mit,
  wohin es auch geht.“

### B3. Was übrig bleibt

- **Bild:** Nemo zeigt ein Projekt mit eingeblendeten versteckten Ordnern; `.seiton` mit ein
  paar Markdown-Dateien.
- **Text:** „Das ist alles. Gewöhnliche Ordner und ein paar Textdateien. Nimmt man SEITON wieder
  weg, bleibt ein ordentlicher Verzeichnisbaum. Der Code ist offen, MIT-Lizenz.“
- **Schluss:** „SEITON: die Ordnung auf eurem neuen Arbeitsplatz. Projekte, Rechte und eine
  europäische Cloud dahinter.“

## Ehrlich bleiben

Die Zuschauer fragen nach. Was gesagt wird, muss stimmen:

- **Wo die Rechte durchgesetzt werden:** in der Nextcloud vom Server. Am Desktop von SEITONs
  eigenen Werkzeugen (Scope, CLI, Laufwerk); am Dateisystem vorbei, etwa in einer Shell, noch
  nicht. Das Modell lässt sich auf POSIX-, NTFS- und APFS-Rechte abbilden; diese Übersetzung ist
  geplant, nicht gebaut.
- **Wer bin ich:** Am Desktop gibt es noch keine Anmeldung; in der Nextcloud zählt deren Konto.
- **Stand:** ein Prototyp, rund 2000 automatisierte Tests, Nextcloud 32 bis 35.
- **Bekannte Lücke:** Die erste Zeitdatei einer Person ohne eigene Rolle in `0_Admin` lässt sich
  in der Cloud noch nicht von ihr selbst anlegen. Kommt in der Demo nicht vor.

## Was diese Fassung weglässt

Zeiterfassung, Tags, Filter, Desk, SunTree: für die zweite Begegnung. Andere Clouds als
Nextcloud: gebaut wird über Adapter, gezeigt wird nur Nextcloud.

## Für die Videofassung

Wie im Kern, dazu in B2 ein Zoom auf Annas Ordnerliste vor und nach der Änderung und ein
Zeitstempel, wie lange es gedauert hat.
