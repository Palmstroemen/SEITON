# Wie aus einem Projekt eine Firma wächst

Stand: 2026-11-15, Gedanken, noch nicht entschieden.

Am Anfang ist eine Firma ein Projekt wie jedes andere: ein Ordner mit den Standardordnern. Wächst
sie, werden aus Ordnern Abteilungen. Die Frage ist, aus welchen und wie, ohne dass die Ordnung, die
bis dahin gilt, zerbricht.

## Die Regel

**Standardordner sagen, *was* drinliegt. Wer daran arbeitet, eine Abteilung, wird ein Projekt.**

Die Namen der Standardordner nennen darum die Sache, nicht eine Abteilung und nicht einen Weg:
`35_Kunden`, nicht `35_Sales`. `35_Kunden` passt im Verkauf wie im AfterSales, `35_Sales` wäre im
AfterSales unsinnig.

## Zwei Arten von Abteilungen

### Querschnittsabteilungen wachsen aus einem Standardordner

Finanz, Recht, HR, Führung und Archiv kümmern sich um *eine Art von Unterlagen*, und zwar in allen
Projekten. Die Finanzabteilung tut im Grunde nichts anderes, als die Brille `4` über die ganze Firma
zu setzen und die Finanzordner aller Projekte zu betreuen. Die Abteilung ist die Brille, die jemand
dauerhaft trägt.

| Standardordner | wird einmal |
|---|---|
| `0_Admin` | die Firmenführung |
| `2_Team` | HR |
| `3_Kommunikation` | die Unternehmenskommunikation (Öffentlichkeit, Investor Relations) |
| `4_Finanz` | die Finanzabteilung |
| `5_Recht` | die Rechtsabteilung |
| `6_Ressourcen` | IT, Gebäude, Fuhrpark |
| `9_Dokumentation` | das Archiv |

Investor Relations passt hierher: ein Gegenüber, eine Aufgabe, `36_Investoren` und eine Brille
darüber. Was sie aus `4` sehen darf, gibt ihr die Finanzabteilung über Rechte.

### Kernabteilungen wachsen aus einem Ablauf

Verkauf, Einkauf, Herstellung und Entwicklung folgen einem Ablauf und berühren dabei fast jeden
Standardordner. Der Verkauf zum Beispiel folgt dem Kunden:

```
Anfrage → Angebot → Vertrag → Auftrag → Lieferung → Rechnung → AfterSales
 35        42        52        43/7      7          44         35
```

Ließe man den Verkauf aus `35_Kunden` wachsen, säße er auf einem Ausschnitt davon und stritte mit
den Querschnittsabteilungen (wem gehören die Angebote in `4`?). Der Einkauf spannt sich ebenso über
Lieferanten, Bestellungen, Verträge und Ressourcen.

Die Kernabteilungen wachsen darum aus **`7`**, der eigentlichen Arbeit, die jede Vorlage selbst
füllt. Was eine Firma ausmacht, liegt dort. Wird eine Tätigkeit groß, wird sie ein Unterprojekt der
Firma und bringt ihre eigenen Standardordner mit:

```
Firma/Verkauf/3_Kommunikation/35_Kunden
Firma/AfterSales/3_Kommunikation/35_Kunden
Firma/Einkauf/3_Kommunikation/34_Lieferanten
```

Die Brille `35` findet die Kundenkommunikation der ganzen Firma über alle Abteilungen hinweg.
„Wo ist alles zu den Kunden?“ hat eine Antwort, wie die Firma auch gerade aufgestellt ist.
Organigramme ändern sich, die Nummern nicht: Bei einer Umorganisation verschiebt man Projekte, die
Ablage in ihnen bleibt.

**Kurz:** Die Querschnittsabteilungen sind Brillen über die Standardordner. Die Kernabteilungen
wachsen aus `7` und tragen die Standardordner in sich.

## Ein Thema wird groß

Manchmal wird nicht eine Tätigkeit groß, sondern ein einzelnes Thema. Dann wird der Ordner an Ort und
Stelle ein Projekt, mit eigenen Finanzen, Verträgen und eigenem Team:

- die Webseite: `37_Öffentlichkeit/Webseite`
- ein Großkunde, ein Key Account: `35_Kunden/Müller GmbH`

Die Nummer im Pfad bleibt stehen, die Adresse ändert sich nicht.

## Das Nummernsystem

### Regeln

1. **Zehn Standardordner, eine Ziffer:** `0` bis `9`, ohne führende Null. Mehr als zehn wird es nie
   geben, das ist ein Versprechen.
2. **0 bis 6 und 9 sind überall gleich. 7 und 8 füllt jede Vorlage selbst**, eine darf leer bleiben.
   Brillen auf `7` und `8` suchen darum nach dem Namen, nicht nach der Nummer.
3. **Unterordner: die Ziffer des Ordners plus eine Ziffer**, `4_Finanz/44_Rechnungen`. Zwei
   nummerierte Ebenen, gesprochen „vierundvierzig“. Darunter ordnet jeder frei; die Vorlage darf dort
   Vorschläge ohne Nummer machen.
4. **`x0` bleibt frei** für den Ordner als Ganzes (`40` für Finanz, `00` für die Verwaltung der
   Verwaltung), die Inhalte beginnen bei `x1` (wie die „standard zeros“ bei Johnny.Decimal).
5. **Die Reihenfolge folgt der Zeit**: ein Mitarbeiter ist zuerst ein Bewerber, eine Rechnung zuerst
   ein Angebot. Wo es keinen Ablauf gibt, von innen nach außen oder von groß nach klein.
