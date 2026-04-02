# UDP Viewer Szenarien

Dieses Dokument ergänzt das Benutzerhandbuch um praxisnahe Szenarien.
Jedes Szenario folgt derselben Struktur, damit du schnell erkennst, ob
es zu deiner aktuellen Aufgabe passt und wie du dabei mit UDP Viewer
vorgehen kannst.

Verwandte Dokumente:

- [Benutzerhandbuch](USER_GUIDE_de.md)
- [Szenario-Abbildungen](SCENARIO_IMAGES_de.md)
- [Unterstützte CSV-Eingabeformate](SUPPORTED_CSV_INPUT_FORMATS_de.md)
- [Simulationsreferenz](SIMULATION_REFERENCE_de.md)

## Inhaltsverzeichnis

- [Szenario 1 Drift eines ESP32-Sensorknotens prüfen](#szenario-1-drift-eines-esp32-sensorknotens-prüfen)
- [Szenario 2 Arduino-Firmware nach einer Änderung prüfen](#szenario-2-arduino-firmware-nach-einer-änderung-prüfen)
- [Szenario 3 Regelverhalten eines ESP-IDF-Projekts bewerten](#szenario-3-regelverhalten-eines-esp-idf-projekts-bewerten)
- [Szenario 4 Digitale Zustände eines ESP32 zeitlich prüfen](#szenario-4-digitale-zustände-eines-esp32-zeitlich-prüfen)
- [Szenario 5 Laufzeit eines batteriebetriebenen IoT-Knotens bewerten](#szenario-5-laufzeit-eines-batteriebetriebenen-iot-knotens-bewerten)
- [Szenario 6 Boot-Sequenz eines Geräts analysieren](#szenario-6-boot-sequenz-eines-geräts-analysieren)
- [Szenario 7 Einen verrauschten UDP-Datenstrom eingrenzen](#szenario-7-einen-verrauschten-udp-datenstrom-eingrenzen)
- [Szenario 8 Einen normalen und einen fehlerhaften Lauf vergleichen](#szenario-8-einen-normalen-und-einen-fehlerhaften-lauf-vergleichen)
- [Szenario 9 Protokoll-Regression nach einem Firmware-Update erkennen](#szenario-9-protokoll-regression-nach-einem-firmware-update-erkennen)
- [Szenario 10 Einen gelieferten Mitschnitt reproduzierbar auswerten](#szenario-10-einen-gelieferten-mitschnitt-reproduzierbar-auswerten)

## Szenario 1 Drift eines ESP32-Sensorknotens prüfen

### Ziel

Herausfinden, ob ein Sensorknoten wirklich driftet oder ob du nur
vereinzelt unruhige Messwerte siehst.

### Ausgangssituation

Du hast einen ESP32, der regelmäßig UDP-Textmeldungen und CSV-Werte für
Temperatur, Feuchte und Versorgungsspannung sendet. Nach einiger Zeit
wirkt die Temperatur zu hoch, obwohl sich an der Umgebung nichts
erkennbar geändert hat.

### Typische Symptome

- die Temperatur steigt langsam und nicht sprunghaft
- einzelne Werte sehen noch plausibel aus, der Gesamttrend aber nicht
- im Textlog ist nicht sofort zu erkennen, ob Sensor, Firmware oder
  Übertragung die Ursache ist

### Warum UDP Viewer hier hilft

Du siehst Textlog und CSV-Verlauf parallel. Dadurch musst du nicht
zwischen mehreren Werkzeugen wechseln und erkennst schneller, ob der
Trend echt ist oder nur aus vereinzelten Ausreißern besteht.

### Vorgehensweise

1. Lege ein neues Projekt für den Lauf an und notiere kurz, was du
   prüfen willst.
2. Verbinde dich mit dem UDP-Stream des ESP32.
3. Setze bei Bedarf einen Filter auf die sensorbezogenen Meldungen.
4. Öffne den Plot-Visualizer für Temperatur und Versorgungsspannung.
5. Beobachte den Verlauf über einige Minuten.
6. Miss im Plot-Visualizer den Abstand zwischen zwei Zeitpunkten.
7. Sichere Log und Screenshots, sobald das Verhalten klar ist.

### Erwartete Erkenntnisse

- ob der Wert wirklich wegdriftet oder nur gelegentlich schwankt
- ob sich der Verlauf zusammen mit der Versorgungsspannung verändert
- ob zeitgleich Reconnects, Warnungen oder Kalibrierhinweise im Log
  auftauchen

### Geeignete UDP-Viewer-Funktionen

- `PROJECT`
- `CONNECT`
- `Filter`
- Plot-Visualizer
- Plot-Messung
- `SAVE`
- Screenshot-Export

### Bilder

- [Abbildung 1 Hauptfenster-Überblick](SCENARIO_IMAGES_de.md#abbildung-1-hauptfenster-überblick)
- [Abbildung 4 Plot-Visualizer-Konfiguration](SCENARIO_IMAGES_de.md#abbildung-4-plot-visualizer-konfiguration)
- [Abbildung 6 Plot-Visualizer mit Tooltip](SCENARIO_IMAGES_de.md#abbildung-6-plot-visualizer-mit-tooltip)

### Hinweise / Grenzen

UDP Viewer macht das Muster sichtbar. Ob die Ursache im Sensor, in der
Kalibrierung oder in der Firmware liegt, musst du danach immer noch im
System selbst bestätigen.

## Szenario 2 Arduino-Firmware nach einer Änderung prüfen

### Ziel

Prüfen, ob eine geänderte Arduino-Firmware weiter die erwarteten Logs
und CSV-Daten liefert.

### Ausgangssituation

Du hast an einer Firmware etwas angepasst, zum Beispiel neue
Statusmeldungen ergänzt oder ein CSV-Feld geändert. Jetzt willst du
sicher sein, dass die Ausgabe noch zu deinem bisherigen Workflow passt.

### Typische Symptome

- Feldnamen oder Feldreihenfolge haben sich unbemerkt geändert
- Textmeldungen sehen korrekt aus, aber der Plot bleibt leer
- ein altes Preset funktioniert plötzlich nicht mehr sauber

### Warum UDP Viewer hier hilft

Du prüfst Ablauf und Datenformat an derselben Stelle. So siehst du
sofort, ob die Firmware zwar noch sendet, aber strukturell nicht mehr
zu deinen bestehenden Visualizer-Einstellungen passt.

### Vorgehensweise

1. Lege ein neues Projekt für den Firmware-Check an.
2. Verbinde den Viewer vor dem Neustart oder Flashen des Geräts.
3. Beobachte Boot- und Initialisierungsmeldungen im Hauptfenster.
4. Öffne den Plot-Visualizer mit der vorhandenen Konfiguration.
5. Prüfe, ob alle erwarteten CSV-Felder weiter sauber ankommen.
6. Spiele den Mitschnitt bei Bedarf später erneut per Replay ab.

### Erwartete Erkenntnisse

- ob das Format noch zu deiner bisherigen Konfiguration passt
- ob Felder hinzugekommen, verschwunden oder verschoben sind
- ob du nur das Preset anpassen musst oder die Firmware selbst

### Geeignete UDP-Viewer-Funktionen

- `PROJECT`
- `CONNECT`
- `SAVE`
- Replay über `Open Log…`
- Plot-Visualizer

### Bilder

- [Abbildung 1 Hauptfenster-Überblick](SCENARIO_IMAGES_de.md#abbildung-1-hauptfenster-überblick)
- [Abbildung 3 Projekt-Dialog](SCENARIO_IMAGES_de.md#abbildung-3-projekt-dialog)
- [Abbildung 4 Plot-Visualizer-Konfiguration](SCENARIO_IMAGES_de.md#abbildung-4-plot-visualizer-konfiguration)

### Hinweise / Grenzen

Gerade bei CSV-basierten Prüfungen fällt oft erst hier auf, dass eine
kleine Protokolländerung große Auswirkungen auf die Auswertung hat.

## Szenario 3 Regelverhalten eines ESP-IDF-Projekts bewerten

### Ziel

Beurteilen, ob ein Regelkreis stabil läuft oder ob du Überschwingen und
zu langes Einschwingen hast.

### Ausgangssituation

Dein ESP32 mit ESP-IDF sendet CSV-Werte für Sollwert, Istwert und
Stellgröße. Auf den ersten Blick läuft alles, aber beim genaueren
Hinsehen wirkt der Verlauf träger oder unruhiger als erwartet.

### Typische Symptome

- der Istwert schießt nach einer Änderung über das Ziel hinaus
- die Stellgröße pendelt, obwohl der Sollwert konstant ist
- im Textlog gibt es keinen klaren Fehlerhinweis

### Warum UDP Viewer hier hilft

Im Plot-Visualizer siehst du den Verlauf sofort in einer Form, die du
direkt bewerten kannst. Das spart dir den Umweg über externe Tools oder
das mühsame Lesen roher CSV-Zeilen.

### Vorgehensweise

1. Verbinde dich mit dem laufenden Controller.
2. Öffne den Plot-Visualizer für Sollwert, Istwert und Stellgröße.
3. Lass das Hauptfenster geöffnet, um Kontextmeldungen parallel zu
   sehen.
4. Markiere zwei Zeitpunkte, um die Einschwingzeit abzuschätzen.
5. Sichere das Ergebnis mit Screenshots im Projekt.

### Erwartete Erkenntnisse

- ob der Regelkreis zu stark überschwingt
- ob sich das System schnell genug beruhigt
- ob Warnungen oder Debug-Meldungen zeitlich zum auffälligen Verlauf
  passen

### Geeignete UDP-Viewer-Funktionen

- Plot-Visualizer
- Plot-Messung
- Highlight-Regeln
- Screenshot-Export

### Bilder

- [Abbildung 4 Plot-Visualizer-Konfiguration](SCENARIO_IMAGES_de.md#abbildung-4-plot-visualizer-konfiguration)
- [Abbildung 5 Plot-Visualizer-Details](SCENARIO_IMAGES_de.md#abbildung-5-plot-visualizer-details)
- [Abbildung 6 Plot-Visualizer mit Tooltip](SCENARIO_IMAGES_de.md#abbildung-6-plot-visualizer-mit-tooltip)

### Hinweise / Grenzen

Die Bewertung wird damit deutlich einfacher. Die eigentliche
Reglerauslegung musst du trotzdem fachlich im Projekt selbst
entscheiden.

## Szenario 4 Digitale Zustände eines ESP32 zeitlich prüfen

### Ziel

Prüfen, ob digitale Zustände in der richtigen Reihenfolge und mit dem
richtigen Timing auftreten.

### Ausgangssituation

Dein Gerät sendet Zustände wie `ready`, `relay_on` oder `door_open` als
CSV-Logic-Kanäle. Du hast den Verdacht, dass ein Zustand zu früh oder
zu spät wechselt.

### Typische Symptome

- zwei Zustände erscheinen vertauscht
- ein Signal bleibt länger aktiv als erwartet
- ein Timeout taucht erst später im Log auf, obwohl das eigentliche
  Timingproblem vorher beginnt

### Warum UDP Viewer hier hilft

Im Logic-Visualizer erkennst du den zeitlichen Ablauf direkt und kannst
Abstände messen, ohne die Daten erst exportieren oder aufbereiten zu
müssen.

### Vorgehensweise

1. Verbinde dich mit dem CSV-Logic-Stream.
2. Öffne den Logic-Visualizer und prüfe die aktiven Kanäle.
3. Starte eine Messung an der ersten relevanten Flanke.
4. Setze den zweiten Messpunkt an der passenden Gegenflanke.
5. Nutze `Space` und `Esc`, um schnell zwischen Messung und Live-Betrieb
   zu wechseln.

### Erwartete Erkenntnisse

- ob die Reihenfolge der Zustände zur Implementierung passt
- ob das Timeout ein Folgefehler oder die eigentliche Ursache ist
- ob das Problem zuverlässig oder nur gelegentlich auftritt

### Geeignete UDP-Viewer-Funktionen

- Logic-Visualizer
- Logic-Messung
- Screenshot-Export
- Replay

### Bilder

- [Abbildung 7 Logic-Visualizer-Konfiguration](SCENARIO_IMAGES_de.md#abbildung-7-logic-visualizer-konfiguration)
- [Abbildung 8 Logic-Visualizer mit Messung](SCENARIO_IMAGES_de.md#abbildung-8-logic-visualizer-mit-messung)

### Hinweise / Grenzen

Besonders hilfreich ist das, wenn du reale GPIO-Signale nicht direkt
misst, sondern nur ihre gemeldeten Zustände im Stream siehst.

## Szenario 5 Laufzeit eines batteriebetriebenen IoT-Knotens bewerten

### Ziel

Prüfen, ob ein batteriebetriebenes Gerät über längere Zeit stabil
sendet.

### Ausgangssituation

Du hast einen mobilen Knoten, der alle paar Sekunden Statusdaten
schickt. Während eines längeren Laufs willst du nachvollziehen, ob bei
sinkender Batteriespannung die Sendeabstände unruhig werden oder Werte
ausfallen.

### Typische Symptome

- die Zeit zwischen zwei Paketen wird unregelmäßig
- Warnungen zur Versorgung tauchen erst spät auf
- nach einem längeren Lauf ist schwer nachvollziehbar, wann das Problem
  begonnen hat

### Warum UDP Viewer hier hilft

Mit Projekt, Log und Plot kannst du einen längeren Lauf sauber
festhalten und später noch einmal nachvollziehen, statt nur lose Dateien
oder einzelne Screenshots zu haben.

### Vorgehensweise

1. Lege vor dem Lauf ein Projekt an.
2. Notiere in der Projektbeschreibung kurz den Testkontext.
3. Beobachte Textmeldungen und CSV-Felder parallel.
4. Sichere Screenshots, wenn Spannung oder Sendeabstand auffällig
   werden.
5. Speichere den kompletten Lauf für die spätere Auswertung.

### Erwartete Erkenntnisse

- ob sich das Sendeintervall im Verlauf verändert
- ob niedrige Spannung mit Lücken im Datenstrom zusammenfällt
- ob du den Lauf später per Replay reproduzierbar bewerten kannst

### Geeignete UDP-Viewer-Funktionen

- `PROJECT`
- `SAVE`
- Plot-Visualizer
- Screenshot-Export
- Replay

### Bilder

- [Abbildung 3 Projekt-Dialog](SCENARIO_IMAGES_de.md#abbildung-3-projekt-dialog)
- [Abbildung 6 Plot-Visualizer mit Tooltip](SCENARIO_IMAGES_de.md#abbildung-6-plot-visualizer-mit-tooltip)

### Hinweise / Grenzen

Dieses Szenario ist besonders nützlich, wenn du einen längeren Lauf
nicht permanent beobachtest, ihn aber später nachvollziehbar auswerten
willst.

## Szenario 6 Boot-Sequenz eines Geräts analysieren

### Ziel

Prüfen, ob ein Gerät beim Start die erwarteten Schritte in der richtigen
Reihenfolge durchläuft.

### Ausgangssituation

Nach dem Einschalten sendet das Gerät Logs für Netzwerkinitialisierung,
Dienststart und Bereitschaft. Manchmal läuft der Start sauber durch,
manchmal wirkt das Gerät zwar aktiv, ist aber noch nicht wirklich
betriebsbereit.

### Typische Symptome

- erwartete Startmeldungen fehlen
- das Gerät reagiert teilweise, aber nicht vollständig
- ein guter und ein schlechter Start unterscheiden sich nur in wenigen
  Zeilen

### Warum UDP Viewer hier hilft

Du kannst den kompletten Startablauf live mitschneiden und später mit
einem Referenzlauf vergleichen. Gerade bei sporadischen Startproblemen
spart das viel Zeit.

### Vorgehensweise

1. Verbinde dich vor dem Neustart mit dem Gerät.
2. Beobachte die Startmeldungen im Hauptfenster.
3. Hebe wichtige Phasen farblich hervor.
4. Speichere den Lauf und vergleiche ihn mit einem bekannten guten
   Ablauf.

### Erwartete Erkenntnisse

- ob Startmeldungen vollständig vorhanden sind
- an welcher Stelle der fehlerhafte Ablauf abweicht
- ob das Problem vor oder nach der Netzwerkbereitschaft beginnt

### Geeignete UDP-Viewer-Funktionen

- `CONNECT`
- Highlight-Regeln
- `SAVE`
- Replay

### Bilder

- [Abbildung 1 Hauptfenster-Überblick](SCENARIO_IMAGES_de.md#abbildung-1-hauptfenster-überblick)
- [Abbildung 2 Regelkonfiguration](SCENARIO_IMAGES_de.md#abbildung-2-regelkonfiguration)

### Hinweise / Grenzen

Dieses Szenario hilft bei Reihenfolge und Timing von Meldungen. Für
Low-Level-Netzwerkanalyse brauchst du weiterhin spezialisierte Tools.

## Szenario 7 Einen verrauschten UDP-Datenstrom eingrenzen

### Ziel

Einen großen Datenstrom so reduzieren, dass du den eigentlichen Fehler
noch live verfolgen kannst.

### Ausgangssituation

Mehrere Teile deines Systems senden gleichzeitig. Während eines Tests
suchst du aber nur die Warnungen und Zustandswechsel eines bestimmten
Bereichs und willst nicht ständig im gesamten Strom nach ihnen suchen.

### Typische Symptome

- der Stream scrollt zu schnell
- Warnungen verschwinden sofort wieder aus dem Blick
- Ursache und Folge lassen sich im Live-Betrieb kaum noch zuordnen

### Warum UDP Viewer hier hilft

Mit `Filter`, `Exclude` und `Highlight` bekommst du den Stream so weit
verdichtet, dass du weiter live arbeiten kannst, ohne den Gesamtkontext
komplett zu verlieren.

### Vorgehensweise

1. Verbinde dich zunächst mit dem vollständigen Stream.
2. Setze Filter-Regeln für den relevanten Bereich.
3. Blende bekannte Wiederholungsmuster mit Exclude aus.
4. Hebe Warnungen und Zustandswechsel hervor.
5. Speichere die fokussierte Session für spätere Vergleiche.

### Erwartete Erkenntnisse

- ein deutlich kleinerer und besser lesbarer Stream
- klarere Zusammenhänge zwischen Warnung und Zustandswechsel
- wiederverwendbare Regeln für ähnliche Tests

### Geeignete UDP-Viewer-Funktionen

- `Filter`
- `Exclude`
- `Highlight`
- `SAVE`

### Bilder

- [Abbildung 1 Hauptfenster-Überblick](SCENARIO_IMAGES_de.md#abbildung-1-hauptfenster-überblick)
- [Abbildung 2 Regelkonfiguration](SCENARIO_IMAGES_de.md#abbildung-2-regelkonfiguration)

### Hinweise / Grenzen

Ob ein großer Stream noch sinnvoll live auswertbar ist, hängt oft direkt
von guten Regeln ab.

## Szenario 8 Einen normalen und einen fehlerhaften Lauf vergleichen

### Ziel

Verstehen, an welcher Stelle ein fehlerhafter Lauf vom normalen Verlauf
abweicht.

### Ausgangssituation

Du hast zwei Mitschnitte: einen unauffälligen Lauf und einen mit
Fehlerbild. Der Defekt lässt sich im Moment nicht gezielt reproduzieren,
du willst aber trotzdem systematisch vergleichen.

### Typische Symptome

- die Randbedingungen wirken gleich, das Ergebnis aber nicht
- das Problem ist nur noch im Mitschnitt verfügbar
- die Analyse findet erst deutlich später statt

### Warum UDP Viewer hier hilft

Mit Replay kannst du beide Läufe in derselben Oberfläche ansehen und
gezielt auf die Phasen gehen, in denen sich das Verhalten unterscheidet.

### Vorgehensweise

1. Öffne zuerst den bekannten guten Mitschnitt.
2. Suche die relevante Phase und merke dir die markanten Stellen.
3. Öffne den fehlerhaften Mitschnitt und spiele denselben Abschnitt ab.
4. Vergleiche Meldungsreihenfolge, Warnungen und Telemetrie.
5. Sichere Screenshots oder Notizen in getrennten Projekten.

### Erwartete Erkenntnisse

- die genaue Stelle, an der beide Läufe auseinanderlaufen
- ob der Fehler zuerst im Log, in der Telemetrie oder in beidem sichtbar
  wird
- eine bessere Grundlage für die eigentliche Ursachenanalyse

### Geeignete UDP-Viewer-Funktionen

- `Open Log…`
- Replay
- Plot-Visualizer
- Logic-Visualizer

### Bilder

- [Abbildung 6 Plot-Visualizer mit Tooltip](SCENARIO_IMAGES_de.md#abbildung-6-plot-visualizer-mit-tooltip)
- [Abbildung 8 Logic-Visualizer mit Messung](SCENARIO_IMAGES_de.md#abbildung-8-logic-visualizer-mit-messung)

### Hinweise / Grenzen

Replay bildet nicht die ursprüngliche Netzsituation nach. Für die
sichtbare Symptomatik reicht es in der Praxis aber oft vollkommen aus.

## Szenario 9 Protokoll-Regression nach einem Firmware-Update erkennen

### Ziel

Erkennen, ob eine Firmware-Änderung das effektive UDP-Protokoll so
verändert hat, dass bestehende Auswertungen nicht mehr sauber laufen.

### Ausgangssituation

Nach einem Update sendet das Gerät weiterhin Daten. Trotzdem zeigt deine
Auswertung plötzlich Lücken, leere Plots oder unplausible Werte.

### Typische Symptome

- Textmeldungen sehen weiterhin unauffällig aus
- einzelne CSV-Felder bleiben leer oder verschwinden
- Namen, Reihenfolgen oder Skalierungen wurden still geändert

### Warum UDP Viewer hier hilft

Du erkennst sofort, ob das Problem nur in der Darstellung liegt oder ob
die Firmware-Ausgabe selbst nicht mehr zur bisherigen Struktur passt.

### Vorgehensweise

1. Verbinde dich mit der aktualisierten Firmware oder öffne einen
   Mitschnitt davon.
2. Prüfe im Textlog, ob Protokoll- oder Versionshinweise auftauchen.
3. Öffne die passende Visualizer-Konfiguration.
4. Kontrolliere, ob alle erwarteten Felder sauber gefüllt werden.
5. Dokumentiere die Abweichung im Projekt.

### Erwartete Erkenntnisse

- ob die Regression textuell, strukturell oder numerisch ist
- ob nur dein Preset angepasst werden muss
- ob die Firmware-Ausgabe selbst nicht mehr kompatibel ist

### Geeignete UDP-Viewer-Funktionen

- `CONNECT`
- Replay
- Plot-Visualizer
- `PROJECT`

### Bilder

- [Abbildung 4 Plot-Visualizer-Konfiguration](SCENARIO_IMAGES_de.md#abbildung-4-plot-visualizer-konfiguration)
- [Abbildung 5 Plot-Visualizer-Details](SCENARIO_IMAGES_de.md#abbildung-5-plot-visualizer-details)

### Hinweise / Grenzen

Besonders hilfreich ist dieses Szenario, wenn Protokolländerungen nicht
vollständig dokumentiert wurden.

## Szenario 10 Einen gelieferten Mitschnitt reproduzierbar auswerten

### Ziel

Aus einer einzelnen Logdatei einen nachvollziehbaren Analysefall machen.

### Ausgangssituation

Du bekommst einen gespeicherten Mitschnitt und eine kurze
Fehlerbeschreibung. Die originale Situation steht dir nicht direkt zur
Verfügung, du willst den Fall aber trotzdem sauber nachvollziehen und
weitergeben können.

### Typische Symptome

- die Beschreibung ist knapp und lückenhaft
- die Hardware ist gerade nicht verfügbar
- mehrere Beteiligte sollen denselben Fall verstehen

### Warum UDP Viewer hier hilft

Mit Projekt, Replay, Screenshots und Visualizern kannst du aus einer
einzelnen Datei wieder einen strukturierten Analysefall machen.

### Vorgehensweise

1. Lege ein neues Projekt mit passender Bezeichnung an.
2. Übernimm die Kurzbeschreibung in die Projektbeschreibung.
3. Öffne den Mitschnitt und spiele ihn per Replay ab.
4. Aktiviere Filter und Visualizer für die vermutete Ursache.
5. Sichere Screenshots und halte den Projektordner als Fallpaket fest.

### Erwartete Erkenntnisse

- ein reproduzierbarer Ablauf für die interne Analyse
- eine bessere Übergabe zwischen den beteiligten Personen
- ein nachvollziehbares Paket statt nur einer einzelnen Logdatei

### Geeignete UDP-Viewer-Funktionen

- `PROJECT`
- `Open Log…`
- Replay
- Screenshots
- `SAVE`

### Bilder

- [Abbildung 3 Projekt-Dialog](SCENARIO_IMAGES_de.md#abbildung-3-projekt-dialog)
- [Abbildung 1 Hauptfenster-Überblick](SCENARIO_IMAGES_de.md#abbildung-1-hauptfenster-überblick)

### Hinweise / Grenzen

Dieses Szenario ist oft der sauberste Weg, um einen Fall aus einer
gespeicherten Datei nachvollziehbar weiterzugeben.
