# UDP Log Viewer Documentation

This document describes the current codebase status of `udp-viewer` as
found in the repository on April 1, 2026.

## 1. Purpose

UDP Log Viewer is a desktop application written in Python and PyQt5 for receiving, viewing, filtering, persisting, replaying, and visualizing UDP log traffic. The primary target appears to be ESP32 and similar embedded systems that stream plain-text logs over UDP instead of USB or serial.

The application combines two major use cases:

- Real-time text log monitoring for diagnostics and debugging
- Live plotting of structured CSV-like telemetry embedded in log lines

## 2. Current Feature Set

The current codebase implements the following user-visible functionality:

- UDP listener with configurable bind IP and port
- Real-time plain-text log display in a `QPlainTextEdit`
- Optional timestamp prefixing for displayed lines
- Automatic live session logging to a file while connected
- Manual save of the current or last session log
- Main-window `RESET` for starting a fresh log phase inside the same app
  session
- UI pause/resume while live file logging continues
- Auto-scroll toggle
- Log trimming with configurable maximum line count
- Project dialog with Markdown project description and
  `README_<projectname>.md` output
- Slot-based filter rules
- Slot-based exclude rules
- Slot-based highlight rules with color mapping
- Replay of text log files
- Built-in replay sample for synthetic text logs
- Built-in simulation for generic log traffic
- Built-in simulation for temperature CSV traffic
- Built-in simulation for logic CSV traffic
- CSV-based data visualizer with dual Y axes
- Logic-state visualizer for up to 8 channels
- Runtime `Legend` toggle in plot and logic graph windows
- edge and period measurement inside the logic graph
- keyboard-driven screenshot and save shortcuts
- explicit `TAB` navigation in the main and graph windows
- Screenshot export from visualizer windows
- Config persistence via `QSettings` and `config.ini`
- Cross-platform packaging scripts for macOS and Windows

## 3. Technology Stack

- Python 3.11+
- PyQt5
- Matplotlib for plotting
- `setuptools` build backend
- `pytest`, `ruff`, `mypy`, `pre-commit` listed as development dependencies
- `cx_Freeze` scripts for packaged desktop builds

## 4. Repository Structure

Top-level structure:

- `src/udp_log_viewer/`
  Main application package
- `src/udp_log_viewer/data_visualizer/`
  CSV parser, visualizer configuration, visualizer windows, dialogs, config persistence
- `tests/`
  Smoke tests and manual-style test scripts around the visualizer subsystem
- `scripts/`
  Developer bootstrap and run scripts
- `packaging/`
  Packaging assets for macOS and Windows
- `data/logs/`
  Example or generated log files
- `freeze_setup.py`, `freeze_setup_win.py`, `freeze_entry.py`
  Frozen build entry points and configuration
- `run.py`, `run_udp_log_viewer.py`
  Convenience launchers

Relevant source files:

- `src/udp_log_viewer/main.py`
  Main window, runtime orchestration, user actions, replay, simulation, listener lifecycle
- `src/udp_log_viewer/udp_listener.py`
  Background UDP receive thread
- `src/udp_log_viewer/highlighter.py`
  Highlight rule compilation and syntax highlighter
- `src/udp_log_viewer/udp_log_utils.py`
  Queue draining, pattern compilation, include/exclude matching helpers
- `src/udp_log_viewer/app_paths.py`
  App support directory and `config.ini` handling

## 5. Runtime Architecture

### 5.1 Main runtime flow

The application starts in `udp_log_viewer.main:main()`, creates the `QApplication`, then instantiates `MainWindow`.

`MainWindow` is responsible for:

- creating the GUI
- loading persisted state
- managing the UDP listener thread
- receiving and buffering lines
- applying filter/exclude/highlight logic
- maintaining live session log files
- driving replay and simulation timers
- forwarding structured lines to the visualizer subsystem

### 5.2 UDP receive pipeline

The UDP pipeline is implemented by `UdpListenerThread`:

