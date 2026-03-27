# Konfigurationsreferenz des UDP-Viewers

Dieses Dokument beschreibt die Konfigurations- und Persistenzmechanismen des UDP-Viewers.

## 1. Überblick

Der UDP-Viewer verwendet derzeit zwei Persistenzebenen:

- `QSettings`
- `config.ini`

Zusätzlich werden Log- und Screenshot-Dateien im Dateisystem abgelegt.

## 2. `QSettings`

`QSettings` wird für kleine, häufig geänderte Anwendungszustände verwendet.

Aktuell relevante Schlüssel:

- `net/bind_ip`
- `net/port`
- `ui/autoscroll`
- `ui/timestamp`
- `log/max_lines`
- `config/selected_path`
- `filter/slots_json`
- `exclude/slots_json`
- `hl/slots_json`

Nicht mehr führend in `QSettings`:

- globale App-Präferenzen wie Visualizer-Presets oder Sprachvorgaben

Diese werden jetzt in `config.ini` gespeichert.

## 3. Bedeutung der `QSettings`-Schlüssel

### Netzwerk

- `net/bind_ip`
  gespeicherte Bind-IP für den UDP-Listener
- `net/port`
  gespeicherter UDP-Port

### UI

- `ui/autoscroll`
  merkt den Auto-Scroll-Status
- `ui/timestamp`
  merkt den Timestamp-Status
- `log/max_lines`
  maximale Anzahl sichtbarer Zeilen in der Hauptansicht

### Konfigurationspfad

- `config/selected_path`
  merkt den zuletzt verwendeten Pfad zur `config.ini`

### Regel-Slots

- `filter/slots_json`
- `exclude/slots_json`
- `hl/slots_json`

Diese Schlüssel enthalten JSON-Repräsentationen der Slot-Regeln und dienen derzeit auch als Fallback, wenn `config.ini` nicht lesbar oder nicht schreibbar ist.

## 4. `config.ini`

Die `config.ini` speichert vor allem:

- App-/Versionsinformationen
- globale Präferenzen
- Pfadkonfiguration
- Rule-Slots
- Visualizer-Konfigurationen

Typische Abschnitte:

- `[app]`
- `[general]`
- `[preferences]`
- `[paths]`
- `[rules]`
- `[visualizer_1]` bis `[visualizer_5]`

## 5. Standardpfad der `config.ini`

Wenn kein benutzerdefinierter Pfad gewählt wurde, verwendet der Viewer standardmäßig:

- macOS:
  `~/Library/Application Support/<ORG>/<APP>/config.ini`
- Windows:
  `%APPDATA%\<ORG>\<APP>\config.ini`
- Linux:
  `~/.local/share/<ORG>/<APP>/config.ini`

## 6. Verhalten bei fehlender `config.ini`

Wenn keine geeignete `config.ini` gefunden wird:

1. der Viewer prüft einen gemerkten Pfad aus `QSettings`
2. danach den Standardpfad
3. ist keine verwendbare Datei vorhanden, fragt die App nach einem Ort
4. an diesem Ort kann eine neue `config.ini` angelegt oder eine bestehende gewählt werden
5. der gewählte Pfad wird anschließend in `config/selected_path` gemerkt

## 7. Abschnitt `[paths]`

Aktuell wichtig:

- `logs_dir`
  bestimmt das Verzeichnis für Live-Logs

Wenn kein Wert vorhanden ist, verwendet die App standardmäßig:

`<config_dir>/logs`

## 8. Abschnitt `[preferences]`

Der Abschnitt `[preferences]` enthält globale App-Defaults.

Aktuell relevante Schlüssel:

- `language`
- `autoscroll_default`
- `timestamp_default`
- `max_lines_default`
- `visualizer_presets`
- `plot_sliding_window_default`
- `plot_window_size_default`
- `logic_sliding_window_default`
- `logic_window_size_default`

Beispiel:

