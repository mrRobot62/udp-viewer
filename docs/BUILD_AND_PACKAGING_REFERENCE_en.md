# Build and Packaging Reference for UDP Viewer

This document describes the current build, run, test, and packaging paths that exist in the UDP Viewer repository. It does not define a future release process. Its purpose is to document which scripts and build entry points currently exist and how they should be interpreted.

## 1. Purpose and Scope

This reference is mainly intended to answer three questions:

- How is the development environment bootstrapped?
- How is the application run and tested locally?
- Which packaging paths currently exist for macOS and Windows, and which of them are primary versus alternative?

Important:

- `freeze_setup.py` is currently the most important and most consistent packaging entry point.
- Several other scripts are wrappers or historically grown alternatives.
- Not every packaging path that exists in the repository is equally well maintained.

## 2. Development Environment

### 2.1 Shared Configuration

The macOS/Linux shell scripts use [common.env](/Users/bernhardklein/workspace/python/udp-viewer/scripts/common.env).

It currently defines:

- virtual environment at `${HOME}/workspace/venv/udp-viewer`
- Python interpreter `python3`
- installation with `.[dev]`

These values are used especially by:

- [bootstrap_macos_linux.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_macos_linux.sh)
- [dev_run.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.sh)
- [dev_test.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.sh)

### 2.2 macOS/Linux Bootstrap

The recommended bootstrap path on macOS and Linux is:

- [bootstrap_macos_linux.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_macos_linux.sh)

This script:

- creates the virtual environment if needed
- activates the environment
- upgrades `pip`, `setuptools`, and `wheel`
- installs the project in editable mode with development dependencies via `pip install -e ".[dev]"`

### 2.3 Windows Bootstrap

The most consistent Windows bootstrap path is currently:

- [bootstrap_windows.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.ps1)

This script:

- creates a virtual environment under `%USERPROFILE%\workspace\venv\udp-viewer`
- activates it
- installs the project in editable mode with development dependencies
- optionally refreshes `pre-commit`, `ruff`, and `mypy`

The batch variant

- [bootstrap_windows.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.bat)

appears to be malformed or damaged in the current repository state and should not be treated as the leading Windows bootstrap path.

## 3. Local Run and Test Paths

### 3.1 Run From Source

On macOS/Linux:

- [dev_run.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.sh)

This script activates the configured virtual environment and starts `udp-log-viewer`.

On Windows:

- [dev_run.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.ps1)

This script activates the virtual environment and then starts `python -m udp_log_viewer.main`.

### 3.2 Test Execution

On macOS/Linux:

- [dev_test.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.sh)

On Windows:

- [dev_test.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.ps1)

Both paths currently run `python -m pytest -q`.

## 4. Primary Packaging Entry Point

The main packaging entry point at the current state is:

- [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py)

Reasons:

- it is designed to be cross-platform
- it uses the current `src`-layout bootstrap
- it uses [freeze_entry.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_entry.py) as the frozen entry point
- it reads the application version from `udp_log_viewer.__version__`

Supported targets in this script:

- `build_exe`
- `bdist_mac`
- `bdist_dmg`

This makes `freeze_setup.py` the best current reference for:

- generic frozen builds
- macOS app bundles
- macOS DMG generation

## 5. macOS Build and Packaging Paths

### 5.1 Primary Path

The clearest current macOS build path is:

```bash
python freeze_setup.py bdist_dmg
```

or through the wrapper:

- [build_dmg.sh](/Users/bernhardklein/workspace/python/udp-viewer/build_dmg.sh)

This path uses `cx_Freeze` directly for DMG generation.

### 5.2 Alternative `dmgbuild` Path

An additional path exists here:

- [packaging/macos/build_dmg.sh](/Users/bernhardklein/workspace/python/udp-viewer/packaging/macos/build_dmg.sh)

This path performs two steps:

1. `python freeze_setup.py bdist_mac`
2. `python -m dmgbuild -s packaging/macos/dmg_settings.py "UDPLogViewer" "dist/UDPLogViewer.dmg"`

