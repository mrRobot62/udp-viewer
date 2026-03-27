# Build- und Packaging-Referenz des UDP Viewers

Dieses Dokument beschreibt den aktuell im Repository vorhandenen Stand der Build-, Run-, Test- und Packaging-Wege des UDP Viewers. Es definiert keinen zukünftigen Release-Prozess, sondern dokumentiert, welche Skripte und Buildpfade heute in der Codebasis existieren und wie sie einzuordnen sind.

## 1. Ziel und Einordnung

Diese Referenz beantwortet vor allem drei Fragen:

- Wie wird die Entwicklungsumgebung eingerichtet?
- Wie wird die Anwendung lokal gestartet und getestet?
- Welche Packaging-Wege für macOS und Windows sind aktuell vorhanden, und welche davon sind primär bzw. alternativ?

Wichtig:

- `freeze_setup.py` ist derzeit der wichtigste und konsistenteste Packaging-Einstiegspunkt.
- Mehrere zusätzliche Skripte sind Wrapper oder historisch gewachsene Alternativen.
- Nicht jeder vorhandene Packaging-Pfad ist im aktuellen Stand gleich gut gepflegt.

## 2. Entwicklungsumgebung

### 2.1 Gemeinsame Konfiguration

Die Shell-Skripte auf macOS/Linux nutzen [common.env](/Users/bernhardklein/workspace/python/udp-viewer/scripts/common.env).

Dort ist aktuell definiert:

- virtuelles Environment unter `${HOME}/workspace/venv/udp-viewer`
- Python-Interpreter `python3`
- Installation mit `.[dev]`

Diese Werte steuern insbesondere:

- [bootstrap_macos_linux.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_macos_linux.sh)
- [dev_run.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.sh)
- [dev_test.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.sh)

### 2.2 macOS/Linux-Bootstrap

Der empfohlene Bootstrap auf macOS und Linux ist:

- [bootstrap_macos_linux.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_macos_linux.sh)

Dieses Skript:

- erzeugt das virtuelle Environment bei Bedarf
- aktiviert das Environment
- aktualisiert `pip`, `setuptools` und `wheel`
- installiert das Projekt editable mit Dev-Abhängigkeiten über `pip install -e ".[dev]"`

### 2.3 Windows-Bootstrap

Der konsistenteste Windows-Bootstrap ist derzeit:

- [bootstrap_windows.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.ps1)

Dieses Skript:

- legt ein virtuelles Environment unter `%USERPROFILE%\workspace\venv\udp-viewer` an
- aktiviert es
- installiert das Projekt editable mit Dev-Abhängigkeiten
- aktualisiert optional `pre-commit`, `ruff` und `mypy`

Die Batch-Variante

- [bootstrap_windows.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.bat)

ist im aktuellen Repository-Stand offensichtlich beschädigt oder falsch formatiert und sollte nicht als führender Bootstrap-Weg betrachtet werden.

## 3. Entwicklungslauf und Tests

### 3.1 Lokaler Start

Unter macOS/Linux:

- [dev_run.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.sh)

Dieses Skript aktiviert das konfigurierte virtuelle Environment und startet anschließend `udp-log-viewer`.

Unter Windows:

- [dev_run.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.ps1)

Dieses Skript aktiviert das virtuelle Environment und startet anschließend `python -m udp_log_viewer.main`.

### 3.2 Testausführung

Unter macOS/Linux:

- [dev_test.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.sh)

Unter Windows:

- [dev_test.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.ps1)

Beide Wege führen aktuell `python -m pytest -q` aus.

## 4. Primärer Packaging-Einstiegspunkt

Der aktuell wichtigste Packaging-Einstiegspunkt ist:

- [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py)

Gründe:

- das Skript ist plattformübergreifend ausgelegt
- es verwendet den aktuellen `src`-Layout-Bootstrap
- es nutzt [freeze_entry.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_entry.py) als sauberen Frozen-Entry-Point
- es bezieht die Version zentral aus `udp_log_viewer.__version__`

Unterstützte Targets in diesem Skript:

- `build_exe`
- `bdist_mac`
- `bdist_dmg`

Damit ist `freeze_setup.py` derzeit die beste Referenz für:

- generische Frozen Builds
- macOS-App-Bundles
- macOS-DMG-Erzeugung

## 5. macOS-Build- und Packaging-Wege

### 5.1 Primärer Weg

Der klarste vorhandene macOS-Buildpfad ist:

```bash
python freeze_setup.py bdist_dmg
```

oder über den Wrapper:

- [build_dmg.sh](/Users/bernhardklein/workspace/python/udp-viewer/build_dmg.sh)

Dieser Weg nutzt `cx_Freeze` direkt für die DMG-Erzeugung.

### 5.2 Alternative mit `dmgbuild`

Zusätzlich existiert:

- [packaging/macos/build_dmg.sh](/Users/bernhardklein/workspace/python/udp-viewer/packaging/macos/build_dmg.sh)

Dieser Weg macht zwei Schritte:

1. `python freeze_setup.py bdist_mac`
2. `python -m dmgbuild -s packaging/macos/dmg_settings.py "UDPLogViewer" "dist/UDPLogViewer.dmg"`

Die dazugehörige Finder-/DMG-Konfiguration liegt in:

