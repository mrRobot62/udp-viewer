# UDP Log Viewer

Cross-platform UDP log viewer for ESP32 and other embedded systems, built with Python and PyQt5.

## Documentation

Complete English documentation:

- [docs/DOCUMENTATION_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOCUMENTATION_en.md)

Complete German documentation:

- [docs/DOKUMENTATION_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOKUMENTATION_de.md)

## Current Scope

The current codebase includes:

- real-time UDP log reception
- filter, exclude, and highlight rules
- live session logging
- replay of saved log files
- built-in simulation for text, temperature, and logic traffic
- CSV-based data visualization
- logic-channel visualization
- macOS and Windows packaging scripts

## Run From Source

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
udp-log-viewer
```

## Developer Bootstrap

```bash
./scripts/bootstrap_macos_linux.sh
```
