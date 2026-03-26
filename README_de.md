# UDP Log Viewer

Plattformübergreifender UDP Log Viewer für ESP32 und andere Embedded-Systeme, entwickelt mit Python und PyQt5.

## Dokumentation

Vollständige deutsche Dokumentation:

- [docs/DOKUMENTATION_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOKUMENTATION_de.md)

Vollständige englische Dokumentation:

- [docs/DOCUMENTATION_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOCUMENTATION_en.md)

## Aktueller Umfang

Die aktuelle Codebasis enthält:

- Echtzeit-UDP-Logempfang
- Filter-, Exclude- und Highlight-Regeln
- Live-Session-Logging
- Replay gespeicherter Logdateien
- integrierte Simulation für Text-, Temperatur- und Logic-Traffic
- CSV-basierte Datenvisualisierung
- Logic-Kanal-Visualisierung
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
