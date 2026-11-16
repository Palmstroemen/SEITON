# Ein Zaun um die Arbeit, nicht um das Programm

*Erster Entwurf, 16. November 2026.*

## Warum heute alles in Sandkästen verschwindet

Auf dem Smartphone ist es längst selbstverständlich: Jede App lebt in ihrem eigenen Sandkasten.
Die Taschenlampe sieht deine Fotos nicht, das Spiel nicht deine Nachrichten. Will eine App mehr,
muss sie fragen. Dieselbe Idee zieht jetzt auf den Schreibtisch. macOS sperrt Programme ein,
Windows ebenso, und unter Linux kommen Programme immer öfter als Flatpak oder Snap, jedes in
seinem eigenen, abgeschlossenen Bereich.

Das hat gute Gründe. Früher durfte jedes Programm alles lesen, was der Benutzer lesen durfte.
Ein einziges bösartiges oder fehlerhaftes Programm, ein unbedachter Klick auf einen
Mailanhang, und die Erpressersoftware verschlüsselt das ganze Home-Verzeichnis: Fotos von
zwanzig Jahren, die Buchhaltung, die Diplomarbeit. Der Sandkasten setzt dem eine Grenze. Ein
Programm sieht nur noch, was es sehen soll. Das ist richtig gedacht, und niemand will zurück
in die Zeit, in der jedes Bildschirmschoner-Programm die Steuererklärung lesen konnte.

## Was dabei verloren geht

Der Sandkasten hat aber einen Konstruktionsfehler: **Er zieht den Zaun um das Programm, nicht um
die Arbeit des Menschen.**

Die Folgen kennt jeder vom Smartphone. Die Fotos gehören der Foto-App, die Notizen der
Notiz-App, die Rechnung steckt im Mailprogramm, das PDF in der Download-Ablage des Browsers.
Gehören sie zum selben Vorhaben, etwa zum Umbau der Küche, gibt es keinen Ort, an dem sie
zusammenliegen. Das Projekt, das im Kopf eine Einheit ist, zerfällt in so viele Silos, wie es
Programme gibt. Und es zerfällt nach der Logik der Hersteller, nicht nach der eigenen.

Daraus folgt eine ganze Reihe von Problemen:

- **Die Daten gehören dem Programm.** Wer die Notiz-App wechselt, nimmt seine Notizen nicht einfach
  mit. Wer ein Programm deinstalliert, verliert oft, was darin lag.
- **Der Überblick geht verloren.** „Wo ist eigentlich die Datei?“ ist eine Frage, die viele gar
  nicht mehr stellen. Eine ganze Generation lernt Computer kennen, ohne je einen Ordner angelegt
  zu haben. Wer nicht weiß, wo seine Daten liegen, kann sie auch nicht sichern, ordnen oder
  mitnehmen. Er ist auf die Cloud des Herstellers angewiesen, die das für ihn erledigt.
- **Zusammenarbeit wird zum Hindernislauf.** Zwischen den Sandkästen gibt es nur schmale
  Durchreichen: das Teilen-Menü, den Öffnen-Dialog, die Zwischenablage. Was in einem Programm
  liegt, muss erst exportiert, kopiert oder hochgeladen werden, damit ein anderes damit
  arbeiten kann.
- **Die Berechtigungen versteht niemand.** „Darf diese App auf Ihre Fotos zugreifen?“ Nach der
  zwanzigsten Frage klickt jeder auf „Erlauben“. Und dann sieht die App eben nicht ein Foto,
  sondern alle. Die Grenze ist grob, und gezogen hat sie der Hersteller, nicht der Mensch.
- **Die Sicherheit bleibt lückenhaft.** Ein Programm, dem man den Ordner „Dokumente“ freigegeben
  hat, kann darin genauso Schaden anrichten wie früher. Der Sandkasten schützt das Programm
  vor dem Rest, aber nicht die Arbeit des Menschen vor dem Programm, dem er sie anvertraut hat.

Kurz: Der Sandkasten macht den Computer sicherer, aber er nimmt dem Menschen die Hoheit über
seine Daten. Er löst ein Sicherheitsproblem und schafft dabei ein Ordnungsproblem.

## Der Zaun gehört dorthin, wo der Mensch ihn zieht

Menschen denken nicht in Programmen. Sie denken in Vorhaben: die Familie, das Auto, die Firma,
der Kunde Huber, der Urlaub 2025, die Küche. Genau dort ziehen sie ihre Grenzen ganz von selbst.
Die Steuerberaterin soll die Finanzen der Firma sehen, nicht die Fotos vom Urlaub. Der Mechaniker
braucht die Rechnungen des Autos, nicht die der Wohnung.