The corresponding DMG/Finder layout configuration lives in:

- [dmg_settings.py](/Users/bernhardklein/workspace/python/udp-viewer/packaging/macos/dmg_settings.py)

Interpretation:

- this path is technically plausible
- it is better understood as an alternative, more manually controlled DMG path
- the actual app build still comes from `freeze_setup.py`

### 5.3 Older Alternative Path

There is also:

- [freeze_setup_dmg.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_dmg.py)

This script is functionally similar, but uses `run_udp_log_viewer.py` instead of `freeze_entry.py`.

Interpretation:

- it is not obviously the leading path anymore
- it is likely an older or alternate macOS build approach
- for new documentation and future builds, `freeze_setup.py` should be treated as the primary reference

## 6. Windows Build and Packaging Paths

### 6.1 EXE Build

Several Windows frozen-build paths currently exist.

Generic primary path:

```bat
python freeze_setup.py build
```

Wrappers for that path:

- [build_exe.bat](/Users/bernhardklein/workspace/python/udp-viewer/build_exe.bat)
- [packaging/windows/build_exe.bat](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/build_exe.bat)

There is also a Windows-specific build path:

- [freeze_setup_win.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_win.py)

Interpretation:

- `freeze_setup.py` is the more consistent general primary path
- `freeze_setup_win.py` is a Windows-specific alternative with a smaller option set
- both already read the application version from the package

### 6.2 Installer Build With Inno Setup

For a Windows setup installer, the repository contains:

- [build_windows_installer.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/build_windows_installer.bat)
- [packaging_windows_installer.iss](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/packaging_windows_installer.iss)

The batch flow is conceptually:

1. create a local `.venv`
2. install `cx_Freeze`
3. run `python freeze_setup_win.py build`
4. invoke Inno Setup via `ISCC.exe`

## 7. Current Inconsistencies and Risks

The packaging state is usable, but not fully consolidated.

Important current observations:

- [build_windows_installer.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/build_windows_installer.bat) expects `packaging\windows\installer.iss`, but the repository currently contains [packaging_windows_installer.iss](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/packaging_windows_installer.iss). In its current state, the installer build path is not fully consistent.
- [packaging_windows_installer.iss](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/packaging_windows_installer.iss) still contains the hard-coded version `0.14.0` instead of the centralized package version.
- the same `.iss` file also contains a fixed `BuildDir` with a Python-version-specific directory name, which is fragile for reproducible installer builds
- [bootstrap_windows.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.bat) appears syntactically damaged and should not currently be treated as the recommended Windows bootstrap path
- [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py), [freeze_setup_win.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_win.py), and [freeze_setup_dmg.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_dmg.py) are overlapping build entry points

## 8. Recommended Practical Use at the Current State

For day-to-day development:

- macOS/Linux: [bootstrap_macos_linux.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_macos_linux.sh), then [dev_run.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.sh) and [dev_test.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.sh)
- Windows: [bootstrap_windows.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.ps1), then [dev_run.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.ps1) and [dev_test.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.ps1)

For macOS packaging:

- primarily [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py) with `bdist_dmg`
- alternatively [packaging/macos/build_dmg.sh](/Users/bernhardklein/workspace/python/udp-viewer/packaging/macos/build_dmg.sh) if a `dmgbuild`-based step is explicitly preferred

For Windows packaging:

- primarily [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py) or, if a Windows-specific path is intentionally desired, [freeze_setup_win.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_win.py)
- installer generation only after the current `.iss` and batch-path inconsistencies are cleaned up

## 9. Boundaries

This reference only documents the current state of the scripts found in the repository. It does not guarantee that every packaging path is immediately reproducible in every environment.

The next useful steps toward a robust release pipeline would be:

- consolidate on one leading Windows build path
- consolidate on one leading macOS DMG path
- align the Inno Setup script with the current version and a flexible build output path
- remove or explicitly mark broken or outdated helper scripts
