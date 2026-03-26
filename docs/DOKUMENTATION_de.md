# UDP Log Viewer Dokumentation

Dieses Dokument beschreibt den aktuell vorliegenden Stand der Codebasis von `udp-viewer` auf Basis der Repository-Analyse vom 26. März 2026.

## 1. Zweck

UDP Log Viewer ist eine Desktop-Anwendung auf Basis von Python und PyQt5 zum Empfangen, Anzeigen, Filtern, Persistieren, Wiedergeben und Visualisieren von UDP-Logdaten. Das Projekt richtet sich erkennbar vor allem an ESP32- und ähnliche Embedded-Systeme, die Textlogs per UDP statt über USB oder serielle Schnittstellen senden.

Die Anwendung kombiniert zwei Hauptanwendungsfälle:

- Echtzeitüberwachung von Textlogs für Debugging und Diagnose
- Live-Visualisierung strukturierter CSV-artiger Telemetriedaten innerhalb von Logzeilen

## 2. Aktueller Funktionsumfang

Die aktuelle Codebasis implementiert folgende sichtbare Funktionen:

- UDP-Listener mit konfigurierbarer Bind-IP und Port
- Echtzeitdarstellung von Textlogs in einem `QPlainTextEdit`
- Optionales Voranstellen lokaler Zeitstempel an angezeigte Zeilen
- Automatisches Mitschreiben einer Live-Session in eine Datei während der Verbindung
- Manuelles Speichern des aktuellen oder letzten Session-Logs
- UI-Pause/Resume, während die Dateilogik weiterlaufen kann
- Auto-Scroll-Schalter
- Zeilenbegrenzung mit konfigurierbarer Maximalanzahl
- Slot-basierte Filterregeln
- Slot-basierte Exclude-Regeln
- Slot-basierte Highlight-Regeln mit Farbzuteilung
- Replay von Text-Logdateien
- Integriertes Replay-Beispiel für synthetische Textlogs
- Integrierte Simulation für generische Textlogs
- Integrierte Simulation für Temperatur-CSV-Daten
- Integrierte Simulation für Logic-CSV-Daten
- CSV-basierter Datenvisualizer mit zwei Y-Achsen
- Logic-Visualizer für bis zu 8 Kanäle
- Screenshot-Export aus Visualizer-Fenstern
- Persistenz über `QSettings` und `config.ini`
- Plattformübergreifende Packaging-Skripte für macOS und Windows

## 3. Technologie-Stack

- Python 3.11+
- PyQt5
- Matplotlib für Diagramme
- `setuptools` als Build-Backend
- `pytest`, `ruff`, `mypy`, `pre-commit` als Dev-Abhängigkeiten
- `cx_Freeze` für paketierte Desktop-Builds

## 4. Repository-Struktur

Top-Level-Struktur:

- `src/udp_log_viewer/`
  Hauptpaket der Anwendung
- `src/udp_log_viewer/data_visualizer/`
  CSV-Parser, Visualizer-Konfiguration, Visualizer-Fenster, Dialoge, Konfigurationsspeicher
- `tests/`
  Smoke-Tests und manuelle Testskripte rund um das Visualizer-Subsystem
- `scripts/`
  Bootstrap- und Run-Skripte für die Entwicklung
- `packaging/`
  Packaging-Assets für macOS und Windows
- `data/logs/`
  Beispiel- oder generierte Logdateien
- `freeze_setup.py`, `freeze_setup_win.py`, `freeze_entry.py`
  Einstiegspunkte und Konfiguration für Frozen Builds
- `run.py`, `run_udp_log_viewer.py`
  Komfort-Launcher

Wichtige Quelldateien:

- `src/udp_log_viewer/main.py`
  Hauptfenster, Laufzeitsteuerung, Benutzeraktionen, Replay, Simulation, Listener-Lebenszyklus
- `src/udp_log_viewer/udp_listener.py`
  Hintergrund-Thread für UDP-Empfang
- `src/udp_log_viewer/highlighter.py`
  Highlight-Regeln und Syntax-Highlighter
- `src/udp_log_viewer/udp_log_utils.py`
  Queue-Helfer, Pattern-Kompilierung, Include/Exclude-Matching
- `src/udp_log_viewer/app_paths.py`
  App-Verzeichnisse und `config.ini`-Handling

## 5. Laufzeitarchitektur

### 5.1 Hauptablauf

Die Anwendung startet in `udp_log_viewer.main:main()`, erzeugt dort die `QApplication` und instanziiert anschließend `MainWindow`.

`MainWindow` übernimmt:

