# Wie aus einem Projekt eine Firma wächst

Stand: 2026-11-15, Gedanken, noch nicht entschieden.

Am Anfang ist eine Firma ein Projekt wie jedes andere: ein Ordner mit den Standardordnern `00`
bis `08`. Wächst sie, werden aus Ordnern Abteilungen. Die Frage ist, aus welchen und wie, ohne dass
die Ordnung, die bis dahin gilt, zerbricht.

## Die Regel

**Standardordner sagen, *was* drinliegt. Wer daran arbeitet, eine Abteilung, wird ein Projekt.**

Die Namen der Standardordner nennen darum die Sache, nicht eine Abteilung: `033_Kunden`, nicht
`033_Sales`. `033_Kunden` passt im Verkauf wie im AfterSales, `033_Sales` wäre im AfterSales
unsinnig.

## Zwei Arten von Abteilungen

### Querschnittsabteilungen wachsen aus einem Standardordner

Finanz, Recht, HR, Führung und Archiv kümmern sich um *eine Art von Unterlagen*, und zwar in allen
Projekten. Die Finanzabteilung tut im Grunde nichts anderes, als die Brille `04` über die ganze Firma
zu setzen und die Finanzordner aller Projekte zu betreuen. Die Abteilung ist die Brille, die jemand
dauerhaft trägt.

| Standardordner | wird einmal |
|---|---|
| `00_Admin` | die Firmenführung |
| `02_Team` | HR |
| `03_Kommunikation` | die Unternehmenskommunikation (Medien, Öffentlichkeit, Webseite, Investor Relations) |
| `04_Finanz` | die Finanzabteilung |
| `05_Rechtliches` | die Rechtsabteilung |
| `06_Ressourcen` | IT, Gebäude, Fuhrpark |
| Archiv | das Archiv |

Investor Relations passt hierher: ein Gegenüber, eine Aufgabe, `035_Investoren` und eine Brille
darüber. Was sie aus `04` sehen darf, gibt ihr die Finanzabteilung über Rechte.

### Kernabteilungen wachsen aus einem Ablauf

Verkauf, Einkauf, Herstellung und Entwicklung folgen einem Ablauf und berühren dabei fast jeden
Standardordner. Der Verkauf zum Beispiel folgt dem Kunden:

```
Anfrage → Angebot → Vertrag → Auftrag → Lieferung → Rechnung → AfterSales
 033       04        05        07        07         04         033
```

Ließe man den Verkauf aus `033_Kunden` wachsen, säße er auf einem Ausschnitt davon und stritte mit
den Querschnittsabteilungen (wem gehören die Angebote in `04`?). Der Einkauf spannt sich ebenso über
Lieferanten, Bestellungen, Verträge und Ressourcen.

Die Kernabteilungen wachsen darum aus **`07_Arbeit`**, der eigentlichen Arbeit, dem einzigen Ordner,
der von Projekt zu Projekt verschieden ist. Was eine Firma ausmacht, liegt dort. Wird eine Tätigkeit
groß, wird sie ein Unterprojekt der Firma und bringt ihre eigenen `00` bis `08` mit:

```
Firma/Verkauf/03_Kommunikation/033_Kunden
Firma/AfterSales/03_Kommunikation/033_Kunden
Firma/Einkauf/03_Kommunikation/034_Partner
```

Die Brille `033` findet die Kundenkommunikation der ganzen Firma über alle Abteilungen hinweg.
„Wo ist alles zu den Kunden?“ hat eine Antwort, wie die Firma auch gerade aufgestellt ist.
Organigramme ändern sich, die Nummern nicht: Bei einer Umorganisation verschiebt man Projekte, die
Ablage in ihnen bleibt.

**Kurz:** Die Querschnittsabteilungen sind Brillen über die Standardordner. Die Kernabteilungen
wachsen aus `07` und tragen die Standardordner in sich.

## Ein Thema wird groß

Manchmal wird nicht eine Tätigkeit groß, sondern ein einzelnes Thema. Dann wird der Ordner an Ort und
Stelle ein Projekt, mit eigenen Finanzen, Verträgen und eigenem Team:

- die Webseite: `037_Öffentlichkeit/Webseite`
- ein Großkunde, ein Key Account: `033_Kunden/Müller GmbH`

Die Nummer im Pfad bleibt stehen, die Adresse ändert sich nicht.

## Flach statt tief

Weil jede Abteilung die Standardordner noch einmal in sich trägt, müssen diese flach sein, sonst
werden die Pfade endlos. Beispiel `03_Kommunikation`: Heute teilt es sich in `intern` und `extern`,
und `extern` mischt zwei Dinge, *an wen* man sich wendet (Kunden, Investoren, Medien) und *auf
welchem Weg* (Webseite, Soziale Medien, Mails). Flach, nur nach dem „an wen“:

```
03_Kommunikation
├── (030 frei: für die ganze Kommunikation, etwa ein Eingang)
├── 031_Intern          Rundschreiben, Protokolle, Vereinbarungen
├── 032_Berichte        nach oben ans Mutterprojekt, und was von dort kommt
├── 033_Kunden
├── 034_Partner
├── 035_Investoren
├── 036_Medien
├── 037_Öffentlichkeit  Webseite, Soziale Medien, Werbung
└── (038, 039 frei)
```

- Intern und extern sind keine Ebene mehr, sondern ein Nummernbereich: `031`/`032` intern, ab `033`
  extern.
- Der Weg ist keine Ebene: Eine Mail an einen Kunden liegt bei `033_Kunden`; alle Mails zeigt ein Filter.
- `032_Berichte` ist die senkrechte Kommunikation (siehe „Ideas from FreeDMS“ im Designdokument).
  Sie wird wichtig, sobald es Abteilungen gibt: Die Abteilung berichtet dort an die Firma.

## Nummern

Gesprochen heißt es „Firma 033“ oder „Verkauf 033“. Wer sich an die Nummern gewöhnt, sagt „leg das
unter 041 ab“, wie ein Buchhalter in Kontonummern denkt. Näher als an Johnny.Decimal ist SEITON damit
an einem Kontenrahmen oder Aktenplan: Die Nummer bedeutet überall dasselbe, in jedem Projekt und in
jeder Sprache.

- Zwei nummerierte Ebenen (`04`, `041`), darunter ordnet jeder frei.
- `x0` bleibt frei für das Ganze des Ordners, die Inhalte beginnen bei `x1` (wie die „standard zeros“
  bei Johnny.Decimal).
- Nummern freihalten: Umnummerieren bricht das Versprechen, dass die Namen sich nie ändern.
- Ordner mit Nummer kommen aus der Vorlage, Ordner ohne Nummer hat man selbst angelegt.

## Offen

- Gehören die Lieferanten zu `02_Team` oder zu den Gegenübern in `03_Kommunikation`?
- Vorschriften: in `031_Intern` oder in `01_Info` (was man wissen muss, wenn man neu dazukommt)?
- Rechte über einen Nummernbereich (`03[3-7]*` statt `/extern/`): ob die Regelpfade das tragen, ist
  nicht geprüft.
- Wo liegt das Archiv: in `08_Dokumentation` oder als eigener Standardordner `09_Archiv`?
