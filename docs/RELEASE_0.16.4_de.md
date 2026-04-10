# Release 0.16.4

Release-Datum: 2026-04-10

## Zusammenfassung

Version `0.16.4` erweitert die Visualizer-Konfiguration deutlich. Im
Fokus stehen bessere Farbauswahl, kompakte frei definierbare
Footer-Statuszeilen und zentral gepflegte Footer-Presets.

## Highlights

- Plot- und Logic-Visualizer bieten jetzt 16 gut unterscheidbare
  Preset-Farben
- jede Visualizer-Farbe kann alternativ als HTML-Farbcode `#RRGGBB`
  eingegeben werden
- zentrale Footer-Presets werden unter `Preferences` -> `Visualizer`
  gepflegt
- Footer-Presets besitzen Name, Typ (`All`, `Plot`, `Logic`) und
  Formatstring
- Preset-Namen sind auf 12 Zeichen begrenzt, damit Dropdowns lesbar
  bleiben
- Plot- und Logic-Slot-Dialoge bieten ein Preset-Dropdown und ein
  eigenes `Footer Format`
- Footer-Statuszeilen werden auf eine kompakte zweizeilige Anzeige
  begrenzt, damit lange Statuszeilen das Graph-Fenster nicht mehr
  verbreitern

## Footer-Platzhalter

Globale Platzhalter für Plot und Logic:

- `{samples}`
  Anzahl aller Samples im Slot-Puffer
- `{start}`
  Zeitstempel des ersten Samples
- `{end}`
  Zeitstempel des letzten Samples
- `{duration}`
  Dauer zwischen erstem und letztem Sample

Interne Plot-Platzhalter:

- `{Feldname}`
  aktueller Wert des Feldes
- `{current:Feldname}`
  aktueller Wert des Feldes
- `{latest:Feldname}`
  Alias für `current`
- `{mean:Feldname}`
  Mittelwert der aktuell gerenderten numerischen Plot-Werte
- `{avg:Feldname}`
  Alias für `mean`
- `{max:Feldname}`
  Maximalwert der aktuell gerenderten numerischen Plot-Werte

`mean`, `avg`, `max`, `current` und `latest` sind keine Werte aus dem
UDP-Datenstrom. Sie werden innerhalb des UDP-Viewers aus den aktuell
gerenderten numerischen Plot-Daten berechnet. Bei aktivem Sliding
Window beziehen sie sich auf das sichtbare Datenfenster.

Logic-Platzhalter:

- `{ch0}`, `{ch1}`, ...
  letzter Zustand des jeweiligen Logic-Kanals

## Formatierung

Footer-Platzhalter unterstützen Python-ähnliche Formatangaben:

- `{samples:04d}`
  Integer mit führenden Nullen, z. B. `0007`
- `{Thot:.1f}`
  Fließkommazahl mit einer Nachkommastelle
- `{Thot:05.1f}`
  Mindestbreite 5 inklusive Dezimalpunkt, z. B. `072.3`
- `{mean:Thot:05.1f}`
  formatierter Mittelwert
- `{avg:Thot:05.1f}`
  formatierter Mittelwert über den Alias `avg`
- `{max:Thot:05.1f}`
  formatierter Maximalwert
- `{current:Thot:05.1f}`
  formatierter aktueller Wert
- `{ch0:02.0f}`
  formatierter Logic-Wert

Hinweis: Die Breite in Python-Formatangaben ist die gesamte
Mindestbreite inklusive Dezimalpunkt und Nachkommastellen. Für
`3 Vorkommastellen + 1 Nachkommastelle` ist bei positiven Zahlen meist
`05.1f` passend.

## Validierung

Der Release-Stand wurde mit fokussierten automatisierten Tests und
einem Compile-Check validiert:

- `tests/test_visualizer_footer_status.py`
- `tests/test_visualizer_color_selection.py`
- `tests/test_core_behavior.py`
- `tests/test_preferences_store.py`
- `python -m compileall src/udp_log_viewer`

## Zugehörige Dateien

- [CHANGELOG.md](../CHANGELOG.md)
- [README_de.md](../README_de.md)
- [USER_GUIDE_de.md](../docs/USER_GUIDE_de.md)
- [CONFIGURATION_REFERENCE_de.md](../docs/CONFIGURATION_REFERENCE_de.md)
- [SUPPORTED_CSV_INPUT_FORMATS_de.md](../docs/SUPPORTED_CSV_INPUT_FORMATS_de.md)
- [RELEASE_0.16.4.md](../docs/RELEASE_0.16.4.md)
