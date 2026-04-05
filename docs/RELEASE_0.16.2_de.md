# Release 0.16.2

Release-Datum: 2026-04-05

## Zusammenfassung

Version `0.16.2` ist ein Bugfix- und Usability-Release fuer
Projektbehandlung, Exit-/Save-Verhalten, Visualizer-Tooltips und
Statusinformationen in den Graph-Fenstern.

## Highlights

- das Speichern des `PROJECT`-Dialogs schliesst bereits geoeffnete
  Visualizer-Fenster nicht mehr
- `RESET` setzt den aktiven Projektkontext auf den Default-Zustand
  zurueck, und der `PROJECT`-Dialog besitzt dafuer zusaetzlich einen
  eigenen `NEW`-Button
- beim Beenden waehrend aktiver Verbindung und bereits empfangener
  Daten erscheint jetzt ein Dialog mit `Save…`, `No` und `Cancel`
- relevante Dialoge und Graph-Bedienelemente besitzen jetzt klarere
  Tooltips, inklusive korrigierter dynamischer `Window Size`-Tooltips
- Plot- und Logic-Fenster zeigen nun eine Footer-Statuszeile mit Start
  und Dauer der Session
- Plot-Fenster koennen kompakte `MAX/Mean/Current`-Statistiken fuer
  ausgewaehlte `Line`-Serien anzeigen; gesteuert wird das ueber die neue
  Spalte `Statistic` im Plot-Konfigurationsdialog

## Validierung

Der Release-Stand wurde mit den fokussierten automatisierten Tests fuer
Exit-Save-Logik, Projekt-Reset, Tooltip-Helfer, Footer-Statusanzeige,
Statistik-Persistenz und Fensterverhalten geprueft, insbesondere:

- `tests/test_main_exit_save.py`
- `tests/test_main_project_reset.py`
- `tests/test_project_dialog.py`
- `tests/test_visualizer_footer_status.py`
- `tests/test_visualizer_statistics_flag.py`
- `tests/test_visualizer_manager_close.py`
- `tests/test_window_size_tooltip.py`

## Zugehoerige Dateien

- [CHANGELOG.md](../CHANGELOG.md)
- [USER_GUIDE_en.md](../docs/USER_GUIDE_en.md)
- [USER_GUIDE_de.md](../docs/USER_GUIDE_de.md)
- [RELEASE_0.16.2.md](../docs/RELEASE_0.16.2.md)