- Aufbau der GUI
- Laden persistierter Zustände
- Verwaltung des UDP-Listener-Threads
- Puffern und Verarbeiten eingehender Zeilen
- Anwenden von Filter-, Exclude- und Highlight-Logik
- Verwaltung der Live-Logdateien
- Steuerung von Replay- und Simulations-Timern
- Weiterleitung strukturierter Zeilen an das Visualizer-Subsystem

### 5.2 UDP-Empfangspfad

Die UDP-Verarbeitung ist in `UdpListenerThread` implementiert:

1. Socket an konfigurierte IP und Port binden
2. Nicht blockierenden Socket plus `select.select()` verwenden
3. Datagramme empfangen
4. Bytes als UTF-8 mit Ersatzzeichen bei ungültigen Sequenzen dekodieren
5. Datagramme in nichtleere Zeilen zerlegen
6. Jede Zeile über ein Qt-Signal ausgeben

Das Herunterfahren ist bewusst defensiv implementiert:

- `stop()` setzt ein Stop-Event und schließt den Socket
- `EBADF` und verwandte Fehler werden beim Beenden absichtlich nicht als echter Fehler behandelt

### 5.3 UI-Pufferung

Eingehende Zeilen werden nicht direkt in großen Bursts in die GUI geschrieben. `MainWindow` sammelt sie in einer Deque und leert diese über einen Timer alle 50 ms. Das reduziert GUI-Last und erlaubt gebündelte Updates.

### 5.4 Filtermodell

Die Anwendung unterstützt jeweils 5 Slots für:

- Filter
- Exclude
- Highlight

Ein Slot enthält:

- `pattern`
- `mode`: `Substring` oder `Regex`
- `color`

Semantik:

- Filter verwendet UND-Logik über semikolongetrennte Tokens innerhalb eines Slots
- Exclude verwendet ODER-Logik über semikolongetrennte Tokens innerhalb eines Slots
- Highlight prüft pro Slot genau ein Pattern; die erste passende Regel bestimmt die Farbe

### 5.5 Visualizer-Routing

Das Visualizer-Subsystem verarbeitet Zeilen unabhängig von der Textansicht. Jede Visualizer-Konfiguration besitzt einen `filter_string`. Der CSV-Parser extrahiert:

- Zeitstempel
- Filter-Token, zum Beispiel `[CSV_TEMP]`
- Nutzdatenfelder

Wenn `filter_string` passt und die Feldanzahl mit der Konfiguration übereinstimmt, wird die Zeile zu einem `VisualizerSample` und im zugehörigen Visualizer-Fenster gepuffert.

## 6. GUI-Überblick

Das Hauptfenster enthält:

- Obere Aktionsleiste
  `SAVE`, `CLEAR`, `COPY`, `CONNECT`, `PAUSE`, `Auto-Scroll`, `Timestamp`
- Verbindungsparameter
  Bind-IP, UDP-Port, Max-Lines
- Filter-Bereich
  Hinzufügen, Bearbeiten, Entfernen und Zurücksetzen von Filter-Slots
- Exclude-Bereich
  Hinzufügen, Bearbeiten, Entfernen und Zurücksetzen von Exclude-Slots
- Highlight-Bereich
  Hinzufügen, Bearbeiten, Entfernen und Zurücksetzen von Highlight-Slots
- Haupt-Logansicht
- Statusleiste

Menüstruktur:

- `File`
  `Open Log…`, `Replay Sample`, `Stop Replay`, `Save…`, `Quit`
- `Tools`
  Simulation für Text-, Temperatur- und Logic-Daten
- `Visualize`
  Temperature Config/Show sowie Logic Config/Show

## 7. Konfiguration und Persistenz

### 7.1 `QSettings`

`QSettings` wird für kleine UI-bezogene Werte genutzt, zum Beispiel:

- Bind-IP
- Port
- Auto-Scroll
- Timestamp-Option
- Max-Lines
- vermutlich auch ältere Formen der Regel-Persistenz

### 7.2 `config.ini`

`config.ini` wird im App-Support-Verzeichnis erzeugt und speichert:

- Versionswerte für App und General
- Überschreibung des Log-Pfads
- JSON-Daten für Regel-Slots
- Visualizer-Konfigurationen

Plattformspezifische Basisverzeichnisse:

- macOS:
  `~/Library/Application Support/<ORG>/<APP>/`
