# Changelog

All notable changes to the UDP Log Viewer project will be documented in
this file.

The format is based on Keep a Changelog and follows semantic versioning
principles where applicable.

------------------------------------------------------------------------
## 0.17.0 -- 2026-04-10
### Added

-   Expanded plot and logic visualizer color selection with 16
    predefined, visually distinct colors
-   Added editable HTML color-code input for visualizer fields using the
    `#RRGGBB` format
-   Synchronized color presets and manual color input so selecting a
    preset writes the corresponding hex code and manual edits switch the
    selection to `Custom`
-   Added per-slot footer format fields for plot and logic visualizers
    so users can define the footer status text with placeholders
-   Added reusable footer status presets in the central `Preferences...`
    dialog under the `Visualizer` tab
-   Added footer preset table editing with `ADD`, `DEL`, `UP`, and
    `DOWN` actions
-   Added footer preset type scoping with `All`, `Plot`, and `Logic` so
    plot and logic slot dialogs only show applicable presets
-   Added a footer preset dropdown to plot and logic visualizer slot
    configuration dialogs
-   Added footer placeholders `{samples}`, `{start}`, `{end}`, and
    `{duration}` for both plot and logic visualizers
-   Added plot footer field placeholders such as `{Thot}`,
    `{current:Thot}`, `{latest:Thot}`, `{mean:Thot}`, `{avg:Thot}`,
    and `{max:Thot}`
-   Added logic footer channel placeholders such as `{ch0}` for the
    latest channel state
-   Added Python-style footer format specifications such as
    `{samples:04d}`, `{Thot:03.1f}`, and `{mean:Thot:04.1f}`
-   Added user guide documentation for footer placeholders, `mean`/`avg`
    availability, and supported Python-style formatting variants
-   Added bilingual release notes for `0.17.0`

### Improved

-   Limited visualizer footer labels to a compact two-line layout and
    enabled wrapping so long footer text no longer forces graph windows
    to grow horizontally
-   Preserved manual footer editing by switching the preset dropdown to
    `Custom` whenever the configured text no longer matches a preset
-   Limited footer preset names to 12 characters for readable dropdowns
    and table entries
-   Added a multi-line footer format editor in `Preferences...` so
    preset formats can be edited with real line breaks instead of only
    escaped `\n` sequences
-   Enforced unique footer preset names during preference normalization;
    the first matching name is kept
-   Updated default footer presets to use compact custom formats instead
    of the previous long automatic statistics line
-   Updated footer preset defaults and templates to include total sample
    count via `{samples}`
-   Reworked bilingual user and technical documentation so footer
    placeholders, internal plot statistics, and configuration keys are
    documented consistently
-   Updated README documentation links to the current `0.17.0` release
    and added visualizer footer/color feature bullets

### Fixed

-   Fixed Preferences dialog footer-preset button layout so `ADD`,
    `DELETE`, `UP`, and `DOWN` appear together below the preset table
-   Replaced the Preferences dialog `OK` button with `Save` and placed
    `Apply` between `Cancel` and `Save`
-   Removed the legacy plot `MAX/Mean/Current` status block from
    configured footer templates by normalizing old `{stats}` placeholders
    out of existing configs and presets
-   Kept the legacy plot statistics footer only as a fallback when no
    custom footer format is configured
-   Preserved existing legacy named colors by mapping them to the new hex
    color values when loading color widgets
-   Avoided Qt test crashes by keeping a stable `QApplication` reference
    in visualizer dialog tests

### Technical

-   Bumped application and package version metadata to `0.17.0`
-   Added shared color-selection and footer-format helper modules for
    reuse across plot and logic visualizer dialogs/windows
-   Added persistence for custom footer status formats in visualizer slot
    configs
-   Added persistence for central footer status presets in preferences
-   Expanded automated coverage for color selection, footer placeholder
    rendering, legacy `{stats}` migration, footer preset persistence,
    preset filtering, sample-count placeholders, and version metadata

------------------------------------------------------------------------
## 0.16.3 -- 2026-04-06
### Fixed

-   Show the exit save dialog whenever the current session already
    contains log data, even after the listener has been disconnected or
    the main window is closed via the window close action

-   Retry listener shutdown with a longer wait timeout when the first
    stop attempt does not finish in time

### Improved

-   Updated the English and German README demo-project wording and
    regenerated the bundled README PDFs

### Technical

-   Bumped application and package version metadata to `0.16.3`
-   Added regression coverage for disconnected-session exit-save
    handling and listener shutdown retry behavior

------------------------------------------------------------------------
## 0.16.2 -- 2026-04-05
### Fixed

