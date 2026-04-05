# UDP Log Viewer

Plattformübergreifender UDP Log Viewer für ESP32 und andere Embedded-Systeme, entwickelt mit Python und PyQt5.

## Dokumentation

Vollständige deutsche Dokumentation:

- [docs/DOKUMENTATION_de.md](docs/DOKUMENTATION_de.md)
- [docs/USER_GUIDE_de.md](docs/USER_GUIDE_de.md)
- [docs/RELEASE_0.16.2.md](docs/RELEASE_0.16.2.md)

Vollständige englische Dokumentation:

- [docs/DOCUMENTATION_en.md](docs/DOCUMENTATION_en.md)

## MAC users only
after installation this application is not signed and can't be started directly.
You have to set this command: `xattr -dr com.apple.quarantine /Applications/UDPLogViewer.app` 

## Screenshots

Die Screenshot-Assets liegen unter [assets/screenshots](assets/screenshots).

### Hauptansicht

![UDP Log Viewer Hauptansicht mit aktiver Verbindung, Reset-Ablauf und Regel-Chips](assets/screenshots/udp_log_viewer_main_highlighted.png)

### Regel-Konfiguration

![UDP Log Viewer Filter-Dialog über der Hauptansicht](assets/screenshots/udp_log_viewer_main_rule_config.png)

### Projekt-Dialog

![UDP Log Viewer Projekt-Dialog mit Markdown-Projektbeschreibung](assets/screenshots/udp_log_viewer_project_config.png)

### Plot-Visualizer mit Tooltip

![Plot-Visualizer mit Legende, Ziel-Linien und Tooltip-Werten](assets/screenshots/udp_log_viewer_plot_tooltip.png)

### Logic-Messung

![Logic-Visualizer mit Periodenmessung zwischen roter und blauer Markerlinie](assets/screenshots/udp_log_viewer_logic_period.png)

## Aktueller Umfang

Die aktuelle Codebasis enthält:

- Echtzeit-UDP-Logempfang
- Filter-, Exclude- und Highlight-Regeln
- Live-Session-Logging
- `RESET` im Hauptfenster für einen frischen Log-Start innerhalb derselben App-Session
- Projektbeschreibungen als `README_<projectname>.md` direkt im Projektordner
- Replay gespeicherter Logdateien
- integrierte Simulation für Text-, Temperatur- und Logic-Traffic
- CSV-basierte Datenvisualisierung
- Logic-Kanal-Visualisierung
- Flanken- und Periodenmessung direkt im Logic-Graphen
- Legende per Laufzeit-Checkbox in Plot- und Logic-Fenstern ein-/ausblendbar
- explizite `TAB`-Navigation sowie Tastaturkürzel für Save und Screenshot
- Sliding-Window-Steuerung direkt im Graph-Fenster
- Packaging-Skripte für macOS und Windows

## Start aus dem Quellcode

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
udp-log-viewer
```

## Entwickler-Bootstrap

```bash
./scripts/bootstrap_macos_linux.sh
```
