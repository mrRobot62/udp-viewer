# Manueller Test des UDP Log Viewers

`udp_viewer_filter_test.py` erzeugt Lognachrichten ohne ESP32. Es benötigt Python 3.10 oder neuer und keine zusätzlichen Pakete. Alle folgenden Befehle werden **im Projektverzeichnis** ausgeführt; alternativ kann `python3` durch `.venv/bin/python` ersetzt werden.

## Vorbereitung und Schnellstart

1. Nur einen Viewer starten. Andere Instanzen einschließlich VSCode-/Python-Starts beenden.
2. Im Viewer UDP, Bind-IP `0.0.0.0`, Port `10514` einstellen und CONNECT wählen.
3. Für den ersten Test Filter und Exclude leeren und PAUSE ausschalten. Die Filter-/Exclude-Verknüpfung bleibt beim RESET der Regeln erhalten.
4. Test starten:

```sh
# 12 leicht lesbare Beispiele als Broadcast, wie beim ESP32
python3 tests/udp_viewer_filter_test.py --broadcast --suite examples

# Vollständiger Test: 12 Beispiele plus 512 Kombinationen
python3 tests/udp_viewer_filter_test.py --broadcast
```

Die Standardmatrix enthält alle Teilmengen von `ADC`, `PCF`, `CL57TE`, `bench`, `scope`, `DEBUG`, `Heartbeat`, `ERROR`, `WARN`, einschließlich einer neutralen Zeile ohne diese Begriffe. Jede Nachricht trägt `[MANUAL]`, eine Laufkennung `run=HHMMSS` und eine fortlaufende `id`. Die Beispiele enthalten auch UTF-8-Zeichen (`überhöht`, `°C`, `✓`).

Ohne `--broadcast` sendet das Skript standardmäßig **UDP-Unicast an `127.0.0.1`**. Mit `--broadcast` wird im lokalen Netz an `255.255.255.255` gesendet; eine angegebene `--host`-Adresse wird dabei ersetzt.

## Alle Parameter

| Parameter | Standard | Wirkung |
| --- | --- | --- |
| `--host ADRESSE` | `127.0.0.1` | IPv4-Zieladresse oder auf IPv4 auflösbarer Hostname des Viewers; nicht `0.0.0.0`. |
| `--port PORT` | `10514` | Zielport von 1 bis 65535. Muss mit dem Viewer übereinstimmen. |
| `--protocol udp\|tcp` | `udp` | Transport auswählen; Viewer entsprechend einstellen. |
| `--broadcast` | aus | UDP-Broadcast an `255.255.255.255`; nicht mit TCP kombinierbar. |
| `--suite examples\|matrix\|all` | `all` | 12 Beispiele, Kombinationsmatrix oder beides. |
| `--terms BEGRIFF ...` | neun Begriffe oben | Eigene Matrix aus maximal 10 verschiedenen, nichtleeren Begriffen; bei N Begriffen entstehen 2^N Zeilen. Beispiele bleiben unverändert. |
| `--interval SEKUNDEN` | `0.05` | Pause nach jeder Nachricht; bei TCP `batch` nach jedem gesamten Durchlauf. Null ist erlaubt. |
| `--repeat ANZAHL` | `1` | Gesamte Suite mehrfach senden; TCP behält dabei dieselbe Verbindung. IDs und Laufkennung wiederholen sich. |
| `--tcp-mode lines\|fragmented\|batch` | `lines` | Je Zeile senden, jede Zeile in zwei Schreibvorgänge teilen oder alle Zeilen eines Durchlaufs gemeinsam schreiben. Bei UDP ohne Wirkung. |
| `--line-ending lf\|crlf\|none` | `lf` | Zeilenabschluss wählen; `none` ist nur bei UDP erlaubt. |
| `--filter BEGRIFF ...` | keine | Separate Include-Substring-Slots zur Berechnung erwarteter Treffer. |
| `--filter-op AND\|OR` | `AND` | Verknüpfung der vorhergesagten Include-Slots. |
| `--exclude BEGRIFF ...` | keine | Separate Exclude-Substring-Slots zur Berechnung erwarteter Treffer. |
| `--exclude-op AND\|OR` | `OR` | Verknüpfung der vorhergesagten Exclude-Slots. |
| `--list` | aus | Eine Suite mit ANZEIGEN/AUSBLENDEN-Vorhersage ausgeben, nichts senden. Bei `--repeat` wird die Liste nicht wiederholt. |
| `--self-test` | aus | Generierung und grundlegende Filtervorhersage intern prüfen; kein Viewer-/Netzwerktest. |
| `-h`, `--help` | — | Hilfe anzeigen. |

**Die Filterargumente konfigurieren den Viewer nicht und reduzieren nicht die Sendemenge.** Trage die Begriffe selbst als einzelne Slots im Modus **Substring** ein und wähle dieselben Operatoren. Die Vorhersage verwendet exakte Groß-/Kleinschreibung. Regex, mehrere Suchbegriffe innerhalb eines Slots und Filter auf Laufkennung/ID sind nicht Gegenstand der folgenden Zähltabelle.

## Filter und Exclude prüfen