- Windows:
  `%APPDATA%\<ORG>\<APP>\`
- Linux:
  `~/.local/share/<ORG>/<APP>/`

Das Standard-Logverzeichnis ist `<app_support_dir>/logs`.

### 7.3 Visualizer-Konfigurationen

`ConfigStore` speichert bis zu 5 Visualizer-Konfigurationen in Abschnitten:

- `visualizer_1`
- `visualizer_2`
- `visualizer_3`
- `visualizer_4`
- `visualizer_5`

Gespeichert werden unter anderem:

- Aktiv-Flag
- Titel
- `filter_string`
- `graph_type`
- Maximalzahl an Samples
- Achsenbeschriftungen und Achsenbereiche
- Feldname, Skalierung, Aktiv-/Plot-Status, Zielachse, Stil, Farbe, Einheit pro Feld

## 8. Logging-Verhalten

Wenn ein Listener gestartet wird:

- wird eine neue Live-Logdatei im Logverzeichnis angelegt
- können eingehende Zeilen in diese Datei geschrieben werden
- wird der Dateiname in der Statusleiste angezeigt

Wichtige Eigenschaften:

- das Pausieren der UI stoppt nicht zwingend das Dateilogging
- beim Speichern wird bevorzugt die Live- oder letzte Session-Datei kopiert
- falls keine zugrunde liegende Logdatei existiert, fällt das Speichern auf den sichtbaren Textpuffer zurück

Typische Dateinamen:

- `udp_live_YYYYMMDD_HHMMSS.txt`
- `udp_log_YYYYMMDD_HHMMSS.txt`

## 9. Replay und Simulation

### 9.1 Replay

Replay öffnet eine vorhandene Textdatei und speist deren Zeilen erneut in dieselbe interne Verarbeitung ein, die auch für Live-Daten verwendet wird.

Aktuelles Verhalten:

- leere Zeilen werden ignoriert
- Zeilen mit führendem `#` werden ignoriert
- Zeilen werden in kleinen, zeitgesteuerten Batches injiziert

### 9.2 Integrierte Textsimulation

Die Textsimulation erzeugt synthetische Status-, Info-, Debug-, Warn- und Fehlermeldungen, die typische Embedded-Firmware-Logs abbilden.

### 9.3 Temperatursimulation

Die Temperatursimulation erzeugt `[CSV_TEMP]`-Zeilen mit einem Modell, bei dem sich die Hotspot-Temperatur schneller ändert als die Kammer-Temperatur.

### 9.4 Logic-Simulation

Die Logic-Simulation erzeugt `[CSV_LOGIC]`-Zeilen mit acht binären Kanälen, die zufällig toggeln.

## 10. Data-Visualizer-Subsystem

Das Visualizer-Subsystem liegt in `src/udp_log_viewer/data_visualizer/`.

### 10.1 Zentrale Klassen

- `VisualizerManager`
  Besitzt Parser, Config-Store, Fenster, Routing und Konfigurationsdialoge
- `CsvLogParser`
  Wandelt Textzeilen in strukturierte Samples um
- `VisualizerConfig`
  Gesamtkonfiguration eines Visualizers
- `VisualizerFieldConfig`
  Plot-Metadaten pro Feld
- `VisualizerAxisConfig`
  Labels, Wertebereiche und Modus einer Achse
- `VisualizerWindow`
  Standardfenster für Linien- und Step-Plots
- `LogicVisualizerWindow`
  Fenster für 8-kanalige Logic-Darstellung

### 10.2 Unterstützte CSV-Eingabevarianten

Der Parser toleriert mehrere Eingabeformen, zum Beispiel:

- `20260323-22:32:19.277;[CSV_TEMP];...`
- `20260323-22:32:19.403 ; [CSV_TEMP] ; ...`
- `20260323-22:32:19.528 [CSV_TEMP];...`
- `[CSV_TEMP];...`

### 10.3 Plot-Visualizer

Der Standard-Visualizer unterstützt:

- fortlaufende Sample-Pufferung
- optionales X-Achsen-Fenster
- zwei Y-Achsen (`Y1`, `Y2`)
- Linien- oder Step-Darstellung pro Feld
- konfigurierbare Farbe und Linienstil
- automatisches Redraw oder Freeze-Modus
- Screenshot-Export nach PNG

### 10.4 Logic-Visualizer

Der Logic-Visualizer ist für binäre oder schwellwertbasierte Kanäle optimiert:

- bis zu 8 Kanäle
- vertikal getrennte Step-Traces
- Kanalnamen auf der Y-Achse
- Cursor-Linie bei Mausbewegung
- Screenshot-Export nach PNG

### 10.5 Standardprofile

Im Code sind zwei wichtige Standardprofile hinterlegt:

- `CSV_TEMP Graph`
  für `[CSV_TEMP]`
- `Logic Graph`
  für `[CSV_LOGIC]`

Das Temperaturprofil enthält vordefinierte Felder wie:

- `Thot`
- `Tch`
- `heater_on`
- `door_open`
- `state`

## 11. Entwicklungsworkflow

### 11.1 Installation

Empfohlene Source-Installation:

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

Alternativ über das Bootstrap-Skript:

