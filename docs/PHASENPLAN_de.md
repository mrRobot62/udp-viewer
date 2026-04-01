# Phasenplan UDP Log Viewer

Dieses Dokument dient als feste Referenz für die weitere Entwicklung des Projekts.

Wichtig:
Vor dem Übergang in eine neue Phase wird die nächste Phase jeweils nochmals gemeinsam reflektiert. Erst nach dieser kurzen fachlichen und technischen Einordnung starten die eigentlichen Änderungen.

## Arbeitsregel für Phasenübergänge

Bei jedem Wechsel in die nächste Phase gilt:

1. Ziel der nächsten Phase kurz bestätigen
2. Betroffene Dateien und Risiken benennen
3. Prüfen, ob sich die Priorität seit der letzten Phase verändert hat
4. Erst danach mit Implementierung, Refactoring oder Tests beginnen

## Phase 1: Stabilisierung

Ziel:
Die bestehende Codebasis wieder reproduzierbar testbar und konsistent machen.

Inhalt:

- `pytest` direkt aus dem Repository-Root lauffähig machen
- `src`-Layout für Tests sauber verdrahten
- `scripts/dev_test.sh` so anpassen, dass es wirklich Tests ausführt
- Versionsquelle zentralisieren
- Versionskonflikte zwischen Paket, GUI und Freeze-Skripten beseitigen
- offensichtliche Inkonsistenzen im Replay-/Simulationsbereich bereinigen
- einen kleinen belastbaren automatisierten Testkern schaffen

Abschlusskriterien:

- `pytest -q` läuft erfolgreich
- `scripts/dev_test.sh` läuft erfolgreich
- Versionsangaben kommen aus einer kanonischen Quelle
- Replay-/Temperaturpfade sind technisch konsistent

Status:
Abgeschlossen

## Phase 2: Wartbarkeit

Ziel:
Die zentrale Laufzeitlogik aus dem großen Hauptmodul herauslösen und besser testbar machen.

Inhalt:

- [main.py](../src/udp_log_viewer/main.py) schrittweise aufteilen
- Zuständigkeiten klar trennen:
  - Connection/Listener
  - Replay/Simulation
  - Filter/Exclude/Highlight
  - Settings/Persistenz
  - Visualizer-Integration
- UI-nahe Logik von fachlicher Logik trennen
- bestehende Smoke-Skripte in echte automatisierte Tests überführen
- Testabdeckung für Parser, Regelwerk, Persistenz und Replay ausbauen
- Konfigurationsverantwortung zwischen `QSettings` und `config.ini` klarziehen

Abschlusskriterien:

- `main.py` ist spürbar kleiner und fachlich klarer geschnitten
- zentrale Logik ist besser ohne GUI testbar
- Tests prüfen Verhalten statt nur manuelle Smoke-Abläufe
- Konfigurationsverantwortung ist eindeutig dokumentiert

Status:
Offen

## Phase 3: Produktreife

Ziel:
Die Anwendung in Richtung klar dokumentierter, releasefähiger und erweiterbarer Produktbasis weiterentwickeln.

Inhalt:

- CSV-Verträge für `[CSV_TEMP]` und `[CSV_LOGIC]` formalisieren
- Build- und Packaging-Wege für macOS und Windows praktisch verifizieren
- technische Dokumentation weiter strukturieren:
  - Benutzerhandbuch
  - Entwicklerhandbuch
  - Architektur
  - Konfigurationsreferenz
  - CSV-Protokollreferenz
- interne Event- und Datenpipeline weiter entkoppeln
- Basis für spätere Erweiterungen wie Exportformate oder zusätzliche Visualizer verbessern

Abschlusskriterien:

- CSV-Formate sind explizit dokumentiert
- Packaging ist nachvollziehbar und reproduzierbar
- die Dokumentation ist thematisch gegliedert
- die Architektur ist auf Erweiterbarkeit vorbereitet

Status:
Offen

## Empfohlene Reihenfolge

1. Phase 1 vollständig abschließen und committen
2. Vor Phase 2 nochmals reflektieren
3. Phase 2 vollständig abschließen und committen
4. Vor Phase 3 nochmals reflektieren
5. Phase 3 vollständig abschließen und committen

## Hinweis zur Zusammenarbeit

Für die weitere Zusammenarbeit gilt ausdrücklich:

- Nach spätestens einer abgeschlossenen Phase wird ein Commit vorbereitet
- Vor jeder neuen Phase erfolgt zuerst eine kurze Reflexion
- Erst nach dieser Freigabe gehen wir in Codeänderungen oder Refactorings
