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

- Aktionsleiste mit `SAVE`, `CLEAR`, `COPY`, `CONNECT`, `PAUSE`
- Optionen `Auto-Scroll` und `Timestamp`
- Eingabefeldern für `Bind-IP`, `Port` und `Max lines`
- Bereichen für `Filter`, `Exclude` und `Highlight`
- Haupt-Logansicht
- Menüleiste mit `File`, `Tools` und `Visualize`

Wichtig zur Menüführung:

- auf macOS können `Preferences...` und `Quit` systemtypisch im App-Menü erscheinen
- auf Windows und Linux liegen diese Einträge typischerweise im `File`-Menü

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

### 5.3 `COPY`

`COPY` kopiert den sichtbaren Inhalt der Hauptansicht in die Zwischenablage.

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

## 9. Visualizer-Nutzung

Im Menü `Visualize` finden sich die Visualizer-Funktionen.

Aktuell relevant:

- Temperatur-Visualizer
- Logic-Visualizer

Typischer Arbeitsablauf:

1. Visualizer-Konfiguration öffnen
2. `filter_string` und Felder passend zur eingehenden CSV-Struktur definieren
3. Visualizer-Fenster anzeigen
4. passende CSV-Zeilen empfangen oder simulieren

### 9.1 Sliding Window im Graph-Fenster

Sowohl der Temperatur- als auch der Logic-Visualizer besitzen eine direkte Sliding-Window-Steuerung im Fenster selbst.

Sichtbare Bedienelemente:

- `Sliding Window`
- Presets `100`, `150`, `200`, `300`
- `Window Size`
- `Reset`
- `Auto Refresh`

Bedeutung:

- `Sliding Window` aktiv
  zeigt immer nur die letzten `N` Samples
- `Window Size`
  bestimmt die aktuell sichtbare Fenstergröße
- Presets
  setzen die Fenstergröße schnell auf typische Werte
- `Reset`
  setzt die Laufzeiteinstellung auf den konfigurierten Default des jeweiligen Graphen zurück

Wichtig:

- Änderungen im geöffneten Graph-Fenster sind zunächst Laufzeit-Overrides
- die persistente Default-Vorgabe kommt aus der Graph-Konfiguration bzw. aus den globalen Präferenzen

Wichtig:

- der Viewer definiert die CSV-Struktur des Sendesystems nicht
- er kann Daten nur dann visualisieren, wenn Filter-Token, Feldanzahl und Feldbedeutung zur Visualizer-Konfiguration passen

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

- [DOKUMENTATION_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOKUMENTATION_de.md)
- [CONFIGURATION_REFERENCE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/CONFIGURATION_REFERENCE_de.md)
- [SUPPORTED_CSV_INPUT_FORMATS_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/SUPPORTED_CSV_INPUT_FORMATS_de.md)
- [BUILD_AND_PACKAGING_REFERENCE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/BUILD_AND_PACKAGING_REFERENCE_de.md)
