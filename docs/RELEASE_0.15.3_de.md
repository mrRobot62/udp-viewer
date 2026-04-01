# Release 0.15.3

Release-Datum: 2026-03-31

## Zusammenfassung

Version `0.15.3` konzentrierte sich auf Fehlerbehebungen und
Bedienverbesserungen rund um Plot- und Logic-Visualisierung,
Logdatei-Handhabung, projektbezogene Artefaktablage und
Visualizer-Konfiguration.

## Highlights

- bessere Darstellung aktueller Werte in Plot-Fenstern
- mehrzeilige Plot-Tooltips
- Hover-Unterstützung mit Hilfslinie im Plot
- konfigurierbarer Standard-Logpfad über `Preferences > Log Path`
- projektbezogener Laufzeitmodus mit Root-Folder und automatischer
  Projekt-Unterordner-Erzeugung
- verfeinerter `PROJECT`-Dialog für längere Namen und Pfade
- klareres Reporting für Live-Log und Speicherpfad
- `APPLY` in Plot- und Logic-Konfigurationsdialogen
- robustere Slot-Wechselbehandlung bei echten Änderungen
- Umbenennung von `Temperature` zu `Plot` in der Plot-UI
- korrigierte Host-Plot-Simulation mit `target_min` und `target_max`

## Packaging

- macOS-Artefakt: DMG via `./build_dmg.sh`
- Windows-Artefakt: Setup EXE via GitHub-Release-Workflow
