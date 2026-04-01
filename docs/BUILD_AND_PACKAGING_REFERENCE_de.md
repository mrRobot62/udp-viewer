# Build- und Packaging-Referenz des UDP Viewers

Dieses Dokument beschreibt die aktuellen Build-, Test-, Packaging- und
Release-Wege des UDP Viewers im Stand `0.16.0`. Es ist bewusst
praxisorientiert: Ziel ist, die heute führenden Pfade von historischen
oder sekundären Varianten zu trennen und dabei die wichtigsten Risiken
klar zu benennen.

## 1. Umfang

Diese Referenz beantwortet vier praktische Fragen:

- wie die Entwicklungsumgebung eingerichtet wird
- wie die Anwendung lokal gestartet und getestet wird
- wie macOS- und Windows-Artefakte gebaut werden
- wie GitHub diese Artefakte aktuell an Releases anhängt

## 2. Aktuelle Versionsquellen

Die maßgeblichen Versionsquellen sind derzeit:

- [__init__.py](../src/udp_log_viewer/__init__.py)
- [pyproject.toml](../pyproject.toml)

Wichtig:

- `__version__` trägt die Produktversion wie `0.16.0`
- `__build__` kann optional einen Build-Marker wie `RC1` tragen
- Release-Tags wie `0.16.0-rc2` leben in Git und nicht im Paket selbst

## 3. Entwicklungs-Bootstrap

### 3.1 macOS und Linux

Die gemeinsame Shell-Konfiguration liegt in:

- [common.env](../scripts/common.env)

Der führende Bootstrap-Pfad ist:

- [bootstrap_macos_linux.sh](../scripts/bootstrap_macos_linux.sh)

Dort wird aktuell angenommen:

- virtuelles Environment: `${HOME}/workspace/venv/udp-viewer`
- Interpreter: `python3`
- editable Installation mit `.[dev]`

### 3.2 Windows

Der empfohlene Windows-Bootstrap ist:

- [bootstrap_windows.ps1](../scripts/bootstrap_windows.ps1)

Dieses Skript:

- erzeugt das virtuelle Environment unter `%USERPROFILE%\workspace\venv\udp-viewer`
- installiert das Projekt mit Dev-Abhängigkeiten
- aktualisiert optional `pre-commit`, `ruff` und `mypy`

Die Batch-Variante

- [bootstrap_windows.bat](../scripts/bootstrap_windows.bat)

ist im aktuellen Repository-Stand weiterhin fehlerhaft formatiert und
sollte nicht als empfohlener Bootstrap-Weg verwendet werden.

## 4. Starten und Testen aus dem Quellcode

Aktuelle Hilfsskripte:

- [dev_run.sh](../scripts/dev_run.sh)
- [dev_test.sh](../scripts/dev_test.sh)
- [dev_run.ps1](../scripts/dev_run.ps1)
- [dev_test.ps1](../scripts/dev_test.ps1)

Aktuelles Verhalten:

- Source-Run auf macOS/Linux: `udp-log-viewer`
- Source-Run auf Windows: `python -m udp_log_viewer.main`
- Testpfad: `python -m pytest -q`

## 5. Packaging-Einstiegspunkte

### 5.1 Plattformübergreifender cx_Freeze-Einstieg

Der wichtigste plattformübergreifende Packaging-Einstiegspunkt ist:

- [freeze_setup.py](../freeze_setup.py)

Gründe:

- verarbeitet das aktuelle `src`-Layout korrekt
- nutzt [freeze_entry.py](../freeze_entry.py)
- liest die Version aus `udp_log_viewer.__version__`
- unterstützt `build_exe`, `bdist_mac` und `bdist_dmg`

### 5.2 Windows-spezifischer cx_Freeze-Einstieg

Zusätzlich existiert:

- [freeze_setup_win.py](../freeze_setup_win.py)

Dieser Pfad bleibt relevant, weil der Windows-Installer ihn aktuell
verwendet.

### 5.3 Älterer macOS-Einstieg

Als älterer Alternativpfad existiert außerdem:

- [freeze_setup_dmg.py](../freeze_setup_dmg.py)

Dieser Weg sollte derzeit als sekundär oder historisch eingeordnet
werden, nicht als führende Referenz.

## 6. macOS-Buildpfade

### 6.1 Führender lokaler DMG-Build

Der führende lokale macOS-Buildpfad ist:

```bash
./build_dmg.sh
```

Der Wrapper liegt in:

- [build_dmg.sh](../build_dmg.sh)

Intern läuft dabei:

```bash
python freeze_setup.py bdist_dmg
```

Das ist aktuell der primäre lokale DMG-Weg.

### 6.2 Alternative mit `dmgbuild`

Zusätzlich existiert:

- [packaging/macos/build_dmg.sh](../packaging/macos/build_dmg.sh)

Dieser Weg:

1. baut die `.app` via `python freeze_setup.py bdist_mac`
2. baut anschließend eine DMG via `python -m dmgbuild`

