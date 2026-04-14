# Unterstützte CSV-Eingabeformate des UDP-Viewers

Dieses Dokument beschreibt nicht das führende Protokoll des Sendesystems.

Es beschreibt ausschließlich, welche CSV-artigen Eingabezeilen der UDP-Viewer aktuell erkennt, wie er diese Zeilen dem richtigen Visualizer zuordnet und wie Feldwerte innerhalb des Viewers interpretiert werden.

## 1. Grundprinzip

Der UDP-Viewer verarbeitet CSV-artige Logzeilen im Visualizer nur dann, wenn:

1. ein `VisualizerConfig` aktiv ist
2. die Zeile einen erkennbaren Filter-Token wie `[CSV_TEMP]` oder `[CSV_LOGIC]` enthält
3. dieser Filter-Token exakt zum `filter_string` des Visualizers passt
4. die Anzahl der Datenfelder exakt der Anzahl der konfigurierten Felder entspricht

Wenn eine dieser Bedingungen nicht erfüllt ist, wird die Zeile für diesen Visualizer verworfen.

## 2. Unterstützte Grundvarianten

Der Parser toleriert aktuell mehrere Layouts.

### Variante A

```text
<timestamp> ; [CSV_TEMP] ; <field1> ; <field2> ; ...
```

Beispiel:

```text
20260323-22:32:19.277;[CSV_TEMP];0;0;1207;0;0;517;1;1;2
```

### Variante B

```text
<timestamp>;[CSV_TEMP];<field1>;<field2>;...
```

Beispiel:

```text
20260323-22:32:19.277;[CSV_TEMP];0;0;1207;0;0;517;1;1;2
```

### Variante C

```text
<timestamp> [CSV_TEMP];<field1>;<field2>;...
```

Beispiel:

```text
20260323-22:32:19.528 [CSV_TEMP];0;0;1218;0;0;521;1;1;2
```

### Variante D

```text
[CSV_TEMP];<field1>;<field2>;...
```

Beispiel:

```text
[CSV_TEMP];0;0;1231;0;0;523;1;1;2
```

## 3. Leerzeichenverhalten

Leerzeichen vor und nach dem Semikolon werden toleriert und beim Parsen ignoriert.

Beispiel:

```text
20260323-22:32:19.403 ; [CSV_TEMP] ; 0 ; 0 ; 1213 ; 0 ; 0 ; 518 ; 1 ; 1 ; 2
```

## 4. Routing über `filter_string`

Jeder Visualizer besitzt einen `filter_string`.

Beispiele:

- `[CSV_TEMP]`
- `[CSV_LOGIC]`

Nur wenn der erkannte Filter-Token exakt diesem Wert entspricht, wird die Zeile in einen `VisualizerSample` überführt.

Das bedeutet:

- `[CSV_TEMP]` passt nicht auf `[CSV_OTHER]`
- `CSV_TEMP` ohne Klammern passt nicht auf `[CSV_TEMP]`
- Groß-/Kleinschreibung und Zeichenfolge müssen exakt stimmen

## 5. Feldanzahl

Die Anzahl der empfangenen Datenfelder muss exakt zur Anzahl der konfigurierten `fields` im Visualizer passen.

Wenn die Feldanzahl nicht passt, wird die Zeile verworfen.

Beispiel:

- Visualizer erwartet 9 Felder
- Zeile enthält nur 8 Felder
- Ergebnis: keine Übernahme in den Plot

## 6. Numerische Interpretation

Für jedes konfigurierte Feld gilt:

- leere Eingabefelder werden als `None` behandelt
- Felder mit `numeric = false` werden nicht numerisch interpretiert
- numerische Felder werden mit `float()` gelesen
- der gelesene Wert wird durch `scale` geteilt

Beispiel:

- Rohwert `1213`
- `scale = 10`
- dargestellter Wert `121.3`

Wenn `scale <= 0` wäre, verwendet der Viewer intern den Normalwert `1`.

## 7. Verhalten bei Fehlern

Eine Zeile wird für einen Visualizer verworfen, wenn:

- kein unterstützter Filter-Token erkannt wird
- der Filter-Token nicht zum `filter_string` passt
- die Feldanzahl nicht passt
- ein numerischer Wert nicht in `float` umgewandelt werden kann

Im letzten Fall wird nur das betroffene Feld als `None` gespeichert, sofern die Zeile ansonsten formal passt.

## 8. Beispiel: Standardprofil `[CSV_TEMP]`

Der Viewer bringt standardmäßig ein Temperaturprofil mit:

- Titel: `CSV_TEMP Graph`
- Filter: `[CSV_TEMP]`

Standardfelder:

1. `rawHot`
2. `hot_mV`
3. `Thot`
4. `rawChamber`
5. `chamberMilliVolts`
6. `Tch`
7. `heater_on`
8. `door_open`
9. `state`

Typische Skalierungen:

- `Thot` und `Tch` mit `scale = 10`
- Zustandswerte meist mit `scale = 1`

## 9. Beispiel: Standardprofil `[CSV_LOGIC]`

Der Viewer bringt standardmäßig ein Logic-Profil mit:

- Titel: `Logic Graph`
- Filter: `[CSV_LOGIC]`

Standardfelder:

1. `ch0`
2. `ch1`
3. `ch2`
4. `ch3`
5. `ch4`
6. `ch5`
7. `ch6`
8. `ch7`

Diese Felder werden im Logic-Visualizer als Kanäle interpretiert.

## 10. Wichtige Abgrenzung

Der UDP-Viewer definiert das Sendesystem nicht.

Das Sendesystem darf seine CSV-Zeilenstruktur weiterhin selbst festlegen. Der Viewer kann diese Daten nur dann visualisieren, wenn:

- der gewählte `filter_string` passt
- die Feldanzahl mit der Visualizer-Konfiguration übereinstimmt
- die Feldbedeutung im Visualizer korrekt hinterlegt ist

Praktisch bedeutet das:

- das Sendesystem bleibt führend für die Semantik
- der UDP-Viewer bildet diese Struktur über die Graph-Konfiguration nach
- die Viewer-Dokumentation beschreibt nur die aktuelle Eingabeinterpretation

## 11. Abgrenzung zu Footer-Parametern

Footer-Platzhalter wie `{mean:Thot}`, `{avg:Thot}`, `{median:Thot}`,
`{tail_avg:Thot}`, `{thr_avg:Thot}`, `{max:Thot}` oder
`{current:Thot}` sind keine CSV-Felder und nicht Teil des
UDP-Datenstroms.

Diese Werte werden im UDP-Viewer aus den bereits geparsten und aktuell
gerenderten numerischen Plot-Werten berechnet:

- `{current:Feldname}` und `{latest:Feldname}`
  letzter gerenderter Wert der Plot-Serie
- `{mean:Feldname}` und `{avg:Feldname}`
  Mittelwert der aktuell gerenderten numerischen Werte
- `{median:Feldname}`
  Median der aktuell gerenderten numerischen Werte
- `{tail_avg:Feldname}`
  Mittelwert über das letzte Viertel der aktuell sichtbaren Werte
- `{thr_avg:Feldname}`
  Mittelwert nur für Werte innerhalb des Zielkorridors
- `{max:Feldname}`
  Maximalwert der aktuell gerenderten numerischen Werte

Bei aktivem Sliding Window beziehen sich diese Werte auf das sichtbare
Datenfenster. Globale Footer-Werte wie `{samples}`, `{start}`, `{end}`
und `{duration}` beziehen sich dagegen auf den gesamten Slot-Puffer.

## 12. Relevante Quelldateien

- [csv_log_parser.py](../src/udp_log_viewer/data_visualizer/csv_log_parser.py)
- [config_store.py](../src/udp_log_viewer/data_visualizer/config_store.py)
- [visualizer_config.py](../src/udp_log_viewer/data_visualizer/visualizer_config.py)
- [visualizer_field_config.py](../src/udp_log_viewer/data_visualizer/visualizer_field_config.py)
- [visualizer_window.py](../src/udp_log_viewer/data_visualizer/visualizer_window.py)