1. Bind socket to configured IP and port
2. Use non-blocking socket plus `select.select()`
3. Receive datagrams
4. Decode bytes as UTF-8 with replacement for invalid sequences
5. Split datagrams into non-empty lines
6. Emit each line through a Qt signal

Shutdown behavior is explicitly defensive:

- `stop()` sets a stop event and closes the socket
- `EBADF` and related shutdown errors are intentionally ignored during teardown

### 5.3 UI buffering

Incoming lines are not appended directly in large bursts. `MainWindow` stores them in a deque and flushes them on a timer every 50 ms. This reduces GUI churn and allows bounded batch updates.

### 5.4 Filtering model

The application supports 5 slots each for:

- Filter
- Exclude
- Highlight

A slot contains:

- `pattern`
- `mode`: `Substring` or `Regex`
- `color`

Semantics:

- Filter uses AND logic across semicolon-separated tokens inside one slot
- Exclude uses OR logic across semicolon-separated tokens inside one slot
- Highlight matches a single pattern per slot and applies the first matching highlight color

### 5.5 Visualizer routing

The visualizer subsystem processes lines independently from the text log view. Each visualizer config has a `filter_string`. The CSV parser extracts:

- timestamp
- filter token, such as `[CSV_TEMP]`
- value fields

If the `filter_string` matches and the field count matches the configuration, the line becomes a `VisualizerSample` and is appended to the matching visualizer window buffer.

## 6. GUI Overview

The main window contains:

- Top action row
  `SAVE`, `RESET`, `CLEAR`, `COPY`, `CONNECT`, `PAUSE`, `Auto-Scroll`, `Timestamp`
- Connection settings
  bind IP, UDP port, max lines
- Filter area
  add, edit, remove, reset filter slots
- Exclude area
  add, edit, remove, reset exclude slots
- Highlight area
  add, edit, remove, reset highlight slots
- Main log text area
- Status bar

`RESET` disconnects the listener, clears the transient session view and buffers, and immediately prepares a new live log file. An active project context remains unchanged.

Menu structure:

- `File`
  `Open Log…`, `Replay Sample`, `Stop Replay`, `Save…`, `Quit`
- `Tools`
  simulation toggles for text, temperature, and logic data
- `Visualize`
  temperature config/show, logic config/show

## 7. Configuration and Persistence

### 7.1 `QSettings`

`QSettings` is used for small UI-related values such as:

- bind IP
- port
- auto-scroll
- timestamp option
- max lines
- likely some legacy rule persistence

### 7.2 `config.ini`

`config.ini` is created in the application support directory and stores:

- app/general version values
- log path override
- rule slot JSON payloads
- visualizer configuration sections

Platform-specific base directories:

- macOS:
  `~/Library/Application Support/<ORG>/<APP>/`
- Windows:
  `%APPDATA%\<ORG>\<APP>\`
- Linux:
  `~/.local/share/<ORG>/<APP>/`

The default log directory is `<app_support_dir>/logs`.

### 7.3 Visualizer config sections

`ConfigStore` persists visualizer configs in separate plot and logic
sections:

- `plot_visualizer_1` to `plot_visualizer_5`
- `logic_visualizer_1` to `logic_visualizer_5`

Stored values include:

- enabled flag
- title
- `filter_string`
- `graph_type`
- max samples
- default sliding-window state
- default window size
- `footer_status_format`
- axis labels and ranges
- per-field name, scale, active/plot flags, axis, style, color, unit

Global visualizer preferences additionally store:

- window-size presets
- default sliding-window state for plot and logic
- default window size for plot and logic
- footer status presets with name, type (`all`, `plot`, `logic`), and
  format string

## 8. Logging Behavior

When a listener is started:

- a new live log file is created in the logs directory
- incoming lines can be written to that file
- the current file name is shown in the status bar

Important behavior:

- pausing the UI does not necessarily stop file logging
- saving prefers copying the live or last session log file
- if no backing live log exists, saving falls back to the visible text buffer

Log files are named like:

- `udp_live_YYYYMMDD_HHMMSS.txt`
- `udp_log_YYYYMMDD_HHMMSS.txt`

## 9. Replay and Simulation

### 9.1 Replay

Replay supports opening an existing text log file and injecting its lines back into the same internal processing pipeline used for live data.

Current replay behavior:

- ignores empty lines
- ignores lines beginning with `#`
- feeds lines in small timed batches