Diesen Pfad sollte man vor allem dann verwenden, wenn die Finder-/DMG-
Gestaltung über
[dmg_settings.py](../packaging/macos/dmg_settings.py)
explizit kontrolliert werden soll.

### 6.3 Typische Ausgaben

Je nach cx_Freeze-Version und verwendetem Pfad entstehen typischerweise:

- `build/UDPLogViewer.dmg`
- `dist/UDPLogViewer.dmg`
- `build/UDPLogViewer.app` oder ein Bundle unterhalb von `build/`

Der GitHub-macOS-Workflow sucht anschließend im Repository nach
`UDPLogViewer*.dmg` und benennt das gewählte Artefakt vor dem Upload in
`UDPLogViewer-<version>.dmg` um.

## 7. Windows-Buildpfade

### 7.1 Generischer Frozen Build

Der generische cx_Freeze-Pfad ist:

```bat
python freeze_setup.py build
```

Vorhandene Wrapper:

- [build_exe.bat](../build_exe.bat)
- [packaging/windows/build_exe.bat](../packaging/windows/build_exe.bat)

Dieser Weg erzeugt einen Frozen-Baum, aber noch keinen finalen
Installer.

### 7.2 Aktueller Installer-Build

Der führende Windows-Installer-Pfad ist:

- [build_windows_installer.bat](../scripts/build_windows_installer.bat)

Dieses Skript macht aktuell:

1. `.venv` erzeugen oder wiederverwenden
2. `cx-Freeze` plus Projekt installieren
3. `build` und `dist` leeren
4. `python freeze_setup_win.py build_exe` ausführen
5. `build\exe.*` erkennen
6. Inno Setup mit [installer.iss](../packaging/windows/installer.iss) aufrufen

Erwartete finale Installer-Benennung:

- `dist/UDPLogViewer-Setup-<version>.exe`

Der GitHub-Windows-Workflow benennt dieses Artefakt vor dem Release-
Upload in

- `UDPLogViewer-<version>-Setup.exe`

um.

## 8. GitHub-Release-Automation

Im Repository liegen zwei Release-Workflows:

- [macos-release.yml](../.github/workflows/macos-release.yml)
- [windows-release.yml](../.github/workflows/windows-release.yml)

Beide laufen in zwei Modi:

- automatisch bei `release: published`
- manuell per `workflow_dispatch` mit vorhandenem `tag_name`

### 8.1 Empfohlenes Release-Verhalten

Der sicherste Release-Ablauf ist:

1. Release-Tag auf den gewünschten Commit setzen und pushen
2. GitHub-Prerelease oder Release für genau diesen Tag anlegen
3. die beiden Packaging-Workflows über das `release`-Event automatisch laufen lassen

Dann bauen die Jobs im Kontext des veröffentlichten Tags und hängen die
Artefakte an genau dieses Release.

### 8.2 Wichtige Stolperfalle

`workflow_dispatch` kann Artefakte an einen beliebigen vorhandenen Tag
anhängen, aber der Workflow läuft trotzdem auf dem ausgewählten Git-Ref.

Das bedeutet:

- manueller Dispatch auf `main`
- Upload auf ein RC-Release eines Feature-Branches

kann dazu führen, dass Artefakte aus `main` gebaut, aber an das RC-
Release angehängt werden. Dadurch entstehen falsche Versions-Artefakte.

Praktische Regel:

- bevorzugt das automatische `release`-Event verwenden
- manuellen Dispatch nur nutzen, wenn ausgewählter Ref und Ziel-Tag
  garantiert denselben Codezustand meinen

## 9. Aktuelle praktische Empfehlung

Für lokale Entwicklung:

- macOS/Linux: [bootstrap_macos_linux.sh](../scripts/bootstrap_macos_linux.sh), danach [dev_run.sh](../scripts/dev_run.sh) und [dev_test.sh](../scripts/dev_test.sh)
- Windows: [bootstrap_windows.ps1](../scripts/bootstrap_windows.ps1), danach [dev_run.ps1](../scripts/dev_run.ps1) und [dev_test.ps1](../scripts/dev_test.ps1)

Für lokales Packaging:

- macOS-DMG: `./build_dmg.sh`
- Windows-Installer: `scripts\build_windows_installer.bat`

Für Release-Artefakte:

- GitHub-Release auf dem gewünschten Tag anlegen
- DMG und Setup EXE über die Release-Workflows automatisch anhängen lassen

## 10. Verbleibende Risiken

Das Build- und Release-System ist heute deutlich klarer, aber noch nicht
vollständig fertig.

Offene Punkte:

- `bootstrap_windows.bat` sollte repariert oder entfernt werden
- `freeze_setup.py`, `freeze_setup_win.py` und `freeze_setup_dmg.py`
  überlappen sich konzeptionell weiterhin
- lokale macOS-Builds hängen vom aktiven Python-Environment und
  `cx_Freeze` ab
- Windows-Packaging braucht weiterhin eine echte Windows-Toolchain mit
  Inno Setup
