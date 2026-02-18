# UDP Log Viewer

Leichtgewichtiger UDP Log Viewer für Embedded Systeme wie ESP32.

Dieses Tool ermöglicht das Empfangen, Anzeigen und Analysieren von UDP
Logdaten in Echtzeit.

------------------------------------------------------------------------

## Übersicht

UDP Log Viewer ist eine Desktop-Anwendung basierend auf Python und
PyQt5.\
Sie wurde speziell für das Debugging von Embedded-Systemen über Netzwerk
entwickelt.

Typische Anwendungsfälle:

-   ESP32 Debugging über WLAN
-   Loganalyse ohne USB-Verbindung
-   Echtzeitüberwachung während Hardwaretests
-   Remote-Diagnose

------------------------------------------------------------------------

## Screenshot

```{=html}
<!-- Hier Screenshots einfügen -->
```
![Hauptfenster](docs/screenshots/main_window.png)

![Filter und Highlight](docs/screenshots/filter_highlight.png)

------------------------------------------------------------------------

## Features

-   Echtzeit UDP Log Empfang
-   Schnelle und schlanke Oberfläche
-   Highlight-, Filter- und Exclude-System
-   Zeitstempel-Unterstützung
-   Logs speichern
-   Pause/Resume
-   Simulation und Replay
-   Plattformübergreifend (macOS, Windows, Linux)

------------------------------------------------------------------------

## Installation

Start aus Source-Code:

``` bash
python -m venv venv
source venv/bin/activate
pip install -e .
udp-log-viewer
```

------------------------------------------------------------------------

## Kurzanleitung (User Manual)

### Schritt 1 -- Anwendung starten

``` bash
udp-log-viewer
```

------------------------------------------------------------------------

### Schritt 2 -- Gerät konfigurieren

Das Gerät muss UDP Logs an die IP-Adresse des PCs senden.

------------------------------------------------------------------------

### Schritt 3 -- Logs anzeigen

Logs erscheinen automatisch im Hauptfenster.

------------------------------------------------------------------------

### Schritt 4 -- Filter verwenden

Filter ermöglichen:

-   Hervorhebung wichtiger Meldungen
-   Ausblenden unwichtiger Logs

------------------------------------------------------------------------

## Entwicklung

Bootstrap:

``` bash
./scripts/bootstrap_macos_linux.sh
```

Start:

``` bash
./scripts/dev_run.sh
```

Tests:

``` bash
./scripts/dev_test.sh
```

------------------------------------------------------------------------

## Roadmap

Geplante Erweiterungen:

-   Erweiterte Filter
-   Plugin-System
-   Erweiterte Exportfunktionen

------------------------------------------------------------------------

## Autor

Bernhard Klein