-   Prevented open plot and logic visualizer windows from closing when
    the `PROJECT` dialog is saved
-   Reset the active project context correctly on main-window `RESET`
    so the next `PROJECT` dialog starts with empty project name, default
    root folder, and default description
-   Added a `NEW` action in the `PROJECT` dialog to restore the same
    default project state without leaving the dialog
-   Improved UDP listener restart robustness so follow-up runs can bind
    and receive client logs more reliably after disconnect/reset cycles
-   Added save confirmation on application exit when a live session is
    still connected and has already received log data

### Improved

-   Added meaningful tooltips to the relevant dialog actions, check
    boxes, and input widgets across the main window, project dialog,
    preferences dialog, slot-copy dialog, and visualizer dialogs
-   Replaced the static `Window Size` tooltip with a tooltip derived
    from the actual slot configuration so the displayed max value is no
    longer misleading
-   Added a persistent footer status line to plot and logic graph
    windows showing session start time and duration
-   Extended plot footer statistics to support compact
    `MAX/Mean/Current` output with at most one decimal place
-   Added a per-field `Statistic` switch to the plot configuration so
    only selected `Line` series appear in the footer statistics

### Technical

-   Bumped application and package version metadata to `0.16.2`
-   Expanded automated coverage for exit-save behavior, project reset,
    footer status rendering, statistic persistence, tooltip helpers, and
    visualizer window context handling

------------------------------------------------------------------------
## 0.16.0 -- 2026-04-01
### Added

-   Added a main-window `RESET` action that clears the active in-memory
    log session, keeps the current project context, and immediately
    prepares a fresh live log file
-   Added runtime live-log session rotation helpers so reset/connect
    flows can reuse or rotate live files consistently
-   Added logic-graph edge measurement with start/end markers, duration
    labels, automatic pause during measurement, and `Space`/`Esc` to
    clear the measurement
-   Added `Shift`-click period measurement in the logic graph to measure
    from one edge to the next edge of the same type
-   Added project-description notes in the `PROJECT` dialog and write
    them as `README_<projectname>.md` files inside the project folder

### Improved

-   Limited plot and logic `Window Size` controls to `1..5000` and
    exposed the allowed range via tooltips in graph windows and config
    dialogs
-   Added runtime `Legend` toggles in plot and logic graph windows
-   Moved compact logic-measurement labels to the right of the blue end
    marker when the measured span is too short for centered text
-   Reused an already prepared live log on the next `CONNECT` instead of
    rotating it again immediately after a reset
-   Added explicit `TAB` navigation plus keyboard shortcuts for save and
    screenshot actions in the main and graph windows

### Technical

-   Bumped application and package version metadata to `0.16.0`
-   Expanded automated coverage for live-log rotation, logic
    measurements, label placement, and window-size clamping
-   Updated release, user, and packaging documentation for the
    final `0.16.0` release

------------------------------------------------------------------------
## 0.15.4 -- 2026-03-31
### Added

-   Added a main-window `RESET` action that clears the in-memory log
    session, resets counters and pause buffers, preserves the active
    project context, and starts a fresh live log file with a new
    timestamp

### Improved

-   Reused an already prepared live log on the next `CONNECT` instead of
    rotating it again immediately after a reset

### Technical

-   Bumped application and package version metadata to `0.15.4`
-   Added regression coverage for the reset-session workflow in the main
    window

------------------------------------------------------------------------
## 0.15.3 -- 2026-03-31
### Fixed

-   Staggered latest-value labels in plot windows to reduce overlap at
    the right edge
-   Switched plot hover tooltips to a multi-line layout for better
    readability
-   Added plot hover guide lines and a cross cursor for easier value
    inspection
-   Updated `SAVE` and `Open Log...` to use an explicit default log
    folder and report the chosen save path in the status bar
-   Ensured live session log files follow the configured `Log Path`
-   Corrected host plot simulation output to emit `target_min` and
    `target_max` as separate values again
-   Fixed false-positive unsaved-change prompts when switching plot or
    logic slots without real edits
-   Refined the `PROJECT` dialog with wider fields, underscore support
    in project names, right-aligned long output paths, and `SAVE` as the
    default action

### Added

-   Added `Log Path` to `Preferences` so the default log/save folder can
    be configured centrally
-   Added `APPLY` actions to plot and logic configuration dialogs
-   Added a runtime-only `PROJECT` context with project-based output
    folders, file prefixes, and title suffixes

### Technical

-   Bumped application and package version metadata to `0.15.3`
-   Added coverage for legacy host plot config normalization and release
    consistency updates
