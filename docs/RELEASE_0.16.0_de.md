# Release 0.16.0

Release-Datum: 2026-04-01

## Zusammenfassung

Version `0.16.0` finalisiert den neuen `RESET`-Ablauf für frische
Log-Phasen, die interaktive Messung im Logic-Graphen sowie erweiterte
Projekt-, Tastatur- und Dokumentationsfunktionen.

## Highlights

- neuer `RESET`-Button im Hauptfenster für eine neue Log-Phase innerhalb
  derselben App-Session
- aktiver `PROJECT`-Kontext bleibt beim Reset erhalten
- das laufende Live-Log wird sauber abgeschlossen und sofort neu
  vorbereitet
- Projektbeschreibungen werden im `PROJECT`-Dialog als
  `README_<projectname>.md` im Projektordner geschrieben
- Flanken- und Periodenmessung im Logic-Graphen mit Markerlinien und
  Zeitlabel
- `Shift` + Klick misst die nächste gleichartige Flanke als Periode
- aktive Logic-Messung pausiert den Graphen bis `Space` oder `Esc`
- kompakte Messlabels wandern rechts neben den Endmarker, wenn der Platz
  zu klein ist
- `Window Size` ist in Plot- und Logic-Fenstern auf `1..5000` begrenzt
- Laufzeit-Checkbox `Legend` in Plot- und Logic-Fenstern
- explizite `TAB`-Navigation und Save-/Screenshot-Kürzel in Haupt- und
  Graph-Fenstern

## Validierung

Der Release-Stand wurde mit den relevanten automatisierten Tests
geprüft, insbesondere:

- `tests/test_core_behavior.py`
- `tests/test_connection_runtime.py`
- `tests/test_listener_runtime.py`
- `tests/test_project_runtime.py`
- `tests/test_sliding_window_behavior.py`

## Packaging-Stand

- veröffentlichter Release-Tag: `0.16.0`
- die Release-Artefakte werden über die GitHub-Release-Workflows
  erzeugt
- veröffentlichte Artefakte:
  - `UDPLogViewer-0.16.0.dmg`
  - `UDPLogViewer-0.16.0-Setup.exe`
