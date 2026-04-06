# Release 0.16.3

Release-Datum: 2026-04-06

## Zusammenfassung

Version `0.16.3` ist ein fokussiertes Bugfix-Release fuer Exit-/Save-
Verhalten nach getrennten Sessions, robusteren Listener-Shutdown und
konsistente Release-Dokumentation.

## Highlights

- der Exit-Save-Dialog erscheint jetzt immer dann, wenn die aktuelle
  Session bereits Logdaten enthaelt, auch wenn der UDP-Listener bereits
  gestoppt wurde oder die Daten nur noch in der gespeicherten Live-
  Session-Datei vorliegen
- der Listener-Shutdown versucht bei einem fehlgeschlagenen ersten
  Warten automatisch einen zweiten, laengeren Timeout
- englische und deutsche README-Dateien verweisen jetzt auf die
  aktuellen Release-Notizen und beschreiben das Demo-Projekt klarer
- die mitgelieferten `README.pdf` und `README_de.pdf` wurden fuer den
  Release-Stand `0.16.3` neu erzeugt

## Validierung

Der Release-Stand wurde mit den fokussierten automatisierten Tests fuer
Exit-Save-Verhalten und Listener-Shutdown geprueft, insbesondere:

- `tests/test_main_exit_save.py`
- `tests/test_listener_runtime.py`

## Zugehoerige Dateien

- [CHANGELOG.md](../CHANGELOG.md)
- [README.md](../README.md)
- [README_de.md](../README_de.md)
- [RELEASE_0.16.3.md](../docs/RELEASE_0.16.3.md)