```bash
./scripts/bootstrap_macos_linux.sh
```

### 11.2 Starten

Vorhandene Startvarianten:

```bash
udp-log-viewer
```

```bash
python run.py
```

```bash
python run_udp_log_viewer.py
```

### 11.3 Tests

Im Repository befinden sich Mischformen aus:

- Visualizer-Smoke-Tests
- Parser-Robustheitstests
- GUI-orientierten manuellen Tests

Wichtiger Ist-Zustand:

- `pytest -q` schlägt derzeit bereits während der Test-Collection fehl
- Ursache: Das `src`-Layout ist in der aktuellen Testausführung nicht auf dem Importpfad
- Typischer Fehler: `ModuleNotFoundError: No module named 'udp_log_viewer'`

Das bedeutet: Testdateien existieren, die Testinfrastruktur ist aber noch nicht so verdrahtet, dass sie im aktuellen Repository-Stand direkt lauffähig ist.

## 12. Packaging

Das Projekt enthält Packaging-Unterstützung für:

- macOS
- Windows

Relevante Dateien:

- `freeze_setup.py`
- `freeze_setup_win.py`
- `freeze_entry.py`
- `packaging/macos/*`
- `packaging/windows/*`

Für Frozen Builds wird `cx_Freeze` verwendet, wobei das Paket `udp_log_viewer` aus dem `src`-Layout eingebunden wird.

## 13. Bekannte Inkonsistenzen und aktuelle Risiken

Während der Analyse sind folgende Inkonsistenzen aufgefallen:

- Versionskonflikte
  `pyproject.toml` verwendet `0.2.0`, `main.py` verwendet `0.15.0 (T3.6.2)`, die Freeze-Skripte verwenden `0.14.0`
- Veraltete Dokumentation
  die vorhandenen Root-README-Dateien decken den aktuellen Feature-Umfang nicht mehr vollständig ab
- Abweichung in der Testausführung
  `scripts/dev_test.sh` aktiviert derzeit nur das virtuelle Environment, startet aber keine Tests
- Drift zwischen Packaging und Doku
  mehrere Dateien deuten auf unterschiedliche historische Release-Stände hin
- Ein Teil der Tests ist eher als ausführbares Smoke-Skript als als strenger automatisierter Test aufgebaut

Diese Punkte verhindern das Verständnis der Codebasis nicht, sollten aber als Wartungsschulden betrachtet werden.

## 14. Praktische Nutzung

Typischer Benutzerablauf:

1. Anwendung starten
2. Bind-IP und Port konfigurieren
3. `CONNECT` klicken
4. Eingehende Logs in Echtzeit beobachten
5. Filter-, Exclude- oder Highlight-Regeln anlegen
6. Optional Visualizer-Fenster für strukturierte CSV-Telemetrie öffnen
7. Logs bei Bedarf speichern oder kopieren
8. Verbindung trennen und Session-Log sichern

Typischer Entwicklerablauf:

1. Virtuelles Environment bootstrappen
2. Projekt im Editable-Modus mit Dev-Abhängigkeiten installieren
3. Anwendung aus dem Quellcode starten
4. Replay- und Simulationsfunktionen für lokale Tests nutzen
5. Vor verlässlichen `pytest`-Runs zuerst das Importpfadproblem des `src`-Layouts beheben

## 15. Empfohlene nächste Schritte

Sinnvolle nächste Verbesserungen im Repository:

- Versionierung an einer zentralen Stelle vereinheitlichen
- Smoke-Skripte in echte `pytest`-Tests mit Assertions überführen
- `pytest` ohne manuelle `PYTHONPATH`-Anpassungen lauffähig machen
- CSV-Schemas für `[CSV_TEMP]` und `[CSV_LOGIC]` explizit dokumentieren
- Schema von `config.ini` separat dokumentieren
- Screenshots für das Visualizer-Subsystem ergänzen
- Release- und Build-Anleitungen für macOS und Windows zentral dokumentieren

## 16. Weiterführende Referenzen

- [SUPPORTED_CSV_INPUT_FORMATS_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/SUPPORTED_CSV_INPUT_FORMATS_de.md)
- [CONFIGURATION_REFERENCE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/CONFIGURATION_REFERENCE_de.md)

## 17. Dateiverweise

Zentrale Dateien zur weiteren Analyse:

- [main.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/main.py)
- [udp_listener.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/udp_listener.py)
- [highlighter.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/highlighter.py)
- [udp_log_utils.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/udp_log_utils.py)
- [app_paths.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/app_paths.py)
- [visualizer_manager.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/data_visualizer/visualizer_manager.py)
- [csv_log_parser.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/data_visualizer/csv_log_parser.py)
- [config_store.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/data_visualizer/config_store.py)
