# Changelog

All notable changes to the UDP Log Viewer project will be documented in
this file.

The format is based on Keep a Changelog and follows semantic versioning
principles where applicable.

------------------------------------------------------------------------
## 0.15.0 -- 2026-03-16
### Improved

### Added

### Technical

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
