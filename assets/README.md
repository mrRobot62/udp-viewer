# Assets

Dieses Verzeichnis enthält statische Projekt-Assets, die in Dokumentation, README-Dateien, Release-Texten oder weiteren begleitenden Unterlagen verwendet werden.

## Ziel

Das Verzeichnis soll künftig vermeiden, dass Screenshots und andere visuelle Materialien nur:

- extern bei GitHub-Assets liegen
- verstreut in Release-Texten auftauchen
- oder an mehreren Stellen mit unterschiedlichen URLs referenziert werden

## Empfohlene Struktur

- `assets/screenshots/`
  Screenshots der Anwendung für README, Dokumentation und Releases
- `assets/diagrams/`
  optionale Diagramme, Ablaufbilder oder Architekturabbildungen
- `assets/icons/`
  optionale nicht-packagingbezogene Symbol- oder Branding-Dateien

## Namenskonvention

Für Screenshots wird empfohlen:

- Dateinamen in Kleinbuchstaben
- Wörter mit Bindestrich trennen
- Dateinamen nach sichtbarer Funktion oder Ansicht benennen

Beispiele:

- `main-window.png`
- `highlighting-example.png`
- `filter-dialog.png`
- `save-dialog.png`
- `temperature-visualizer.png`
- `logic-visualizer.png`

## Nutzung in Markdown

Wenn Bilder lokal im Repository vorliegen, sollten README- und Doku-Dateien bevorzugt diese lokalen Dateien referenzieren.

Beispiel:

```md
![Main window](assets/screenshots/main-window.png)
```

## Aktueller Stand

Im aktuellen Repository-Stand liegen die in den README-Dateien eingebundenen Screenshots noch als externe GitHub-Asset-Links vor. Dieses Verzeichnis ist die vorbereitete Struktur, um solche Bilder künftig lokal und versioniert im Repository abzulegen.
