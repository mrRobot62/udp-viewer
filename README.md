# UDP Log Viewer

Cross-platform UDP log viewer for ESP32 and other embedded systems, built with Python and PyQt5.

## Documentation

Complete English documentation:

- [docs/DOCUMENTATION_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOCUMENTATION_en.md)
- [docs/USER_GUIDE_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/USER_GUIDE_en.md)
- [docs/RELEASE_0.16.0.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/RELEASE_0.16.0.md)

Complete German documentation:

- [docs/DOKUMENTATION_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/DOKUMENTATION_de.md)

## MAC users only
after installation this application is not signed and can't be started directly.
You have to set this command: `xattr -dr com.apple.quarantine /Applications/UDPLogViewer.app` 

## Screenshots

Screenshot assets should eventually be stored under [assets/screenshots](/Users/bernhardklein/workspace/python/udp-viewer/assets/screenshots). The images below currently still use the existing GitHub asset URLs until local files are added to the repository.

### Main Screen

<img width="1100" height="785" alt="UDP Log Viewer main screen" src="https://github.com/user-attachments/assets/1d86de14-ef78-48fb-9b06-0868c29e1b72" />

### Highlighting

<img width="1100" height="785" alt="UDP Log Viewer highlighting" src="https://github.com/user-attachments/assets/6423b809-f52e-462a-8957-b17a9840f6af" />

### Filter Adjustment

<img width="232" height="387" alt="UDP Log Viewer filter adjustment" src="https://github.com/user-attachments/assets/56fb3ab1-fdb6-46e6-98d6-4c1e933cd127" />

### Saving and Loading Logs

<img width="963" height="213" alt="UDP Log Viewer save and load dialog" src="https://github.com/user-attachments/assets/1dd140b2-8a6a-467e-9dd3-c9728ab3d86c" />

## Current Scope

The current codebase includes:

- real-time UDP log reception
- filter, exclude, and highlight rules
- live session logging
- main-window `RESET` support to start a fresh log phase inside the same app session
- runtime project contexts for grouping logs and screenshots per test session
- project descriptions stored as `README_<projectname>.md` inside the project folder
- replay of saved log files
- built-in simulation for text, temperature, and logic traffic
- CSV-based data visualization
- logic-channel visualization
- edge and period measurement directly inside the logic graph
- runtime `Legend` toggle in plot and logic graph windows
- keyboard-driven screenshot/save shortcuts and explicit `TAB` navigation in the main and graph windows
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