SEITON baut auf dieser natürlichen Grenze auf: **dem Projekt.** Alles, was zu einem Vorhaben
gehört, liegt in einem Projektordner, ganz gleich, mit welchem Programm es entstanden ist. In
jedem Projekt stehen dieselben Ordner an derselben Stelle: die Finanzen in `4_Finanz`, die
Verträge in `5_Recht`, die Fotos in `9_Dokumentation`. Das Projekt ist sichtbar, man kann es
kopieren, sichern, verschlüsseln, auf einen USB-Stick legen oder mit anderen teilen. Es gehört
keinem Programm, es gehört dem Menschen.

Und in SEITON hat jedes Projekt schon heute seine Rechte. Wer darf die Finanzen sehen, wer
die Verträge ändern? Das stellt man in Rollen ein, die jeder versteht: „Buchhaltung darf
`4_Finanz` lesen und schreiben.“ Dafür braucht man keine Informatik-Ausbildung.

## Wie der Sandkasten in SEITON weiterlebt, nur besser

Die Idee des Sandkastens ist richtig: Nicht jedes Programm soll alles sehen. SEITON verwirft sie
nicht. Es zieht den Zaun nur an einer anderen Stelle. So könnte das aussehen (einiges davon gibt
es schon, anderes ist der nächste Schritt):

1. **Das Projekt ist der Sandkasten.** Ein Programm, das man im Projekt „Autowerkstatt“ startet,
   arbeitet in der Autowerkstatt. Die Finanzabteilung der Firma bekommt es nicht zu Gesicht. Die
   Grenze ist kein unsichtbarer Container irgendwo in einem versteckten Verzeichnis. Sie ist der
   Projektordner, den man im Dateimanager vor sich sieht.

2. **Programme bekommen Rollen, wie Menschen.** Was für die Buchhalterin gilt, kann auch für ein
   Programm gelten: Das Steuerprogramm darf `4_Finanz` lesen, in allen Projekten, und sonst
   nichts. Der Bildbearbeiter darf in `9_Dokumentation` schreiben. Statt zwanzig unverständlicher
   Einzelfragen steht da eine Regel, die man einmal festlegt und lesen kann. Und weil die Ordner
   in jedem Projekt gleich heißen, passt die Regel überall.

3. **Der Öffnen-Dialog kennt die Ordnung.** Heute ist der Dialog zum Öffnen und Speichern die
   schmale Durchreiche zwischen den Sandkästen. In SEITON wird er zum Wegweiser: Er bietet das
   aktuelle Projekt an und weiß, dass eine Rechnung nach `4_Finanz` gehört. Was der Mensch dort
   auswählt, darf das Programm öffnen. Die Freigabe ist dieselbe Handlung wie das Ablegen.

4. **Jedes Projekt hat seinen Arbeitsplatz.** In SEITON merkt sich jedes Projekt seine Programme,
   seine Taskleiste und sein Aussehen. In der Autowerkstatt liegen die Werkstattprogramme
   bereit, im Musikstudio die Musikprogramme. Der Schritt zum Sandkasten ist klein: Was im
   Musikstudio läuft, bleibt im Musikstudio.

5. **Die Daten bleiben Dateien.** Was ein Programm erzeugt, landet als gewöhnliche Datei im
   Projekt, nicht in seinem privaten Speicher. Deinstalliert man das Programm, bleibt die Arbeit.
   Wechselt man das Programm, findet das neue alles an derselben Stelle. Eine Sicherung ist eine
   Kopie des Projektordners.

6. **Der Überblick geht quer, ohne die Grenzen aufzuheben.** Mit den Perspektiven von SEITON
   sieht man zum Beispiel alle Rechnungen aller Projekte auf einen Blick, ohne dass dafür etwas
   kopiert oder ein Zaun eingerissen wird. Man sieht nur, was man auch sehen darf.

Für die Durchsetzung muss SEITON nichts neu erfinden. Linux bringt die Werkzeuge mit, aus denen
heute die Sandkästen gebaut werden: Namensräume, Landlock, die Portale von Flatpak. SEITON
gibt ihnen eine Grenze, die ein Mensch versteht, statt einer, die ein Hersteller festlegt.

## Sicher und trotzdem Herr über die eigenen Daten

Der Sandkasten von heute stellt uns vor eine falsche Wahl: Sicherheit oder Ordnung. Entweder
jedes Programm sieht alles, oder die eigenen Daten zerfallen in die Silos der Hersteller.

SEITON hält beides zusammen. Der Zaun bleibt, aber er steht dort, wo der Mensch ihn ohnehin
zieht: um seine Projekte. Was dahinter liegt, ist sichtbar, geordnet und gehört ihm. Programme
dürfen darin arbeiten, aber nur dort, wo man sie hineinlässt.

Alles hat seinen Platz, alles ist auf seinem Platz. Auch die Programme.
