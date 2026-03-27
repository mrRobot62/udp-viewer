# UDP Log Viewer

Plattformübergreifender UDP Log Viewer für ESP32 und andere Embedded-Systeme, entwickelt mit Python und PyQt5.

## Dokumentation

Vollständige deutsche Dokumentation:

- [docs/DOKUMENTATION_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOKUMENTATION_de.md)
- [docs/USER_GUIDE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/USER_GUIDE_de.md)

Vollständige englische Dokumentation:

- [docs/DOCUMENTATION_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOCUMENTATION_en.md)

## Screenshots

Screenshot-Assets sollen künftig unter [assets/screenshots](/Users/bernhardklein/workspace/python/udp-viewer/assets/screenshots) liegen. Die folgenden Bilder verwenden aktuell noch die bestehenden GitHub-Asset-Links, bis lokale Dateien versioniert im Repository vorliegen.

### Hauptansicht

<img width="1100" height="785" alt="UDP Log Viewer Hauptansicht" src="https://github.com/user-attachments/assets/1d86de14-ef78-48fb-9b06-0868c29e1b72" />

### Highlighting

<img width="1100" height="785" alt="UDP Log Viewer Highlighting" src="https://github.com/user-attachments/assets/6423b809-f52e-462a-8957-b17a9840f6af" />

### Filter-Anpassung

<img width="232" height="387" alt="UDP Log Viewer Filter-Anpassung" src="https://github.com/user-attachments/assets/56fb3ab1-fdb6-46e6-98d6-4c1e933cd127" />

### Speichern und Laden von Logs

<img width="963" height="213" alt="UDP Log Viewer Speichern und Laden" src="https://github.com/user-attachments/assets/1dd140b2-8a6a-467e-9dd3-c9728ab3d86c" />

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
