# UDP Viewer Configuration Reference

This document describes the current configuration and persistence
mechanisms used by UDP Viewer.

## 1. Overview

The application currently uses two persistence layers:

- `QSettings`
- `config.ini`

In addition, log files, screenshots, and project files are written to
the filesystem.

## 2. `QSettings`

`QSettings` is used for small and frequently changing UI state.

Currently relevant keys:

- `net/bind_ip`
- `net/port`
- `ui/autoscroll`
- `ui/timestamp`
- `log/max_lines`
- `config/selected_path`
- `filter/slots_json`
- `exclude/slots_json`
- `hl/slots_json`

Global app preferences such as visualizer presets and language defaults
now primarily live in `config.ini`.

## 3. `config.ini`

The `config.ini` stores:

- app and version information
- global preferences
- path configuration
- rule slots
- visualizer configurations

Typical sections:

- `[app]`
- `[general]`
- `[preferences]`
- `[paths]`
- `[rules]`
- `[plot_visualizer_1]` to `[plot_visualizer_5]`
- `[logic_visualizer_1]` to `[logic_visualizer_5]`

## 4. Default `config.ini` location

If the user has not chosen a custom config path, the application uses a
platform-specific default:

- macOS:
  `~/Library/Application Support/<ORG>/<APP>/config.ini`
- Windows:
  `%APPDATA%\<ORG>\<APP>\config.ini`
- Linux:
  `~/.local/share/<ORG>/<APP>/config.ini`

## 5. Behavior When `config.ini` Is Missing

Current lookup order:

1. last remembered path from `QSettings`
2. platform default path
3. if neither is usable, the app asks the user for a path

The selected path is then stored as `config/selected_path`.

## 6. `[paths]`

Currently important key:

- `logs_dir`

If it is missing, the application falls back to:

```text
<config_dir>/logs
```

## 7. `[preferences]`

The `[preferences]` section contains global defaults.

Currently relevant keys:

- `language`
- `autoscroll_default`
- `timestamp_default`
- `max_lines_default`
- `visualizer_presets`
- `plot_sliding_window_default`
- `plot_window_size_default`
- `logic_sliding_window_default`
- `logic_window_size_default`

## 8. `[rules]`

The `[rules]` section contains:

- `filter_slots_json`
- `exclude_slots_json`
- `hl_slots_json`

These are JSON arrays with up to five slot entries each.

Each slot typically contains:

- `pattern`
- `mode`
- `color`

## 9. Visualizer Sections

Visualizer configs are stored in:

- `plot_visualizer_1` to `plot_visualizer_5`
- `logic_visualizer_1` to `logic_visualizer_5`

Important notes:

- plot and logic slots are persisted separately
- each slot has its own configuration
- older `visualizer_1..5` sections are migrated into the newer split schema

Typical keys include:

- `enabled`
- `title`
- `filter_string`
- `graph_type`
- `max_samples`
- `sliding_window_enabled`
- `default_window_size`
- `window_geometry`
- `x_label`
- `field_count`

Plus per-field keys such as:

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

## 10. Live Logs and Screenshots

During a listener session, the app creates a live log file inside
`logs_dir`.

Typical file naming:

```text
udp_live_YYYYMMDD_HHMMSS.txt
```

Project mode can prefix file names with the active project name.

Screenshots are typically written below the effective log location,
usually in a `screenshots` subfolder.

## 11. Project Descriptions

When a project is created or saved through the `PROJECT` dialog, the app
writes:

```text
README_<projectname>.md
```

into the project folder.

The project-name character set is currently limited to:

- `A-Z`
- `a-z`
- `0-9`
- `_`
- `-`

## 12. Relevant Source Files

- [config_manager.py](../src/udp_log_viewer/config_manager.py)
- [preferences.py](../src/udp_log_viewer/preferences.py)
- [project_runtime.py](../src/udp_log_viewer/project_runtime.py)
- [config_store.py](../src/udp_log_viewer/data_visualizer/config_store.py)
