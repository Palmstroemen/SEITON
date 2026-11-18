# Demo für Firmen

Entwurf vom 18. November 2026, noch nicht durchgespielt. Für kleine und mittlere Betriebe:
Inhaber, Büroleitung, die IT-Verantwortlichen, auch Steuerberater als Multiplikatoren. Etwa
dreieinhalb Minuten. Die Szenen K1 bis K4 stehen in „Demo – Kern“; hier steht, was diese Fassung
anders macht. Was beim Durchspielen zu prüfen ist, steht in [eckigen Klammern].

## Worum es geht

**Der eine Satz:** Jeder Kunde, jeder Auftrag ist gleich abgelegt, und jede Abteilung sieht über
alle Kunden genau ihren Teil.

**Der Aufhänger:** Ein neuer Kunde, ein neuer Mitarbeiter. Wo legt der Neue ab? Wie findet er
sich in den alten Aufträgen zurecht? Und was darf er sehen?

**Für wen:** Betriebe von drei bis dreihundert Leuten. Sie haben keine eigene IT-Abteilung oder
eine kleine. Sie fragen: Was kostet uns das an Umstellung, und was gewinnen wir im Alltag?

**Eigene Wörter:** „Kunde“ und „Auftrag“ für Projekte; „Abteilung“ für einen Standardordner quer
durch alle Kunden. Der Gedanke dahinter („Wie aus einem Projekt eine Firma wächst“): **Die
Abteilung ist die Brille, die jemand dauerhaft trägt.**

## Vorbereitung

Wie im Kern, dazu:

- **Demo-Daten:** ein Ordner `Kunden` mit drei, vier Kundenprojekten (`Bäckerei Sonne`,
  `Autohaus Berger`, `Hotel Alpenblick`), jeweils mit ein paar Angeboten, Rechnungen und
  Verträgen; dazu ein neuer Kunde als gewöhnlicher Ordner mit einer Anfrage und einem
  unterschriebenen Angebot. [Datensatz anlegen.]
- **Vorlagen:** `Standard` und darüber `Firma` (sie bringt `7_Arbeit` mit `71_Verkauf` bis
  `74_Entwicklung` und `8_Produkte`). [Prüfen, ob die beiden Vorlagen zusammen das Bild ergeben,
  das hier beschrieben ist, oder ob eine Vorlage `Kunde` passender wäre.]
- **Für F2:** eine Nextcloud mit SEITON wie in der Behörden-Fassung, mit einem Konto für die
  Steuerberaterin (Rolle `Steuerberatung`: `4_Finanz` lesen).

## Ablauf

| Zeit | Szene | Daten und Sätze dieser Fassung |
|---|---|---|
| 0:00–0:20 | Das Durcheinander | der Ordner `Kunden` in Nemo, jeder Kunde anders aufgebaut: „Jeder hat seine Ordnung. Der Neue versteht keine davon.“ |
| 0:20–0:40 | K1 | der neue Kunde wird ein Projekt: „Jeder Kunde gleich gebaut, ohne dass jemand Ordner anlegt.“ |
| 0:40–1:05 | K2 | das unterschriebene Angebot auf `71_Verkauf`, die Anfrage auf `3_Kommunikation`: „Wo der Neue ablegt, ist keine Frage mehr.“ |
| 1:05–1:40 | K3 | die Brille `4_Finanz` über alle Kunden: „Das ist die Buchhaltung. Sie ist keine Ordnerstruktur, sie ist eine Brille: alle Rechnungen aller Kunden, und sonst nichts.“ |
| 1:40–2:05 | K4 | eine Rechnung aus LibreOffice über „Perspektiven“ in den Kunden ohne `4_Finanz` |
| 2:05–2:45 | F1 | der neue Mitarbeiter |
| 2:45–3:20 | F2 | die Steuerberaterin |
| 3:20–3:30 | Schluss | |

### F1. Der neue Mitarbeiter

- **Bild:** Scope, links das Zugriffs-Panel; `.seiton/ACLs.md` im Editor.
- **Handgriff:** in Scope unter Zugriff **+ Person**: der neue Verkäufer, Gruppe `Verkauf`. [Prüfen,
  wie das Hinzufügen nach dem Umbau aussieht.]
- **Was passiert:** In `ACLs.md` ist genau eine Zeile dazugekommen. Mit der Brille `7_Arbeit`
  sieht er über alle Kunden den Verkauf, die Finanzen nicht.
- **Text:** „Ein neuer Mitarbeiter ist eine Zeile. Er findet sich in jedem Kunden sofort
  zurecht, weil jeder Kunde gleich gebaut ist, und er sieht nur, was er braucht.“

### F2. Die Steuerberaterin

- **Bild:** der Browser, als Steuerberaterin in der Nextcloud angemeldet.
- **Was passiert:** Sie sieht alle Kunden, darin nur `4_Finanz`. In der Ansicht „Perspectives“
  liegen die Finanzen aller Kunden nebeneinander.
- **Text:** „Kein Ordner, den jemand für sie zusammenkopiert, kein Mail-Anhang. Sie schaut mit der
  Brille der Buchhaltung, auf dem Server, und sieht nichts anderes.“

### Schluss

- **Text:** „Jeder Kunde gleich gebaut. Jede Abteilung eine Brille. Und alles bleibt in
  gewöhnlichen Ordnern, auf eurem Rechner oder eurer Nextcloud.“

## Ehrlich bleiben

- **Umstellung:** Bestehende Kundenordner werden nicht umgebaut. Man macht sie zu Projekten; was
  zu den Standardordnern passt, wandert hinein, wenn man es anfasst. [Prüfen, was „Sortieren
  nach Datum“ und `Sort.md` hier zeigen können, ohne zu viel zu versprechen.]
- **Rechte:** wie in der Behörden-Fassung. Durchgesetzt werden sie in der Nextcloud vom Server,
  am Desktop von SEITONs eigenen Werkzeugen, am Dateisystem vorbei noch nicht.
- **Stand:** ein Prototyp.

## Was diese Fassung weglässt

Zeiterfassung (obwohl sie für Firmen zählt: für die zweite Begegnung, wenn die Lücke mit der
ersten Zeitdatei in der Cloud geschlossen ist), Tags, Filter, Desk, SunTree.
