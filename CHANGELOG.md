# Changelog

All notable changes to the UDP Log Viewer project will be documented in
this file.

The format is based on Keep a Changelog and follows semantic versioning
principles where applicable.

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