### 9.2 Built-in text simulation

The text simulator produces synthetic status, info, debug, warning, and error messages representative of embedded firmware logs.

### 9.3 Temperature simulation

The temperature simulator generates `[CSV_TEMP]` lines with thermal behavior intended to mimic a chamber/hotspot model where hotspot temperature changes faster than chamber temperature.

### 9.4 Logic simulation

The logic simulator emits `[CSV_LOGIC]` lines with eight binary channels that toggle randomly.

## 10. Data Visualizer Subsystem

The visualizer subsystem is in `src/udp_log_viewer/data_visualizer/`.

### 10.1 Core classes

- `VisualizerManager`
  Owns parser, config store, windows, routing, and config dialogs
- `CsvLogParser`
  Parses incoming text lines into structured samples
- `VisualizerConfig`
  Overall visualizer definition
- `VisualizerFieldConfig`
  Per-field plotting metadata
- `VisualizerAxisConfig`
  Axis labels, ranges, and mode
- `VisualizerWindow`
  Standard line/step plot window
- `LogicVisualizerWindow`
  8-channel logic plot window

### 10.2 Supported CSV input variants

The parser tolerates multiple line layouts, for example:

- `20260323-22:32:19.277;[CSV_TEMP];...`
- `20260323-22:32:19.403 ; [CSV_TEMP] ; ...`
- `20260323-22:32:19.528 [CSV_TEMP];...`
- `[CSV_TEMP];...`

### 10.3 Plot visualizer

The standard visualizer supports:

- continuous sample buffering
- sliding-window controls in the open graph window
- dual Y axes (`Y1`, `Y2`)
- line or step rendering per field
- configurable color with 16 preset colors or HTML code `#RRGGBB`
- configurable line style
- automatic redraw or frozen mode
- footer status lines with placeholders such as `{samples}`, `{Thot}`,
  `{current:Thot}`, `{mean:Thot}`, `{avg:Thot}`, and `{max:Thot}`
- screenshot export to PNG

The footer parameters `mean`, `avg`, `max`, `current`, and `latest` are
calculated inside the viewer from the currently rendered numeric plot
values. They are not values from the UDP data stream. With an active
sliding window, they refer to the visible window.

### 10.4 Logic visualizer

The logic visualizer is optimized for binary or thresholded channels:

- up to 8 displayed channels
- vertically separated step traces
- channel labels on Y axis
- sliding-window controls in the open graph window
- hover cursor line on the plot
- footer status lines with placeholders such as `{samples}`, `{start}`,
  `{duration}`, and `{ch0}`
- interactive edge and period measurement by mouse click
- screenshot export to PNG

Measurement behavior:

- left click measures to the next edge on the selected channel
- `Shift` + left click measures to the next edge of the same type
- the graph pauses while a measurement is active
- `Space` or `Esc` clear the measurement and restore the previous
  refresh state

### 10.5 Default visualizer profiles

The code provides two important default profiles:

- `CSV_TEMP Graph`
  for `[CSV_TEMP]`
- `Logic Graph`
  for `[CSV_LOGIC]`

The temperature profile includes predefined fields such as:

- `Thot`
- `Tch`
- `heater_on`
- `door_open`
- `state`

## 11. Development Workflow

### 11.1 Install

Recommended source setup:

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

Or via the project bootstrap script:

```bash
./scripts/bootstrap_macos_linux.sh
```

### 11.2 Run

Available launch styles:

```bash
udp-log-viewer
```

```bash
python run.py
```

```bash
python run_udp_log_viewer.py
```

### 11.3 Tests

