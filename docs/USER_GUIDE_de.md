# Benutzerhandbuch des UDP Viewers

Dieses Dokument beschreibt die sichtbare Nutzung des UDP Viewers aus Anwendersicht. Es ist bewusst arbeitsablauforientiert aufgebaut und ergänzt die technischen Referenzen zu Konfiguration, CSV-Eingabeformaten sowie Build und Packaging.

## 1. Zweck der Anwendung

Der UDP Viewer dient dazu, Text- und Telemetriedaten per UDP zu empfangen, sichtbar zu machen, zu filtern, mit Farben hervorzuheben, lokal mitzuschreiben und bei Bedarf in Diagrammen zu visualisieren.

Typische Einsatzfälle:

- Echtzeitbeobachtung von Embedded-Logs
- Filtern relevanter Meldungen während der Entwicklung
- Hervorheben von Fehler- oder Zustandsmustern
- Replay gespeicherter Logs
- Simulation typischer Datenströme ohne reales Sendesystem
- Visualisierung strukturierter CSV-artiger Telemetriedaten

## 2. Überblick über die Hauptoberfläche

Die Hauptoberfläche besteht im Wesentlichen aus:

- Aktionsleiste mit `SAVE`, `RESET`, `CLEAR`, `COPY`, `CONNECT`, `PAUSE`
- Optionen `Auto-Scroll` und `Timestamp`
- Eingabefeldern für `Bind-IP`, `Port` und `Max lines`
- Bereichen für `Filter`, `Exclude` und `Highlight`
- Haupt-Logansicht
- Menüleiste mit `File`, `Tools` und `Visualize`

Wichtig zur Menüführung:

- auf macOS können `Preferences...` und `Quit` systemtypisch im App-Menü erscheinen
- auf Windows und Linux liegen diese Einträge typischerweise im `File`-Menü

![Hauptfenster mit aktiver Verbindung, Highlight-Chips und Reset-Button](../assets/screenshots/udp_log_viewer_main_highlighted.png)

## 3. Erster Start und typische Verbindung

### 3.1 Bind-IP und Port

Vor dem Start des UDP-Empfangs werden üblicherweise folgende Felder gesetzt:

- `Bind-IP`
- `Port`

Typische Varianten:

- `0.0.0.0`
  lauscht auf allen lokalen Interfaces
- eine konkrete lokale IP
  lauscht nur auf diesem Interface

### 3.2 Verbindung starten

Zum Start des Empfangs:

1. `Bind-IP` und `Port` eintragen oder bestehende Werte übernehmen
2. `CONNECT` drücken

Erwartetes Verhalten:

- der Button wechselt in den verbundenen Zustand
- eine Live-Logdatei wird für diese Session vorbereitet
- eingehende UDP-Zeilen erscheinen in der Hauptansicht
- die Statusleiste zeigt den aktiven Zustand an

### 3.3 Verbindung beenden

Zum Trennen:

1. erneut `CONNECT` drücken
2. gegebenenfalls den Save-Dialog bestätigen

Erwartetes Verhalten:

- der Listener wird beendet
- die App kehrt in den getrennten Zustand zurück
- die letzte Session kann weiter gespeichert werden

## 4. Laufende Bedienung während einer Session

### 4.1 `PAUSE`

`PAUSE` stoppt die fortlaufende Aktualisierung der sichtbaren Logansicht.

Praktisch bedeutet das:

- du kannst eine laufende Ansicht anhalten
- nach dem Lösen der Pause läuft die Anzeige wieder weiter
- der genaue Umgang mit Puffern ist intern geregelt und muss für die normale Nutzung nicht manuell gesteuert werden

### 4.2 `Auto-Scroll`

Wenn `Auto-Scroll` aktiv ist:

- springt die Hauptansicht bei neuen Zeilen an das Ende

Wenn `Auto-Scroll` deaktiviert ist:

- bleibt die aktuelle Scrollposition erhalten

Das ist besonders nützlich, wenn ältere Logbereiche untersucht werden sollen, ohne dass neue Zeilen die Sicht verschieben.

### 4.3 `Timestamp`

Wenn `Timestamp` aktiv ist:

- ergänzt die App lokale Zeitstempel in der angezeigten Ausgabe

Wichtig:

- die Option wirkt sich auf die Anzeige im Viewer aus
- je nach Ablauf gilt die Änderung beim nächsten `CONNECT`

### 4.4 `Max lines`

Dieses Feld begrenzt die Anzahl sichtbarer Zeilen in der Hauptansicht.

Nutzen:

- verhindert ungebremstes Anwachsen des sichtbaren Puffers
- hilft, die GUI bei langen Sessions reaktionsfähig zu halten

## 5. Arbeiten mit Logs