-   Added runtime project-name validation and filename helper coverage

------------------------------------------------------------------------
## 0.15.2 -- 2026-03-29
### Improved

-   Expanded plot and logic visualizers to support up to 5 independent
    slots each
-   Reworked the plot and logic configuration dialogs with dedicated
    slot controls, clearer layout, and direct slot-to-slot copy support
-   Changed `SHOW` behavior so all active slots of the selected
    visualizer type are opened at once
-   Added runtime diagnostics for skipped or unavailable visualizer
    slots in the main log view

### Added

-   Per-slot persistence for plot and logic visualizers in `config.ini`
-   `COPY` and `CLEAR` actions in both visualizer configuration dialogs
-   Automatic migration from legacy `visualizer_1..5` sections to the
    new plot/logic slot schema

### Fixed

-   Prevented inactive visualizer slots from opening windows or
    buffering samples
-   Clarified Visual Studio Code debug setup for the repository `src`
    layout

### Technical

-   Bumped application and package version metadata to `0.15.2`
-   Added `matplotlib` as an explicit runtime dependency for plot
    windows
-   Expanded automated coverage for slot persistence, migration,
    multi-slot routing, and window handling

------------------------------------------------------------------------
## 0.15.1 -- 2026-03-27
### Improved

-   Added a global `Preferences...` dialog backed by `config.ini` for
    application defaults and visualizer presets
-   Refined the visualizer sliding-window UX with more realistic preset
    values and live graph controls
-   Improved logic visualizer readability with clearer level markers and
    stronger channel separation
-   Updated German documentation, including the user guide, to cover the
    new preferences and graph behavior

### Fixed

-   Ensured all visualizer windows close when quitting the application
    or closing the main window
-   Restored platform-native menu behavior so `Preferences...` and
    `Quit` follow the active operating system conventions

### Technical

-   Bumped application and package version metadata to `0.15.1`
-   Added test coverage for preference persistence and visualizer window
    shutdown behavior

------------------------------------------------------------------------
## 0.15.0 -- 2026-03-27
### Improved

-   Modernized the main window internals by extracting connection,
    listener, file, configuration, and settings runtime helpers
-   Unified version handling across packaging scripts and application
    metadata
-   Expanded documentation for user workflows, configuration, CSV input,
    packaging, and release-related tasks
-   Improved asset organization and prepared repository-managed
    screenshot handling
-   Aligned platform-specific menu and preferences behavior with the
    active operating system conventions

### Added

-   Data visualizer support with dedicated plotting windows, axis and
    field configuration, and sliding-window controls
-   Logic visualizer support with configurable channels, step rendering,
    and timestamp-based X-axis handling
-   Persistent preferences and settings storage infrastructure
-   Additional GUI and headless test coverage for runtime helpers,
    settings storage, plotting behavior, and visualizer workflows
-   Windows installer generation via Inno Setup using centrally managed
    application version information

### Technical

-   Refactored `main.py` into smaller runtime and support modules to
    reduce coupling and improve testability
-   Added supporting modules for replay simulation, rule slots, app
    paths, and UI state handling
-   Updated packaging and developer scripts to consume version metadata
    from the Python package directly

---
## 0.14.0 -- 2026-02-18
### Improved

-   Simplified developer onboarding process
-   Reproducible virtual environment setup
-   Unified development workflow across macOS, Linux, and Windows
-   Reduced setup friction for new contributors and fresh environments

### Added
-   Cross-platform developer bootstrap scripts:
    -   scripts/bootstrap_macos_linux.sh
    -   scripts/bootstrap_windows.ps1

-   Developer convenience scripts:
    -   scripts/dev_run.sh / dev_run.ps1
    -   scripts/dev_test.sh / dev_test.ps1

-   Centralized developer configuration via scripts/common.env

-   Support for editable install using `pip install -e .`

-   Support for optional developer dependencies via
    `[project.optional-dependencies].dev`

-   Consistent application startup via entry-point command:

        udp-log-viewer


### Technical

-   Fully PEP 621 compliant pyproject.toml
-   Modern setuptools build backend
-   Proper CLI entry-point definition
-   Clean separation between runtime and development dependencies

------------------------------------------------------------------------

## \[T1\] -- 2026-02-17

### Added

-   Initial UDP Log Viewer implementation
-   PyQt5 GUI application framework
-   UDP log reception and display
-   Highlight, filter, and exclude system
-   Timestamp support
-   Log saving functionality
-   Simulation and replay support
-   Cross-platform packaging support (macOS DMG, Windows EXE)
-   Application configuration via config.ini
