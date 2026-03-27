# UDP Log Viewer — DMG Build Guide (macOS)

This guide describes how to build a macOS `.dmg` installer for **UDP Log Viewer** using **cx_Freeze** + **dmgbuild**.
It is intended to be re-used regularly (release builds and test builds).

---

## 1) Prerequisites

### macOS
- Python 3.12 (recommended, matches current project)
- A project virtual environment (venv)

### Python packages (inside your venv)
Install/update the packaging tools:

```bash
python -m pip install -U pip
python -m pip install -U cx_Freeze dmgbuild
```

Quick check:

```bash
python -m pip list | grep -E "cx_Freeze|dmgbuild"
```

---

## 2) Project layout assumptions

This guide assumes:
- Source package: `src/udp_log_viewer/`
- Main entry module: `udp_log_viewer.main`
- Packaging assets:
  - `packaging/macos/app.icns`
  - `packaging/macos/dmg_settings.py`
- Build scripts:
  - `build_dmg.sh`
  - `freeze_setup.py`

---

## 3) Versioning (PEP 440)

Set `APP_VERSION` and the packaging version to a valid semantic version, e.g.:

- ✅ `0.14.0`
- ❌ `0.14-step10.3-bdist_dmg`  (invalid for packaging tools)

Where to set it:
- `src/udp_log_viewer/main.py` → `APP_VERSION = "0.14.0"`
- `freeze_setup.py` → `version="0.14.0"`

---

## 4) Clean old build outputs

Before building a new DMG, remove old build artifacts:

```bash
rm -rf build dist
```

(Optional) also remove `__pycache__` if you want a super-clean tree:
```bash
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
```

---

## 5) Build the app bundle / DMG

### Option A: use the helper script
```bash
chmod +x ./build_dmg.sh
./build_dmg.sh
```

### Option B: run cx_Freeze directly
```bash
python freeze_setup.py bdist_dmg
```

Expected outputs (typical):
- `build/UDPLogViewer.app`
- `build/UDPLogViewer.dmg`
- sometimes also `dist/UDPLogViewer.dmg` (depends on cx_Freeze version / settings)

---

## 6) Test the built app

### Start the bundle directly
```bash
./build/UDPLogViewer.app/Contents/MacOS/UDPLogViewer
```

If you start it from Finder, you can still inspect logs/errors via Console.app
or start from Terminal to see stdout/stderr.

### Basic functional smoke test
1. App opens (title shows version).
2. Click **CONNECT**.
3. Verify it does not crash and receives UDP lines.
4. Verify live log file is created at the configured log directory.
   (See config file below.)

---

## 7) Log directory configuration (important for packaged apps)

Packaged apps should not write logs into the current working directory.
The recommended default locations are:

- macOS:
  `~/Library/Application Support/LocalTools/UdpLogViewer/logs/`

A small `config.ini` should exist under the same Application Support area:

- macOS:
  `~/Library/Application Support/LocalTools/UdpLogViewer/config.ini`

Example:

```ini
[General]
version = 0.14.0

[Paths]
log_dir = /Users/<you>/Library/Application Support/LocalTools/UdpLogViewer/logs
```

If directory creation fails:
- show a MessageBox
- also write `[UI/ERROR] ...` to the UI log (no crash)

---

## 8) Common issues & fixes

### A) `InvalidVersion: ...`
Reason: version string is not PEP440 compatible.

Fix: use `major.minor.patch` like `0.14.0`.

---

### B) `bdist_mac has no such option 'bundle_identifier'`
Reason: cx_Freeze versions differ; some options are not supported in your installed version.

Fix:
- remove unsupported keyword args from the `bdist_mac` options section in `freeze_setup.py`.
- keep only options that your cx_Freeze accepts.

---

### C) `ImportError: attempted relative import with no known parent package`
Reason: wrong entrypoint (running a package module as a script).

Fix:
- entry point should be `udp_log_viewer.main` (module), not a direct file path
- in `freeze_setup.py`, prefer a launcher entry that imports the package cleanly.

(Your Step 10.2 fix already addressed this.)

---

### D) First start is slow (6–10s), second start is fast
This can be normal on macOS:
- Gatekeeper / first-run verification
- loading Qt frameworks / caches
- cold filesystem caches

If you want to improve this later:
- strip unused Qt components
- reduce included translations/plugins
- enable build optimizations (later step)

---

## 9) Release checklist (practical)

Before tagging a release:
- [ ] version updated (`APP_VERSION`, `freeze_setup.py`, config)
- [ ] build clean (`rm -rf build dist`)
- [ ] `python freeze_setup.py build` and run the app
- [ ] `python freeze_setup.py bdist_dmg`
- [ ] smoke test DMG install + CONNECT
- [ ] attach `.dmg` + `source` archive to GitHub release

---

## 10) Notes: signing / notarization (optional, later)

For distribution outside your own machines, macOS may require:
- code signing
- notarization

This guide intentionally skips it for now (we can add it as a later step when needed).
