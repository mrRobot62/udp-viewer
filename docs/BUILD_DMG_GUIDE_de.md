# UDP Log Viewer — DMG-Build-Anleitung (macOS)

Diese Anleitung beschreibt den aktuellen lokalen DMG-Build für den UDP
Log Viewer auf macOS.

## 1. Ziel

Es gibt derzeit zwei macOS-Wege:

- den führenden lokalen DMG-Build über `./build_dmg.sh`
- einen alternativen `dmgbuild`-Pfad unter `packaging/macos/`

Für normale Builds sollte zuerst der Root-Wrapper verwendet werden.

## 2. Voraussetzungen

- macOS mit Xcode Command Line Tools
- Python `3.12`
- aktives Projekt-Environment mit `cx_Freeze`

Empfohlener Start:

```bash
cd /Users/bernhardklein/workspace/python/udp-viewer
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade cx-Freeze
python -m pip install -e .[dev]
```

## 3. Führender Buildpfad

Der empfohlene lokale Build ist:

```bash
./build_dmg.sh
```

Dieses Skript ruft intern auf:

```bash
python freeze_setup.py bdist_dmg
```

Relevante Dateien:

- [build_dmg.sh](../build_dmg.sh)
- [freeze_setup.py](../freeze_setup.py)
- [freeze_entry.py](../freeze_entry.py)

## 4. Alternative mit `dmgbuild`

Zusätzlich existiert:

- [packaging/macos/build_dmg.sh](../packaging/macos/build_dmg.sh)

Dieser Pfad ist sinnvoll, wenn die DMG-Gestaltung explizit über
`dmgbuild` gesteuert werden soll.

Ablauf:

1. `python freeze_setup.py bdist_mac`
2. `python -m dmgbuild -s packaging/macos/dmg_settings.py "UDPLogViewer" "dist/UDPLogViewer.dmg"`

Relevante Dateien:

- [packaging/macos/build_dmg.sh](../packaging/macos/build_dmg.sh)
- [packaging/macos/dmg_settings.py](../packaging/macos/dmg_settings.py)

## 5. Typische Ausgaben

Je nach Tool-Version entstehen typischerweise:

- `build/UDPLogViewer.dmg`
- `dist/UDPLogViewer.dmg`
- `build/UDPLogViewer.app` oder ein Bundle unterhalb von `build/`

## 6. Praktischer Test

Nach dem Build sollte mindestens geprüft werden:

1. Anwendung startet
2. Fenstertitel zeigt die erwartete Version
3. `CONNECT` funktioniert
4. Live-Logdatei wird angelegt

## 7. Typische Probleme

### `ModuleNotFoundError: No module named 'cx_Freeze'`

`cx_Freeze` ist nicht im aktuell aktiven Python-Interpreter installiert.

### Falsche oder alte Artefakte

Vor einem frischen lokalen Build sollte der bisherige `build`- oder
`dist`-Inhalt geprüft oder bewusst weggeräumt werden.

### Unterschiedliche DMG-Namen lokal und im Release

Lokal kann die Datei unterschiedlich heißen. Der GitHub-Workflow benennt
das gefundene Artefakt vor dem Release-Upload in
`UDPLogViewer-<version>.dmg` um.

## 8. Empfehlung

Für normale lokale Arbeit:

- `./build_dmg.sh`

Nur bei bewusstem Bedarf an einer separaten `dmgbuild`-Layout-Steuerung:

- `packaging/macos/build_dmg.sh`
