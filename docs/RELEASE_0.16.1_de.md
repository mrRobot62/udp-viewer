# Release 0.16.1

Release-Datum: 2026-04-01

## Zusammenfassung

Version `0.16.1` ist ein gezieltes Wartungsrelease fuer den
Projekt-Workflow und den Regel-Editor im Hauptfenster.

## Highlights

- die Projekterstellung behandelt Dateisystem- und Berechtigungsfehler
  nun kontrolliert, statt bei nicht beschreibbaren Zielordnern
  abzustuerzen
- die `PROJECT`-Aktion zeigt einen klaren Fehlerdialog, wenn
  Projektordner oder README nicht angelegt werden koennen
- die Farbauswahl wurde fuer `Filter` und `Exclude` im Hauptfenster
  entfernt, weil diese Regeltypen keine Farbbedeutung haben
- alte gespeicherte Farben fuer `Filter` und `Exclude` werden beim
  Laden und Speichern auf `None` normalisiert, damit Einstellungen und
  Chip-Anzeige konsistent bleiben

## Validierung

Der Release-Stand wurde mit den relevanten automatisierten Tests
geprueft, insbesondere:

- `tests/test_core_behavior.py`
- `tests/test_phase2_refactor.py`
- `tests/test_project_runtime.py`
- `tests/test_settings_store.py`

## Zugehoerige Dateien

- [README.md](../README.md)
- [README_de.md](../README_de.md)
- [RELEASE_0.16.1.md](../docs/RELEASE_0.16.1.md)
