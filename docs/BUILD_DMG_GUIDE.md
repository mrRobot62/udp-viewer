# UDP Log Viewer — DMG Build Guide (macOS)

This guide describes the current local DMG build paths for UDP Log
Viewer on macOS.

## 1. Goal

Two macOS paths currently exist:

- the main local DMG build via `./build_dmg.sh`
- the alternative `dmgbuild`-based path under `packaging/macos/`

For normal builds, the root helper script should be treated as the
primary path.

## 2. Prerequisites

- macOS with Xcode Command Line Tools
- Python `3.12`
- active project environment with `cx_Freeze`

Recommended start:

```bash
cd /Users/bernhardklein/workspace/python/udp-viewer
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade cx-Freeze
python -m pip install -e .[dev]
```

## 3. Primary Build Path

The recommended local build is:

```bash
./build_dmg.sh
```

That wrapper currently executes:

```bash
python freeze_setup.py bdist_dmg
```

Relevant files:

- [build_dmg.sh](../build_dmg.sh)
- [freeze_setup.py](../freeze_setup.py)
- [freeze_entry.py](../freeze_entry.py)

## 4. Alternative `dmgbuild` Path

An additional path exists:

- [packaging/macos/build_dmg.sh](../packaging/macos/build_dmg.sh)

This path is useful when the DMG layout should be controlled explicitly
through `dmgbuild`.

Sequence:

1. `python freeze_setup.py bdist_mac`
2. `python -m dmgbuild -s packaging/macos/dmg_settings.py "UDPLogViewer" "dist/UDPLogViewer.dmg"`

Relevant files:

- [packaging/macos/build_dmg.sh](../packaging/macos/build_dmg.sh)
- [packaging/macos/dmg_settings.py](../packaging/macos/dmg_settings.py)

## 5. Typical Outputs

Depending on tool version, typical outputs are:

- `build/UDPLogViewer.dmg`
- `dist/UDPLogViewer.dmg`
- `build/UDPLogViewer.app` or a bundle below `build/`

## 6. Practical Smoke Test

After the build, verify at least:

1. application launches
2. window title shows the expected version
3. `CONNECT` works
4. a live log file is created

## 7. Common Problems

### `ModuleNotFoundError: No module named 'cx_Freeze'`

`cx_Freeze` is missing in the currently active interpreter.

### Old or wrong artifacts

Before a fresh build, inspect or intentionally clear old `build` and
`dist` outputs.

### Different local and release file names

Local file names may vary. The GitHub macOS workflow later renames the
selected file to `UDPLogViewer-<version>.dmg` before uploading it to the
release.

## 8. Recommendation

For normal local work:

- `./build_dmg.sh`

Only when explicit `dmgbuild`-based Finder layout control is required:

- `packaging/macos/build_dmg.sh`