Für jeden Tabellenfall im Viewer die angegebenen Regeln setzen, nach Ende des vorherigen Laufs CLEAR drücken und die Matrix erneut senden:

```sh
python3 tests/udp_viewer_filter_test.py --broadcast --suite matrix
```

| Include-Slots | Filter-Verknüpfung | Exclude-Slots | Exclude-Verknüpfung | Gesendet | Tatsächlich angezeigt | Ausgeblendet |
| --- | --- | --- | --- | ---: | ---: | ---: |
| keine | AND oder OR | keine | AND oder OR | 512 | 512 | 0 |
| ADC | AND oder OR | keine | beliebig | 512 | 256 | 256 |
| ADC, PCF | OR | keine | beliebig | 512 | 384 | 128 |
| ADC, PCF | AND | keine | beliebig | 512 | 128 | 384 |
| CL57TE, bench | AND | keine | beliebig | 512 | 128 | 384 |
| ERROR, WARN | OR | keine | beliebig | 512 | 384 | 128 |
| keine | beliebig | DEBUG, Heartbeat | OR | 512 | 128 | 384 |
| keine | beliebig | DEBUG, Heartbeat | AND | 512 | 384 | 128 |
| keine | beliebig | CL57TE, scope | AND | 512 | 384 | 128 |
| ADC, PCF | OR | DEBUG, Heartbeat | AND | 512 | **288** | 224 |
| ADC, PCF | AND | DEBUG, Heartbeat | AND | 512 | **96** | 416 |
| ADC, PCF | OR | DEBUG, Heartbeat | OR | 512 | **96** | 416 |
| ADC, PCF | AND | DEBUG, Heartbeat | OR | 512 | **32** | 480 |
| ADC | beliebig | ADC | beliebig | 512 | 0 | 512 |

**So liest du die Tabelle:** Von 512 gesendeten und vollständig empfangenen Nachrichten werden die unter „Tatsächlich angezeigt“ genannten Nachrichten nach Anwendung beider Regelgruppen sichtbar. „Ausgeblendet“ umfasst sowohl Nachrichten ohne Include-Treffer als auch Nachrichten mit Exclude-Treffer. Beide Spalten ergeben zusammen 512; dies sind Sollzahlen für den manuellen Vergleich, keine automatisch gemessenen Ergebnisse.

Die Zahlen gelten für die **Standardmatrix mit 512 Zeilen**, einen Durchlauf und unveränderte Regeln während des Laufs. UI-Meldungen zählen nicht dazu. Exclude gewinnt gegenüber Include. Ohne aktive Include-Regeln wird alles zugelassen; ohne Exclude-Regeln nichts ausgeschlossen. Bei genau einer aktiven Regel wirken AND und OR gleich.

Beispiel: Filter `ADC OR PCF` lässt 384 der 512 Nachrichten zu. Exclude `DEBUG AND Heartbeat` entfernt davon die 96 Nachrichten, die beide Ausschlussbegriffe enthalten. Somit werden **288 Nachrichten angezeigt und insgesamt 224 ausgeblendet**. Um jede Nachricht mit DEBUG oder Heartbeat zu entfernen, muss Exclude auf **OR** stehen; dann werden bei demselben Filter **96 angezeigt und 416 ausgeblendet**.

Beispiele mit passender Vorhersage im Terminal:

```sh
# Von 512 Nachrichten: 96 angezeigt, 416 ausgeblendet
python3 tests/udp_viewer_filter_test.py --broadcast --suite matrix \
  --filter ADC PCF --filter-op OR \
  --exclude DEBUG Heartbeat --exclude-op OR

# Nur CL57TE bench: von 512 Nachrichten 128 angezeigt, 384 ausgeblendet
python3 tests/udp_viewer_filter_test.py --broadcast --suite matrix \
  --filter CL57TE bench --filter-op AND

# CL57TE scope ausschließen: von 512 Nachrichten 384 angezeigt, 128 ausgeblendet
python3 tests/udp_viewer_filter_test.py --broadcast --suite matrix \
  --exclude CL57TE scope --exclude-op AND

# Kleine Matrix: von 8 Nachrichten 2 angezeigt, 6 ausgeblendet
python3 tests/udp_viewer_filter_test.py --broadcast --suite matrix \
  --terms ADC PCF DEBUG --filter ADC PCF --filter-op AND
```

## Transport und Nachrichtenabgrenzung

```sh
# Lokal auf demselben Rechner, Unicast
python3 tests/udp_viewer_filter_test.py --suite examples

# Anderer Rechner: Beispiel-IP durch die tatsächliche Viewer-IP ersetzen
python3 tests/udp_viewer_filter_test.py --host 192.168.0.193 --port 10514 --suite examples

# UDP benötigt keinen abschließenden Zeilenumbruch
python3 tests/udp_viewer_filter_test.py --broadcast --suite examples --line-ending none

# Windows-Zeilenabschluss
python3 tests/udp_viewer_filter_test.py --broadcast --suite examples --line-ending crlf

# TCP: Viewer vorher trennen, auf TCP stellen und erneut CONNECT wählen
python3 tests/udp_viewer_filter_test.py --protocol tcp --suite examples

# Teilnachrichten, einschließlich geteilter UTF-8-Zeichen
python3 tests/udp_viewer_filter_test.py --protocol tcp --suite examples --tcp-mode fragmented

# Mehrere Zeilen in einem Schreibvorgang, mit CRLF
python3 tests/udp_viewer_filter_test.py --protocol tcp --suite examples \
  --tcp-mode batch --line-ending crlf
```

