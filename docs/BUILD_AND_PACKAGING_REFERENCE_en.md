# Build and Packaging Reference for UDP Viewer

This document describes the current build, test, packaging, and release
paths that exist in the UDP Viewer repository as of version `0.16.0`.
Its purpose is practical: it explains which paths are the current
leading ones, which are secondary, and where the most important risks
and footguns still are.

## 1. Scope

This reference answers four practical questions:

- how to bootstrap a local development environment
- how to run and test the application from source
- how to build macOS and Windows artifacts
- how GitHub release automation currently attaches those artifacts

## 2. Current Source of Truth

The currently relevant version sources are:

- [__init__.py](../src/udp_log_viewer/__init__.py)
- [pyproject.toml](../pyproject.toml)

Important:

- `__version__` carries the product version such as `0.16.0`
- `__build__` can carry an optional build marker such as `RC1`
- release tags such as `0.16.0-rc2` live in Git, not inside the package

## 3. Development Bootstrap

### 3.1 macOS and Linux

The shared shell configuration is:

- [common.env](../scripts/common.env)

The main bootstrap path is:

- [bootstrap_macos_linux.sh](../scripts/bootstrap_macos_linux.sh)

That path currently assumes:

- virtual environment: `${HOME}/workspace/venv/udp-viewer`
- interpreter: `python3`
- editable install with `.[dev]`

### 3.2 Windows

The preferred Windows bootstrap path is:

- [bootstrap_windows.ps1](../scripts/bootstrap_windows.ps1)

This script:

- creates the virtual environment under `%USERPROFILE%\workspace\venv\udp-viewer`
- installs the project with development extras
- optionally refreshes `pre-commit`, `ruff`, and `mypy`

The batch variant

- [bootstrap_windows.bat](../scripts/bootstrap_windows.bat)

is still malformed in the current repository state and should not be
used as the recommended bootstrap path.

## 4. Running and Testing From Source

Current helper scripts:

- [dev_run.sh](../scripts/dev_run.sh)
- [dev_test.sh](../scripts/dev_test.sh)
- [dev_run.ps1](../scripts/dev_run.ps1)
- [dev_test.ps1](../scripts/dev_test.ps1)

Current behavior:

- source run on macOS/Linux: `udp-log-viewer`
- source run on Windows: `python -m udp_log_viewer.main`
- test path: `python -m pytest -q`

## 5. Packaging Entry Points

### 5.1 Cross-platform cx_Freeze entry

The main cross-platform packaging entry point is:

- [freeze_setup.py](../freeze_setup.py)

Reasons:

- uses the current `src` layout correctly
- uses [freeze_entry.py](../freeze_entry.py)
- reads the version from `udp_log_viewer.__version__`
- supports `build_exe`, `bdist_mac`, and `bdist_dmg`

### 5.2 Windows-specific cx_Freeze entry

An additional Windows-specific entry point exists:

- [freeze_setup_win.py](../freeze_setup_win.py)

This is still relevant because the Windows installer script uses it.

### 5.3 Older macOS-specific entry

An older alternative macOS path also exists:

- [freeze_setup_dmg.py](../freeze_setup_dmg.py)

This should currently be treated as a secondary or historical path, not
the primary reference.

## 6. macOS Build Paths

### 6.1 Primary local DMG build

The leading local macOS build path is:

```bash
./build_dmg.sh
```

The wrapper lives at:

- [build_dmg.sh](../build_dmg.sh)

Internally this runs:

```bash
python freeze_setup.py bdist_dmg
```

This is the current primary local DMG path.

### 6.2 Alternative `dmgbuild` path

An alternative path also exists:

- [packaging/macos/build_dmg.sh](../packaging/macos/build_dmg.sh)

This path:

1. builds the `.app` via `python freeze_setup.py bdist_mac`
2. then builds a DMG via `python -m dmgbuild`

Use this path only when Finder layout control through
[dmg_settings.py](../packaging/macos/dmg_settings.py)
is explicitly needed.

### 6.3 Typical outputs

Depending on cx_Freeze version and path used, typical outputs are:

- `build/UDPLogViewer.dmg`
- `dist/UDPLogViewer.dmg`
- `build/UDPLogViewer.app` or a bundle below `build/`

The GitHub macOS workflow searches the repository for `UDPLogViewer*.dmg`
and then renames the selected artifact to `UDPLogViewer-<version>.dmg`
before uploading it to the release.

## 7. Windows Build Paths

### 7.1 Generic frozen build

The generic cx_Freeze build path is:

```bat
python freeze_setup.py build
```

Wrappers currently present:

- [build_exe.bat](../build_exe.bat)
- [packaging/windows/build_exe.bat](../packaging/windows/build_exe.bat)

This produces a frozen build tree, but not a final installer.

### 7.2 Current installer build

The leading Windows installer path is:

- [build_windows_installer.bat](../scripts/build_windows_installer.bat)

This script currently:

1. creates or reuses `.venv`
2. installs `cx-Freeze` plus the project
3. clears `build` and `dist`
4. runs `python freeze_setup_win.py build_exe`
5. detects `build\exe.*`
6. invokes Inno Setup with [installer.iss](../packaging/windows/installer.iss)

Expected final installer naming:

- `dist/UDPLogViewer-Setup-<version>.exe`

The GitHub Windows release workflow later renames that artifact to:

- `UDPLogViewer-<version>-Setup.exe`

before attaching it to a GitHub release.

## 8. GitHub Release Automation

The repository contains two release workflows:

- [macos-release.yml](../.github/workflows/macos-release.yml)
- [windows-release.yml](../.github/workflows/windows-release.yml)

Both can run in two modes:

- automatically on `release: published`
- manually via `workflow_dispatch` with an existing `tag_name`

### 8.1 Recommended release behavior

The safest release flow is:

1. create and push the release tag on the intended commit
2. create the GitHub prerelease or release for that tag
3. allow the `release` event to trigger both packaging workflows

That path ensures the jobs run on the tagged release context and attach
their assets to the matching release.

### 8.2 Important footgun

`workflow_dispatch` can attach assets to any existing tag name, but the
workflow itself still runs on the selected Git ref.

That means:

- if you manually dispatch from `main`
- but upload to a release tag that points to a feature-branch RC

the workflow may build artifacts from `main` and then upload them to the
RC release. This can produce wrong-version assets.

Practical rule:

- prefer the automatic `release` event
- only use manual dispatch when you are certain the selected ref and the
  target tag belong to the same code state

## 9. Current Practical Recommendation

For local development:

- macOS/Linux: [bootstrap_macos_linux.sh](../scripts/bootstrap_macos_linux.sh), then [dev_run.sh](../scripts/dev_run.sh) and [dev_test.sh](../scripts/dev_test.sh)
- Windows: [bootstrap_windows.ps1](../scripts/bootstrap_windows.ps1), then [dev_run.ps1](../scripts/dev_run.ps1) and [dev_test.ps1](../scripts/dev_test.ps1)

For local packaging:

- macOS DMG: `./build_dmg.sh`
- Windows installer: `scripts\build_windows_installer.bat`

For release assets:

- use a GitHub release on the intended tag
- let the release event workflows attach the DMG and Setup EXE

## 10. Remaining Risks

The build and release system is much clearer than before, but not fully
finished.

Open points:

- `bootstrap_windows.bat` should still be repaired or removed
- `freeze_setup.py`, `freeze_setup_win.py`, and `freeze_setup_dmg.py`
  still overlap conceptually
- macOS local builds depend on the active Python environment and
  `cx_Freeze`
- Windows packaging still requires a true Windows toolchain with
  Inno Setup