### 5.1 `SAVE`

`SAVE` speichert die aktuelle oder letzte Session.

Im aktuellen Verhalten bevorzugt die App:

- die zugrunde liegende Live-Logdatei der Session

Falls keine geeignete Datei vorliegt:

- wird auf den aktuell sichtbaren Textinhalt zurückgegriffen

### 5.2 `CLEAR`

`CLEAR` leert die sichtbare Hauptansicht.

Das dient vor allem dazu:

- die Anzeige für eine neue Beobachtungsphase aufzuräumen
- aktuelle Effekte von Filtern oder Highlights übersichtlicher zu prüfen

### 5.3 `RESET`

`RESET` startet innerhalb derselben App-Session eine neue Log-Phase.

Dabei passiert im aktuellen Verhalten:

- die sichtbare Hauptansicht wird geleert
- interne Buffer und Zähler werden zurückgesetzt
- `CONNECT` geht auf `OFF`
- das laufende Live-Log wird sauber abgeschlossen
- sofort wird eine neue Live-Logdatei mit aktuellem Zeitstempel vorbereitet
- ein aktives `PROJECT` bleibt erhalten

Praktischer Nutzen:

- neue Testphase beginnen, ohne die Anwendung neu zu starten
- neue Logdatei mit sauberem Anfang erzeugen
- weiterhin im gleichen Projektordner weiterarbeiten

### 5.4 `COPY`

`COPY` kopiert den sichtbaren Inhalt der Hauptansicht in die Zwischenablage.

### 5.5 Tastaturbedienung im Hauptfenster

Das Hauptfenster unterstützt eine explizite Tastaturbedienung über
`TAB` und `Shift` + `TAB`.

Damit lassen sich nacheinander unter anderem erreichen:

- `PROJECT`
- `SAVE`
- `RESET`
- `CLEAR`
- `COPY`
- `CONNECT`
- `PAUSE`
- die Eingabefelder für `Bind-IP`, `Port` und `Max lines`

Zusätzliche Save-Kürzel:

- `Ctrl` + `S`
- `Cmd` + `S`
- `F12`

### 5.6 `PROJECT`

Im `PROJECT`-Dialog steht jetzt zusätzlich eine mehrzeilige
Markdown-Beschreibung zur Verfügung.

Verhalten:

- beim Erstellen oder Speichern eines Projekts wird eine Datei
  `README_<projectname>.md` im Projektordner geschrieben
- Standardinhalt ist eine Überschrift mit Projektname und aktuellem
  Zeitstempel
- die Beschreibung ist auf `1024` Zeichen begrenzt
- erlaubte Zeichen im Projektnamen sind `A-Za-z`, `0-9`, `_` und `-`

![Projekt-Dialog mit mehrzeiliger Markdown-Beschreibung](../assets/screenshots/udp_log_viewer_project_config.png)

## 6. Filter, Exclude und Highlight

Die App bietet jeweils Slot-basierte Regeln für:

- `Filter`
- `Exclude`
- `Highlight`

Jeder Bereich kann mehrere Regeln enthalten, die als Chips sichtbar werden.

### 6.1 Filter

Filter begrenzen die sichtbaren Zeilen auf passende Inhalte.

Typischer Einsatz:

- nur Meldungen eines Subsystems anzeigen
- nur bestimmte Zustände oder Tags beobachten

Wenn keine Filterregeln aktiv sind:

- werden grundsätzlich alle nicht anderweitig verworfenen Zeilen angezeigt

### 6.2 Exclude

Exclude-Regeln unterdrücken unerwünschte Meldungen.

Typischer Einsatz:

- periodische Statusmeldungen ausblenden
- bekannte, wenig hilfreiche Wiederholungen aus der Hauptansicht fernhalten

### 6.3 Highlight

Highlight-Regeln färben passende Meldungen in der Anzeige ein.

Typischer Einsatz:

- Fehlerfälle rot markieren
- bestimmte Zustände oder Teilsysteme farblich hervorheben

### 6.4 Regeln anlegen und ändern

Der typische Ablauf ist in allen drei Bereichen ähnlich:

1. passenden Button drücken, zum Beispiel `FILTER`, `EXCLUDE` oder `HIGHLIGHT`
2. Muster und Modus eingeben
3. gegebenenfalls Farbe wählen
4. Regel bestätigen

Vorhandene Chips können anschließend bearbeitet oder entfernt werden.

![Filter-Regel-Konfiguration im Dialog](../assets/screenshots/udp_log_viewer_main_rule_config.png)

### 6.5 Zurücksetzen

Über `RESET` im Regelbereich lassen sich aktive Regeln wieder zurücksetzen.

## 7. Replay von Logdateien

