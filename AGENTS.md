# Projektanweisungen: UDP Log Viewer

## Geltungsbereich und Zusammenarbeit

- Diese Anweisungen gelten für das gesamte Repository.
- Größere Entscheidungen, Fortschritte und Ergebnisse kurz auf Deutsch erklären.
- Vor Änderungen die Repository-Anweisungen und den aktuellen Arbeitsbaum prüfen.
- Vorhandene lokale Änderungen erhalten und nicht ohne ausdrückliche Anweisung überschreiben.

## Freigaben

- Vor jedem Terminalbefehl die ausdrückliche Freigabe des Anwenders einholen.
- Keine Terminalbefehle selbständig ausführen. Dies gilt auch für lesende Befehle, Git-Abfragen, Tests, Builds und Prüfungen.
- Vor der Freigabe die konkreten Befehle und ihren Zweck nennen. Mehrere Befehle dürfen gemeinsam zur Freigabe vorgelegt werden; eine Freigabe gilt nur für den ausdrücklich genehmigten Umfang.
- Eine allgemeine Aufgabenbeschreibung ist keine Freigabe für Terminalbefehle. Bei Änderungen oder zusätzlichen Befehlen erneut fragen.
- Keine Implementierung der Version 0.18.0 ohne vorherige ausdrückliche Freigabe.
- TCP-Rolle und Nachrichtenabgrenzung müssen vor der Implementierung ausdrücklich mit dem Anwender abgestimmt werden.
- Commit, Push, Merge und Veröffentlichung jeweils erst nach entsprechender ausdrücklicher Anweisung durchführen.
- Abhängige Git-Operationen strikt nacheinander ausführen.
- Für die Umsetzung den Branch `feature/0.18.0` verwenden. Seine Erstellung bzw. der Wechsel dorthin erfordert ebenfalls die vorherige Befehlsfreigabe.

## Projekt und zuletzt geprüfter Stand

- Repository: `/Users/bernhardklein/workspace/python/udp-viewer`
- Remote: https://github.com/mrRobot62/udp-viewer
- Python-/PyQt5-Desktopanwendung für Empfang, Anzeige, Filterung und Speicherung von Logs, mit Plot-/Logic-Visualizern, Projekten, Replay/Simulation und persistenten Einstellungen.
- Bei der Prüfung am 20. November 2026 standen lokales `main` und Remote-`main` auf `6635cba0d8382a085ff293ff630bf75ce28da3a3`; der Arbeitsbaum war sauber.
- Versionsmetadaten: `0.17.0`. Die vorhandene Testsuite bestand mit 118 erfolgreichen Tests.
- Version 0.17.0 wurde nach Angaben des Anwenders final veröffentlicht, einschließlich macOS-DMG und Windows-Setup.exe.
- Diese Angaben sind eine Momentaufnahme. Vor späteren Arbeiten den tatsächlichen Stand erneut prüfen, nach Freigabe der dafür notwendigen Terminalbefehle.

## Ziel für Version 0.18.0

1. UDP oder TCP in der Oberfläche auswählbar machen; UDP bleibt Standard und vollständig funktionsfähig.
2. Protokollauswahl persistent speichern. Bestehende Konfigurationen ohne Protokollangabe verwenden UDP.
3. Beide Transportarten an dieselbe Log-Verarbeitung anbinden: Filter, Speicherung, Zähler sowie Plot-/Logic-Visualizer.
4. Connect, Disconnect, RESET/CLEAR, Reconnect und Anwendungsende für beide Transportarten zuverlässig behandeln.
5. Netzwerkverarbeitung darf die Oberfläche nicht blockieren.
6. Verbindungszustände und Fehler verständlich darstellen.
7. Neue oder geänderte Klassen und Funktionen mit knappen, aussagekräftigen Docstrings dokumentieren.
8. Benutzer- und technische Dokumentation sowie Konfigurationsreferenz auf Deutsch und Englisch erst nach erfolgreichem Test der Version 0.18 und ausdrücklicher Freigabe des Anwenders erstellen bzw. aktualisieren. Diese Arbeit erfolgt als separate nachgelagerte Phase.
9. Changelog und Versionsmetadaten auf 0.18.0 vorbereiten.
10. Aussagekräftige automatisierte Tests ergänzen und relevante vorhandene Tests ausführen, jeweils nach Befehlsfreigabe.

## Architektur: geprüfte Ausgangslage

- `src/udp_log_viewer/udp_listener.py`: UDP-Empfang im Hintergrundthread, Weitergabe von Zeilen und Status über Qt-Signale.
- `src/udp_log_viewer/listener_runtime.py`: Validierung der Startparameter und Listener-Stopp.
- `src/udp_log_viewer/connection_runtime.py`: Live-Log-Zustand, Speicherung und Statusformatierung.
- `src/udp_log_viewer/main.py`: Oberfläche, gemeinsame Log-Verarbeitung und Lebenszyklussteuerung.
- `src/udp_log_viewer/ui_state.py` und `settings_store.py`: Netzwerkeinstellungen über `QSettings`.
- `src/udp_log_viewer/preferences.py` und `config_runtime.py`: weitere Einstellungen und Konfigurationsintegration.
- Eine `src/udp_log_viewer/config_manager.py` existierte bei der Prüfung nicht.
- `src/udp_log_viewer/data_visualizer/`: Plot-/Logic-Verarbeitung und transiente Fensterzustände.
- Besondere Aufmerksamkeit benötigen der bislang vom vorhandenen Listener-Objekt abgeleitete Verbindungsstatus, synchrones Warten beim Stopp und verspätete Signale alter Sitzungen nach RESET/Reconnect.