6. **Namen nennen die Sache**, nicht eine Abteilung und nicht einen Weg (Mail, Webseite).
7. **Nummern freihalten**, nach hinten: Umnummerieren bricht das Versprechen, dass die Namen sich nie
   ändern. Ordner mit Nummer kommen aus der Vorlage, Ordner ohne Nummer hat man selbst angelegt.

Gesprochen heißt es „Firma 35“ oder „Verkauf 35“. Wer sich an die Nummern gewöhnt, sagt „leg das
unter 44 ab“, wie ein Buchhalter in Kontonummern denkt. Näher als an Johnny.Decimal ist SEITON damit
an einem Kontenrahmen oder Aktenplan: Die Nummer bedeutet überall dasselbe, in jedem Projekt und in
jeder Sprache.

### Die Ordner

```
0_Admin             → Firmenführung
   01_Ziele
   02_Planung
   03_Entscheidungen    Beschlüsse, Protokolle der Leitung
   04_Organisation      Aufbau, Abläufe, Zuständigkeiten
1_Info
   11_Einstieg          hier anfangen, wenn man neu ist
   12_Grundlagen
   13_Vorschriften      Regeln, die für alle gelten
   14_Recherche         Gesammeltes, noch nicht Entschiedenes
2_Team              → HR
   21_Bewerbungen
   22_Mitarbeiter       ein Ordner pro Person
   23_Externe           Freelancer, Berater
   24_Ehemalige
3_Kommunikation     → Unternehmenskommunikation
   31_Intern            Rundschreiben, Protokolle, Vereinbarungen
   32_Berichte          nach oben ans Mutterprojekt, und was von dort kommt
   33_Partner
   34_Lieferanten
   35_Kunden
   36_Investoren
   37_Öffentlichkeit    Presse, Rundfunk, Webseite, Soziale Medien, Werbung
4_Finanz            → Finanzabteilung
   41_Budget
   42_Angebote          Eingang / Ausgang
   43_Aufträge          Eingang / Ausgang
   44_Rechnungen        Eingang / Ausgang
   45_Zahlungen         Konten, Auszüge, Kredite
   46_Steuern
   47_Abschlüsse
5_Recht             → Rechtsabteilung
   51_Schutzrechte      Patente, Marken: oft das Erste, woran ein Startup denkt
   52_Verträge
   53_Versicherungen
   54_Behörden          Bescheide, Genehmigungen, Anträge
   55_Rechtsfälle       der Streit kommt zuletzt
6_Ressourcen        → IT, Gebäude, Fuhrpark
   61_Immobilien
   62_Fahrzeuge
   63_Maschinen
   64_Computer
   65_Software
   66_Lager
7, 8                → je nach Vorlage, hier wachsen die Kernabteilungen
9_Dokumentation     → Archiv
   91_Berichte
   92_Bilder
   93_Videos
   94_Handbücher
   95_Archiv            abgeschlossene Unterprojekte, gepackt
```

### Die dritte Ebene: wo ein Ablauf zwei Richtungen hat

Angebot, Auftrag und Rechnung gibt es beim Verkaufen und beim Einkaufen. Die Richtung ist keine
eigene Ebene über dem Ablauf, sondern liegt darunter, als Vorschlag ohne Nummer:

```
44_Rechnungen
├── Eingang     was wir bezahlen
└── Ausgang     was andere uns bezahlen
```

Ebenso der Weg einer Veröffentlichung in `37_Öffentlichkeit`: Entwürfe → Freigegeben →
Veröffentlicht.

### 7 und 8 je nach Vorlage

| Vorlage | 7 | 8 |
|---|---|---|
| Standard | 7_Arbeit | leer |
| Person | 7_Gesundheit | 8_Bildung |
| Firma | 7_Arbeit (71_Verkauf, 72_Einkauf, 73_Herstellung, 74_Entwicklung) | 8_Produkte |
| Development | 7_Entwicklung (71_Anforderungen … 75_Auslieferung) | 8_Betrieb |

### Was sich gegenüber heute ändert

- Die führende Null fällt weg, aus `04_Finanz` wird `4_Finanz`.
- Dokumentation und Archiv werden eins und rücken auf die 9, ans Ende. Heute nennen „Die Methode
  auf einer Seite“ und Lektion 09 `08_Dokumentation` „das Archiv“.
- `03_Kommunikation` verliert die Ebene `intern`/`extern`: Sie wird zum Nummernbereich (`31`/`32`
  intern, ab `33` extern), und der Weg (Webseite, Soziale Medien) ist keine Ebene mehr.
- Die Lieferanten wandern von `02_Team` nach `34`: Team ist, wer *im* Projekt arbeitet,
  Kommunikation, mit wem man es *von außen* zu tun hat.
- Die Datenblätter sind kein eigener Ordner mehr; sie liegen bei ihrer Maschine oder ihrem Gerät.
- Die Vorschriften kommen nach `13`: was man als Neuer wissen muss.
- `04_Finanz/Einnahmen` und `Ausgaben` werden zur dritten Ebene `Eingang`/`Ausgang`.
- Die Vorlage „Person“ belegt 7 und 8 heute schon anders; das wird zur Regel.
- Der Umzug betrifft Vorlagen, Ordnerregeln in `ACLs.md`, Lektionen, Texte und Testdaten. Der Code
  hängt nicht am Muster `NN_` (geprüft).

## Offen

- Rechte über einen Nummernbereich (`3[3-7]*` statt `/extern/`): ob die Regelpfade das tragen, ist
  nicht geprüft.
- `0_Admin/01_Ziele` sieht aus wie das alte `01_Info`: Das verwirrt in der Übergangszeit.