- [dmg_settings.py](/Users/bernhardklein/workspace/python/udp-viewer/packaging/macos/dmg_settings.py)

Einordnung:

- dieser Weg ist technisch plausibel
- er ist eher ein alternativer, stärker manuell kontrollierter DMG-Pfad
- der eigentliche App-Build kommt auch hier wieder aus `freeze_setup.py`

### 5.3 Älterer Alternativpfad

Zusätzlich existiert:

- [freeze_setup_dmg.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_dmg.py)

Dieses Skript ist funktional ähnlich, nutzt aber `run_udp_log_viewer.py` statt `freeze_entry.py`.

Einordnung:

- nicht offensichtlich der führende Pfad
- wahrscheinlich älterer oder alternativer macOS-Buildansatz
- für neue Dokumentation und künftige Builds sollte eher `freeze_setup.py` als Referenz gelten

## 6. Windows-Build- und Packaging-Wege

### 6.1 EXE-Build

Es existieren mehrere Wege für einen Windows-Frozen-Build.

Generischer Primärpfad:

```bat
python freeze_setup.py build
```

Wrapper dafür:

- [build_exe.bat](/Users/bernhardklein/workspace/python/udp-viewer/build_exe.bat)
- [packaging/windows/build_exe.bat](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/build_exe.bat)

Zusätzlich existiert ein Windows-spezifischer Buildpfad:

- [freeze_setup_win.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_win.py)

Einordnung:

- `freeze_setup.py` ist der konsistentere allgemeine Hauptpfad
- `freeze_setup_win.py` ist ein Windows-spezifischer Alternativpfad mit reduzierterem Optionssatz
- beide beziehen die Version bereits zentral aus dem Paket

### 6.2 Installer-Build mit Inno Setup

Für einen Setup-Installer existieren:

- [build_windows_installer.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/build_windows_installer.bat)
- [packaging_windows_installer.iss](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/packaging_windows_installer.iss)

Der Batch-Ablauf ist konzeptionell:

1. lokales `.venv` anlegen
2. `cx_Freeze` installieren
3. `python freeze_setup_win.py build`
4. Inno Setup per `ISCC.exe` ausführen

## 7. Aktuelle Inkonsistenzen und Risiken

Der Packaging-Bestand ist nutzbar, aber nicht vollständig konsolidiert.

Wichtige aktuelle Beobachtungen:

- [build_windows_installer.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/build_windows_installer.bat) erwartet `packaging\windows\installer.iss`, im Repository liegt aber [packaging_windows_installer.iss](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/packaging_windows_installer.iss). Der Installer-Build ist damit im aktuellen Stand nicht ohne Anpassung konsistent.
- [packaging_windows_installer.iss](/Users/bernhardklein/workspace/python/udp-viewer/packaging/windows/packaging_windows_installer.iss) enthält noch die harte Version `0.14.0` statt der inzwischen zentralisierten Paketversion.
- dieselbe `.iss`-Datei enthält einen festen `BuildDir` mit Python-spezifischem Verzeichnisnamen. Das ist für reproduzierbare Installer-Builds fragil.
- [bootstrap_windows.bat](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.bat) wirkt syntaktisch beschädigt und sollte im aktuellen Stand nicht als empfohlener Windows-Bootstrap gelten.
- mit [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py), [freeze_setup_win.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_win.py) und [freeze_setup_dmg.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_dmg.py) existieren mehrere sich teilweise überlappende Build-Einstiegspunkte.

## 8. Empfohlene praktische Nutzung im aktuellen Stand

Für Entwicklungsarbeit:

- macOS/Linux: [bootstrap_macos_linux.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_macos_linux.sh), danach [dev_run.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.sh) und [dev_test.sh](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.sh)
- Windows: [bootstrap_windows.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/bootstrap_windows.ps1), danach [dev_run.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_run.ps1) und [dev_test.ps1](/Users/bernhardklein/workspace/python/udp-viewer/scripts/dev_test.ps1)

Für macOS-Packaging:

- primär [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py) mit `bdist_dmg`
- alternativ [packaging/macos/build_dmg.sh](/Users/bernhardklein/workspace/python/udp-viewer/packaging/macos/build_dmg.sh), wenn ein `dmgbuild`-basierter Schritt bewusst gewünscht ist

Für Windows-Packaging:

- primär [freeze_setup.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup.py) oder bei explizitem Windows-Sonderpfad [freeze_setup_win.py](/Users/bernhardklein/workspace/python/udp-viewer/freeze_setup_win.py)
- Installer-Generierung nur nach vorheriger Bereinigung der Inkonsistenzen im `.iss`-/Batch-Pfad

## 9. Abgrenzung

Diese Referenz beschreibt nur den Stand der vorhandenen Skripte im Repository. Sie garantiert nicht, dass jeder Packaging-Pfad in jeder Umgebung sofort reproduzierbar funktioniert.

Für eine belastbare Release-Pipeline wären als nächster Schritt sinnvoll:

- Konsolidierung auf einen führenden Windows-Buildpfad
- Konsolidierung auf einen führenden macOS-DMG-Pfad
- Vereinheitlichung des Inno-Setup-Skripts mit aktueller Version und flexiblem Build-Ausgabepfad
- Entfernung oder Kennzeichnung beschädigter bzw. veralteter Hilfsskripte