## Freigegebene Architektur

Der Anwender hat die Implementierung und die folgenden Architekturentscheidungen im Chat ausdrücklich freigegeben. Terminalbefehle benötigen weiterhin eine gesonderte vorherige Freigabe. Der Branch `feature/0.18.0` wurde nach Befehlsfreigabe angelegt.

| Thema | Freigegebene Entscheidung |
| --- | --- |
| TCP-Rolle | Viewer als TCP-Server auf lokaler Bind-IP und Port. |
| Nachrichtenabgrenzung | UTF-8-Zeilen mit LF oder CRLF; Teilnachrichten puffern und mehrere Nachrichten je Empfang aufteilen. |
| Gleichzeitige Clients | Ein aktiver Client; zusätzliche Verbindungen schließen und verständlich melden, bestehenden Client erhalten. |
| Verbindungsabbruch | Server lauscht weiter und erlaubt erneute Verbindung des Senders; vorhandene Logs und Visualizer-Daten bleiben erhalten. |
| Unvollständige letzte Zeile | Bei Abbruch verwerfen und melden; nicht mit der nächsten Verbindung vermischen. |
| Größenlimit | Maximal 1 MiB je Nachricht ohne Zeilenabschluss; bei Überschreitung Client trennen, Puffer leeren und weiter lauschen. |
| UTF-8-Verarbeitung | Bytes bis zur vollständigen Zeile puffern, damit fragmentierte UTF-8-Sequenzen erhalten bleiben; ungültige Sequenzen durch U+FFFD ersetzen. |
| Leerzeilen | Leere und ausschließlich aus Leerraum bestehende Zeilen wie bisher bei UDP ignorieren. |
| Zähler | UDP: Datagramme und Zeilen. TCP: empfangene Bytes und vollständige Zeilen. Vor Anzeigefiltern zählen; TCP-Lesevorgänge nicht als Pakete ausweisen. |
| Persistenz | `net/protocol` in QSettings mit Standard `udp`. |
| Oberfläche | Protokollwechsel im getrennten Zustand; Start, Lauschen, Client verbunden, Stop und Fehler unterscheiden. |

Die bisherige UDP-Datagramm- und Zeilenbehandlung soll erhalten bleiben. Falls der Anwender TCP-Clientbetrieb oder mehrere gleichzeitige Clients wünscht, Architektur und Aufwand vor Umsetzung neu abstimmen.

## Regression und Testumfang

- Bekannter Regressionfall: längere Laufzeit, Disconnect ohne Speichern, RESET/CLEAR, neues Projekt und Reconnect führten früher zu fehlenden Zuständen im Logic-Fenster.
- Den Fix aus 0.17.0 erhalten: transiente Visualizer-Zustände einschließlich Auto-Refresh, Freeze und Messzustand beim Reset zurücksetzen.
- `clear_all_buffers()` ruft derzeit `reset_runtime_state(clear_samples=True)` auf. Diesen Zusammenhang erhalten und die vollständige Wiederverbindungssequenz testen.
- Geplante zusätzliche Tests: fragmentierte Nachrichten und UTF-8-Sequenzen, mehrere Zeilen pro Empfang, CRLF, Verbindungsabbruch, Restpuffer, Größenlimit, zusätzliche Clients, Bind-Fehler, Stop/Reconnect, Persistenz und UDP-Fallback sowie gemeinsame Verarbeitung und Visualizer-Regression.
- Lokale Tests ersetzen keine plattformspezifischen Prüfungen auf macOS und Windows.
- Relevante Release-Workflows: `.github/workflows/macos-release.yml` und `.github/workflows/windows-release.yml`. Keine Veröffentlichung ohne ausdrückliche Anweisung.

## Aufwand und Kontingent

- Die ursprüngliche Frage nach dem Aufwand bezieht sich auf das benötigte Codex-Kontingent, nicht auf Entwicklungstage. Die zuvor genannten 4–6 Entwicklungstage beantworten diese Frage nicht.
- Das verbleibende Kontingent und die genaue Abrechnung sind nicht bekannt. Keine verbindlichen Prozent-, Token- oder Kostenangaben ohne belastbare Nutzungsdaten machen.
- Dokumentation bei der Kontingentplanung als separate Phase nach erfolgreichen Tests und ausdrücklicher Freigabe berücksichtigen.
- Hauptaufwand: TCP-Framing und Limits, nicht blockierender Verbindungslebenszyklus sowie Reset-/Reconnect-Regressionsschutz.
- Eine Kontingentschätzung setzt den oben vorgeschlagenen TCP-Server mit einem aktiven Client voraus; zusätzliche Rollen oder parallele Clients erweitern den Umfang.