TCP kann Schreibvorgänge intern zusammenfassen oder weiter aufteilen. `fragmented` und `batch` testen unterschiedliche Schreibmuster, garantieren aber keine bestimmte Aufteilung beim Empfang. Der Viewer soll in allen drei Modi dieselben vollständigen Zeilen anzeigen. TCP verwendet konkrete Zieladressen, keinen Broadcast. Nach Skriptende soll der Viewer wieder auf einen Sender warten; ein erneuter Aufruf prüft die Wiederverbindung.

## Tempo, Wiederholung und Bedienung

```sh
# Langsamer Lauf für Änderungen während des Empfangs
python3 tests/udp_viewer_filter_test.py --broadcast --interval 0.5

# 120 Beispielnachrichten; bei TCP bleibt eine Verbindung bestehen
python3 tests/udp_viewer_filter_test.py --protocol tcp --suite examples --repeat 10

# Höhere UDP-Senderate; Verluste sind möglich
python3 tests/udp_viewer_filter_test.py --broadcast --suite matrix --interval 0.01

# Vorschau ohne Netzwerk, mit Filtervorhersage
python3 tests/udp_viewer_filter_test.py --suite matrix --filter ADC PCF --filter-op OR --list

# Interne Prüfung und vollständige Hilfe
python3 tests/udp_viewer_filter_test.py --self-test
python3 tests/udp_viewer_filter_test.py --help
```

Zusätzlich manuell prüfen:

- Während eines langsamen Laufs AND/OR umschalten: neue Zeilen folgen der neuen Auswahl; alte Zeilen werden nicht rückwirkend geändert.
- Regeln hinzufügen/entfernen und Filter-/Exclude-RESET betätigen: Operator bleibt erhalten. Leere Slots beeinflussen die Verknüpfung nicht.
- Viewer schließen und neu starten: beide Operatoren werden wiederhergestellt.
- PAUSE/RESUME prüfen: die Logansicht pausiert, die Live-Protokollierung läuft weiter; nach RESUME wird der begrenzte Pausenpuffer angezeigt.
- CLEAR leert die sichtbare Anzeige; Sitzungs-RESET beendet den Empfang und setzt Sitzung/Visualizer zurück. Danach neu verbinden und das Skript erneut starten.
- Für die Ein-Sender-Regel einen langsamen TCP-Lauf starten und in einem zweiten Terminal einen weiteren TCP-Aufruf ausführen. Der zweite Sender soll abgewiesen werden; der erste muss weiterarbeiten. Ein erfolgreicher lokaler Schreibaufruf beweist nicht, dass der Server den zweiten Sender akzeptiert hat.

## Ergebnis richtig beurteilen

- UDP: bei vollständigem Empfang eine Erhöhung von `pkts` um 12 (`examples`), 512 (`matrix`) oder 524 (`all`) je Standarddurchlauf, unabhängig von Filtern. `lines` zählt empfangene nichtleere Zeilen vor den Anzeigefiltern.
- TCP: `bytes` zählt empfangene Bytes, `lines` vollständige nichtleere Zeilen. UTF-8 und LF/CRLF beeinflussen die Bytezahl. TCP-Schreibvorgänge sind keine Paketzähler.
- Nur neue `[MANUAL]`-Zeilen des jeweiligen Laufs vergleichen. `shown` enthält auch andere Nachrichten; bestehende Zeilen und UI-Meldungen verfälschen einen direkten Vergleich.
- Die Live-Datei enthält die durch Filter/Exclude zugelassenen Live-Zeilen. UI-Diagnosen können zusätzlich enthalten sein. Visualizer erhalten ihre Eingaben unabhängig von diesen Regeln.
- Dieses Skript enthält **keine passenden Plot-/Logic-CSV-Datensätze**. Es prüft daher keine Visualizer-Kurven oder Logic-Zustände. Ebenso werden Größenlimit, ungültiges UTF-8 und ein unvollständiger TCP-Rest beim Abbruch nicht gezielt erzeugt.
- Eine erfolgreiche Sendemeldung bestätigt die Übergabe an das Betriebssystem, nicht den Empfang. Besonders UDP kann Pakete verlieren.
- Bleibt `pkts` unverändert: Protokoll, Zieladresse, Port, CONNECT und parallele Viewer prüfen. Steigt `pkts`, aber es erscheint nichts: Filter, Exclude und PAUSE prüfen. Broadcast wird im lokalen Netz verteilt; `127.0.0.1` erreicht ausschließlich denselben Rechner.

Abbruch des Skripts mit `Ctrl+C`. Die angegebenen Nachrichten werden im normalen Betrieb auch in die Live-Datei des Viewers geschrieben, soweit die Regeln sie zulassen.
