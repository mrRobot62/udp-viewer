# UDP Log Viewer

Cross-platform UDP log viewer for ESP32 and other embedded systems, built with Python and PyQt5.

## Why using this tool?

Debugging embedded devices over UDP is painful.
This tool makes it simple and visual. Not only viewing data, visualizing data as well.

## Documentation

Complete English documentation:

- [docs/DOCUMENTATION_en.md](docs/DOCUMENTATION_en.md)
- [docs/USER_GUIDE_en.md](docs/USER_GUIDE_en.md)
- [docs/RELEASE_0.16.2.md](docs/RELEASE_0.16.2.md)

Complete German documentation:

- [docs/DOKUMENTATION_de.md](docs/DOKUMENTATION_de.md)

## Windows-User
please use setup.exe to install this viewer

## ToDo for MAC users
after installation this application is not signed and can't be started directly.
You have to set this command: `xattr -dr com.apple.quarantine /Applications/UDPLogViewer.app` 

## Screenshots

Screenshot assets are stored under [assets/screenshots](assets/screenshots).

### Main Screen

![UDP Log Viewer main screen with active connection, reset workflow, and rule chips](assets/screenshots/udp_log_viewer_main_highlighted.png)

### Rule Configuration

![UDP Log Viewer filter-rule dialog on top of the main window](assets/screenshots/udp_log_viewer_main_rule_config.png)

### Project Dialog

![UDP Log Viewer project dialog with Markdown project description](assets/screenshots/udp_log_viewer_project_config.png)

### Plot Visualizer Tooltip

![Plot visualizer with legend, target lines, and tooltip values](assets/screenshots/udp_log_viewer_plot_tooltip.png)

### Logic Measurement

**Measuring HIGH/LOW phase**
![Logic visualizer signal measurement with red and blue markers](assets/screenshots/udp_log_viewer_logic_signal.png)

**Measuring signal period**
![Logic visualizer period measurement with red and blue markers](assets/screenshots/udp_log_viewer_logic_period.png)

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
# You like it?
⭐ If you like this project, consider giving it a star!