Die Anwendung kann bestehende Logdateien erneut einspeisen.

Typischer Ablauf:

1. `File -> Open Log…`
2. Textdatei auswählen
3. Replay startet und injiziert die Zeilen in denselben internen Verarbeitungsweg wie Live-Daten

Zusätzlich existieren Menüpunkte für:

- `Replay Sample`
- `Stop Replay`
- `Preferences...`
- `Save…`
- `Quit`

Praktischer Nutzen:

- Fehlerbilder reproduzieren
- Filter- oder Highlight-Regeln ohne Live-System testen
- Visualizer-Verhalten anhand vorhandener Dateien prüfen

## 8. Simulation

Im Menü `Tools` stehen integrierte Simulationen zur Verfügung.

Vorhandene Richtungen:

- `Simulate Traffic`
- `Simulate Temperature Traffic`
- `Simulate Logic Traffic`

Diese Funktionen sind hilfreich, wenn:

- gerade kein reales Sendesystem aktiv ist
- UI-Verhalten geprüft werden soll
- Visualizer-Fenster mit Testdaten gespeist werden sollen

Im aktuellen Verhalten erfordern bestimmte Simulationen eine aktive Verbindung.

![Menüeintrag für integrierte Traffic-Simulationen](../assets/screenshots/udp_log_viewer_menu_simulation.png)

## 9. Visualizer-Nutzung

Im Menü `Visualize` finden sich die Visualizer-Funktionen.

Aktuell relevant:

- Temperatur-Visualizer
- Logic-Visualizer

Typischer Arbeitsablauf:

1. Visualizer-Konfiguration öffnen
2. gewünschten Slot `1..5` auswählen
3. `Slot Active` setzen sowie `filter_string` und Felder passend zur eingehenden CSV-Struktur definieren
4. Konfiguration speichern
5. Visualizer-Fenster anzeigen
6. passende CSV-Zeilen empfangen oder simulieren

### 9.0 Slots für Plot und Logic

Sowohl für Plot als auch für Logic existieren jeweils bis zu 5
unabhängige Slots.

Jeder Slot besitzt eine eigene:

- Konfiguration
- Persistenz in der `config.ini`
- Fensterinstanz
- Sample-Historie bzw. Buffer

Im Konfigurationsfenster stehen dafür zusätzliche Bedienelemente bereit:

- `Slot`
- `Slot Active`
- `COPY`
- `CLEAR`

Bedeutung:

- `Slot`
  wählt den zu bearbeitenden Visualizer-Slot
- `Slot Active`
  bestimmt, ob dieser Slot bei `SHOW` geöffnet wird und Daten
  verarbeitet
- `COPY`
  kopiert eine Slot-Konfiguration auf einen anderen Slot desselben Typs
- `CLEAR`
  leert den aktuellen Slot vollständig

Beim Wechsel des Slots mit ungespeicherten Änderungen fragt die App, ob
diese verworfen werden sollen.

Wichtig:

- `SHOW` öffnet alle aktiven Slots des gewählten Typs
- inaktive Slots öffnen kein Fenster und sammeln keine Samples
- leere Slots erscheinen als leere Konfigurationsseite
- eine eingehende CSV-Zeile muss sowohl zum `filter_string` als auch zur
  Feldanzahl des jeweiligen Slots passen

### 9.1 Sliding Window im Graph-Fenster

Sowohl der Temperatur- als auch der Logic-Visualizer besitzen eine direkte Sliding-Window-Steuerung im Fenster selbst.

Sichtbare Bedienelemente:

- `Sliding Window`
- `Legend`
- Presets `100`, `150`, `200`, `300`
- `Window Size`
- `Reset`
- `Auto Refresh`

Bedeutung:

- `Sliding Window` aktiv
  zeigt immer nur die letzten `N` Samples
- `Window Size`
  bestimmt die aktuell sichtbare Fenstergröße
  gültiger Bereich im aktuellen Stand: `1..5000`
- `Legend`
  blendet die Legende im geöffneten Graph-Fenster zur Laufzeit ein oder aus
- Presets
  setzen die Fenstergröße schnell auf typische Werte
- `Reset`
  setzt die Laufzeiteinstellung auf den konfigurierten Default des jeweiligen Graphen zurück

Wichtig:

- Änderungen im geöffneten Graph-Fenster sind zunächst Laufzeit-Overrides
- die persistente Default-Vorgabe kommt aus der Graph-Konfiguration bzw. aus den globalen Präferenzen

![Plot-Visualizer mit Tooltip, Legende und Zielbereichen](../assets/screenshots/udp_log_viewer_plot_tooltip.png)

Zusätzliche Screenshot-Kürzel im Graph-Fenster:

- `Ctrl` + `Shift` + `S`
- `Cmd` + `Shift` + `S`
- `F12`

Auch die Graph-Fenster besitzen eine explizite `TAB`-Navigation über die
sichtbaren Bedienelemente.

### 9.2 Messung im Logic-Graphen

Im Logic-Graphen kann die Zeit zwischen Signalflanken direkt gemessen
werden.

Bedienung:

- Linksklick auf eine Kanalzeile
  startet eine Flankenmessung
- `Shift` + Linksklick auf eine Kanalzeile
  startet eine Periodenmessung
- `Space` oder `Esc`
  löscht die Messung wieder

Verhalten:

- der Start rastet auf die nächste Flanke des gewählten Kanals ein
- bei normalem Klick endet die Messung an der nächsten Flanke desselben Kanals
- bei `Shift`-Klick endet die Messung an der nächsten gleichartigen Flanke
- während eine Messung aktiv ist, pausiert die Graph-Ansicht, damit das Signal nicht weiter nach links wandert
- nach `Space` oder `Esc` läuft die Anzeige wieder mit dem vorherigen Refresh-Zustand weiter

Darstellung:

- rote Startlinie
- blaue Endlinie
- gestrichelte Pfeillinie zwischen Start und Ende
- Zeittext im Format `MM:SS.mmm`
- wenn der Platz zwischen Start und Ende zu klein ist, erscheint der
  Text rechts neben der blauen Endlinie

Wichtig:

- der Viewer definiert die CSV-Struktur des Sendesystems nicht
- er kann Daten nur dann visualisieren, wenn Filter-Token, Feldanzahl und Feldbedeutung zur Visualizer-Konfiguration passen
- für Plot-Fenster muss `matplotlib` in der aktiven Python-Umgebung
  installiert sein

![Logic-Visualizer mit Periodenmessung und Markerlinien](../assets/screenshots/udp_log_viewer_logic_period.png)

## 10. Persistenz aus Anwendersicht

Die App merkt sich wichtige Nutzungsdaten, zum Beispiel:

- `Bind-IP`
- `Port`
- `Auto-Scroll`
- `Timestamp`
- `Max lines`
- Rule-Slots für `Filter`, `Exclude` und `Highlight`
- zuletzt gewählten Pfad zur `config.ini`
- globale Präferenzen wie Sprache und Visualizer-Defaults

Wenn keine verwendbare `config.ini` gefunden wird:

- fragt die App nach einem Speicher- oder Ladeort
- der gewählte Pfad wird anschließend gemerkt

### 10.1 `Preferences...`

Die App besitzt jetzt einen grundlegenden Präferenzdialog.

Dort lassen sich aktuell unter anderem einstellen:

- Sprache
- Default für `Auto-Scroll`
- Default für `Timestamp`
- Default für `Max lines`
- globale Visualizer-Presets
- Default-Sliding-Window-Werte für Plot und Logic

Diese Werte werden in `config.ini` persistiert.

![Preferences-Dialog auf der Registerkarte General](../assets/screenshots/udp_log_viewer_preferences_general.png)

## 11. Typische Arbeitsabläufe

### 11.1 Live-Debugging

1. App starten
2. `Bind-IP` und `Port` setzen
3. `CONNECT`
4. bei Bedarf Filter und Highlight-Regeln anlegen
5. interessante Session mit `SAVE` sichern

### 11.2 Analyse einer vorhandenen Datei

1. App starten
2. `File -> Open Log…`
3. Replay beobachten
4. Filter, Exclude und Highlight auf die Datei anwenden

### 11.3 Visualisierung strukturierter UDP-Daten

1. Visualizer konfigurieren
2. Verbindung aufbauen oder Simulation starten
3. passende CSV-Zeilen einspeisen
4. Diagramm oder Logic-Ansicht beobachten

## 12. Typische Grenzen

Wichtige praktische Grenzen im aktuellen Stand:

- eine Visualisierung funktioniert nur bei passender Feldanzahl und passendem `filter_string`
- Windows-Packaging ist dokumentiert, aber der Installer-Weg ist aktuell noch nicht vollständig konsolidiert
- nicht jeder vorhandene Build- oder Packaging-Pfad ist gleich gut gepflegt

## 13. Weiterführende Referenzen

- [DOKUMENTATION_de.md](../docs/DOKUMENTATION_de.md)
- [CONFIGURATION_REFERENCE_de.md](../docs/CONFIGURATION_REFERENCE_de.md)
- [SUPPORTED_CSV_INPUT_FORMATS_de.md](../docs/SUPPORTED_CSV_INPUT_FORMATS_de.md)
- [BUILD_AND_PACKAGING_REFERENCE_de.md](../docs/BUILD_AND_PACKAGING_REFERENCE_de.md)