```ini
[preferences]
language = de
autoscroll_default = true
timestamp_default = true
max_lines_default = 20000
visualizer_presets = 100,150,200,300
plot_sliding_window_default = true
plot_window_size_default = 200
logic_sliding_window_default = true
logic_window_size_default = 150
```

## 9. Abschnitt `[rules]`

Der Abschnitt `[rules]` enthält:

- `filter_slots_json`
- `exclude_slots_json`
- `hl_slots_json`

Diese Werte sind JSON-Listen mit bis zu 5 Slot-Einträgen.

Jeder Slot enthält:

- `pattern`
- `mode`
- `color`

Beispielstruktur:

```json
[
  {
    "pattern": "OVEN",
    "mode": "Substring",
    "color": "Green"
  }
]
```

## 10. Visualizer-Abschnitte

Die Visualizer-Konfigurationen werden in Abschnitten gespeichert:

- `visualizer_1`
- `visualizer_2`
- `visualizer_3`
- `visualizer_4`
- `visualizer_5`

Typische Schlüssel:

- `enabled`
- `title`
- `filter_string`
- `graph_type`
- `max_samples`
- `sliding_window_enabled`
- `default_window_size`
- `window_geometry`
- `x_label`
- `x_continuous`
- `x_min`
- `x_max`
- `y1_label`
- `y1_logarithmic`
- `y1_min`
- `y1_max`
- `y2_label`
- `y2_logarithmic`
- `y2_min`
- `y2_max`
- `field_count`

Zusätzlich pro Feld:

- `field_<n>_name`
- `field_<n>_active`
- `field_<n>_numeric`
- `field_<n>_scale`
- `field_<n>_plot`
- `field_<n>_axis`
- `field_<n>_render_style`
- `field_<n>_color`
- `field_<n>_line_style`
- `field_<n>_unit`

## 11. Live-Logs

Beim Start einer Listener-Session erzeugt die App standardmäßig eine Live-Logdatei im `logs_dir`.

Namensformat:

```text
udp_live_YYYYMMDD_HHMMSS.txt
```

Beim Speichern einer Session wird bevorzugt diese Datei kopiert. Falls keine passende Live-Datei verfügbar ist, fällt die App auf den sichtbaren Textinhalt zurück.

## 12. Screenshots

Visualizer-Screenshots werden standardmäßig unterhalb des Log-Verzeichnisses verwendet:

```text
<logs_dir>/screenshots
```

Zusätzlich merken sich die Visualizer-Fenster den zuletzt genutzten Screenshot-Ordner in `QSettings`.

## 13. Schreibstrategie

Der Viewer verwendet derzeit folgende Strategie:

- UI-State wird in `QSettings` gespeichert
- globale Präferenzen werden in `config.ini` gespeichert
- Rule-Slots werden zuerst in `QSettings` gespeichert
- anschließend wird versucht, dieselben Slots auch in `config.ini` zu schreiben
- wenn `config.ini` nicht schreibbar ist, bleibt `QSettings` der Fallback

Diese Reihenfolge wurde bewusst gewählt, damit Filter-/Highlight-Regeln auch bei problematischen Dateipfaden erhalten bleiben.

## 14. Praktische Auswirkungen

Wichtig für den Betrieb:

- eine nicht schreibbare `config.ini` verhindert nicht mehr automatisch die Persistenz von Rule-Slots
- globale Präferenzen wie Visualizer-Presets und App-Defaults liegen ebenfalls in `config.ini`
- der Config-Pfad ist Teil des gemerkten Anwendungszustands
- ein Wechsel des Speicherorts kann das sichtbare Konfigurationsverhalten verändern, wenn an einem anderen Ort eine andere `config.ini` liegt

## 15. Relevante Quelldateien

- [settings_store.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/settings_store.py)
- [preferences.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/preferences.py)
- [preferences_dialog.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/preferences_dialog.py)
- [config_runtime.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/config_runtime.py)
- [app_paths.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/app_paths.py)
- [config_store.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/data_visualizer/config_store.py)
- [main.py](/Users/bernhardklein/workspace/python/udp-viewer/src/udp_log_viewer/main.py)