The repository contains a mix of:

- visualizer smoke tests
- parser robustness scripts
- GUI-oriented manual tests

Important current state:

- focused automated tests can be run from the repository root with
  `pytest`
- visualizer and preference tests cover footer formatting, color
  selection, preset persistence, and dialog behavior
- GUI-heavy behavior still needs focused or manual validation where the
  test relies on Qt window state

Typical focused command:

```bash
pytest -q tests/test_visualizer_footer_status.py tests/test_visualizer_color_selection.py tests/test_core_behavior.py tests/test_preferences_store.py
```

## 12. Packaging

The project contains packaging support for:

- macOS
- Windows

Relevant files:

- `freeze_setup.py`
- `freeze_setup_win.py`
- `freeze_entry.py`
- `packaging/macos/*`
- `packaging/windows/*`

The frozen builds use `cx_Freeze` and package the `udp_log_viewer` package from the `src` layout.

## 13. Known Inconsistencies and Current Risks

During analysis, the following inconsistencies were found:

- Version mismatch
  the historical backup file `src/udp_log_viewer/main.py_1_` still
  contains an old hard-coded version and should not be treated as the
  active application entry point
- Documentation drift
  generated PDF files must be regenerated from the updated Markdown
  sources before a binary release if PDFs are shipped
- Test execution drift
  `scripts/dev_test.sh` currently only activates the virtual environment and does not run `pytest`
- Packaging/docs drift
  parts of the repository suggest multiple historical release states
- Some test files behave more like executable smoke scripts than strict automated assertions

These points do not prevent understanding the codebase, but they should be treated as maintenance debt.

## 14. Practical Usage Summary

Typical user workflow:

1. Launch the application
2. Configure bind IP and port
3. Click `CONNECT`
4. Observe incoming logs in real time
5. Add filter, exclude, or highlight rules as needed
6. Optionally open visualizer windows for structured CSV telemetry
7. Save or copy logs when needed
8. Disconnect and preserve the session log

Typical developer workflow:

1. Bootstrap a virtual environment
2. Install editable project dependencies
3. Run the app from source
4. Use replay and simulation features for local testing
5. Run focused `pytest` suites for the area being changed

## 15. Suggested Next Documentation/Engineering Improvements

Recommended follow-up work for the repository:

- regenerate shipped PDF documentation from the updated Markdown
  sources before a binary release
- replace historical backup files such as `main.py_1_` with archived
  release references or remove them from the source tree
- continue converting smoke-style scripts into strict `pytest` tests
  with assertions
- add updated screenshots for the new visualizer footer preset UI

## 16. File References

Primary files for further inspection:

- [main.py](../src/udp_log_viewer/main.py)
- [udp_listener.py](../src/udp_log_viewer/udp_listener.py)
- [highlighter.py](../src/udp_log_viewer/highlighter.py)
- [udp_log_utils.py](../src/udp_log_viewer/udp_log_utils.py)
- [app_paths.py](../src/udp_log_viewer/app_paths.py)
- [visualizer_manager.py](../src/udp_log_viewer/data_visualizer/visualizer_manager.py)
- [csv_log_parser.py](../src/udp_log_viewer/data_visualizer/csv_log_parser.py)
- [config_store.py](../src/udp_log_viewer/data_visualizer/config_store.py)

## 17. Further References

- [USER_GUIDE_en.md](../docs/USER_GUIDE_en.md)
- [CONFIGURATION_REFERENCE_en.md](../docs/CONFIGURATION_REFERENCE_en.md)
- [SUPPORTED_CSV_INPUT_FORMATS_en.md](../docs/SUPPORTED_CSV_INPUT_FORMATS_en.md)
- [BUILD_AND_PACKAGING_REFERENCE_en.md](../docs/BUILD_AND_PACKAGING_REFERENCE_en.md)
- [RELEASE_0.17.0.md](../docs/RELEASE_0.17.0.md)
- [DOKUMENTATION_de.md](../docs/DOKUMENTATION_de.md)
