# Simulation Referenz

Dieses Dokument beschreibt die aktuell implementierte Simulationslogik des UDP-Viewers mit Fokus auf die PLOT-Temperatursimulation.

Stand der Beschreibung:

- Codebasis `0.16.0`
- relevante Implementierung in [replay_simulation.py](../src/udp_log_viewer/replay_simulation.py)

## 1. Zweck

Die Simulation dient dazu, ohne reales Zielsystem plausibel wirkende Testdaten fuer:

- Text-Logs
- Temperatur-PLOTs
- Logic-Signale

zu erzeugen.

Fuer die Temperatursimulation ist das Ziel ausdruecklich nicht ein physikalisch exaktes Ofenmodell, sondern ein praxistaugliches Testprofil mit:

- nachvollziehbarem Aufheizverhalten
- Traegheit des Trocknungsraums
- schneller reagierendem HotSpot nahe der Heizspirale
- zufaelligen `DOOR_OPEN`-Phasen
- Heater-Cutoff bei `150 °C` HotSpot

## 2. Relevante Code-Stellen

- [replay_simulation.py](../src/udp_log_viewer/replay_simulation.py)
  enthaelt Replay-Beispiele und die eigentliche Simulationslogik
- [main.py](../src/udp_log_viewer/main.py)
  startet die Timer und injiziert die erzeugten Simulationszeilen in den normalen Verarbeitungsweg
- [config_store.py](../src/udp_log_viewer/data_visualizer/config_store.py)
  liefert passende Default-Konfigurationen fuer `CSV_CLIENT_PLOT` und `CSV_HOST_PLOT`

## 3. Simulationsarten

Aktuell existieren drei voneinander getrennte Simulationspfade:

### 3.1 Text-Simulation

Erzeugt allgemeine Logzeilen wie:

- `[HOST/INFO]`
- `[OVEN/INFO]`
- `[HEATER/INFO]`
- `[UI/DEBUG]`

Die Text-Simulation arbeitet mit einem einfachen Zustand fuer:

- `seq`
- `ntc`
- `core`
- `target`
- `heater`
- `mask`

### 3.2 Temperatur-PLOT-Simulation

Die Temperatursimulation ist die wichtigste Simulationsart fuer Plot-Fenster.

Sie erzeugt pro Tick zwei zusammengehoerende CSV-Zeilen:

- `CSV_CLIENT_PLOT`
- `CSV_HOST_PLOT`

Beide Zeilen basieren auf demselben Simulationszustand. Dadurch entsprechen `Chamber` und `HotSpot` in beiden Formaten immer demselben internen Berechnungsstand.

### 3.3 Logic-Simulation

Erzeugt einfache binäre Kanalwerte fuer:

- `CSV_CLIENT_LOGIC`
- `CSV_HOST_LOGIC`

## 4. Temperatur-Simulationszustand

Der Temperaturzustand wird in `TemperaturePlotSimulationState` gehalten.

Aktuelle Felder:

- `seq`
  laufender Tick-Zaehler
- `chamber`
  Temperatur des Trocknungsraums
- `hotspot`
  Temperatur nahe der Heizspirale
- `target`
  Solltemperatur
- `heater_on`
  Heater aktiv oder nicht
- `door_open`
  simulierte Tuer offen
- `state`
  einfacher Zustandswert fuer die Ausgabe
- `heater_ticks_remaining`
  Restlaufzeit des aktuellen Heizimpulses
- `rest_ticks_remaining`
  Sperrzeit bis zum naechsten Einschalten
- `door_ticks_remaining`
  Restdauer einer offenen Tuersituation

## 5. Temperatur-Simulationsablauf

Die Hauptlogik liegt in:

- [replay_simulation.py](../src/udp_log_viewer/replay_simulation.py#L121)

Ein Tick durchlaeuft vereinfacht diese Schritte:

1. `seq` erhoehen
2. pruefen, ob eine `DOOR_OPEN`-Phase aktiv ist oder neu startet
3. Heater-Entscheidung treffen
4. Temperaturen fuer `Chamber` und `HotSpot` fortschreiben
5. Grenzen und Cutoff anwenden
6. `state` setzen
7. `CSV_CLIENT_PLOT` und `CSV_HOST_PLOT` erzeugen

## 6. Modellidee fuer Chamber und HotSpot

Die aktuelle Modellannahme ist:

- `HotSpot` reagiert schneller, weil er nahe an der Heizquelle sitzt
- `Chamber` reagiert traeger, weil der gesamte Trocknungsraum thermische Masse hat
- nach Heater-`OFF` kann `Chamber` kurz weiter steigen, weil Restwaerme aus dem HotSpot in den Raum wandert
- bei `DOOR_OPEN` faellt `Chamber` Richtung Umgebung ab, `HotSpot` faellt ebenfalls, aber mit eigener Dynamik

Die Heizung arbeitet nicht als saubere PID-Regelung, sondern als einfacher Impuls-/Pausen-Mechanismus mit Mindestlaufzeit und Sperrzeit.

## 7. Ausgabeformate

### 7.1 `CSV_CLIENT_PLOT`

Format:

```text
[CSV_CLIENT_PLOT];<rawHot>;<hot_mV>;<Thot>;<rawChamber>;<chamberMilliVolts>;<Tch>;<heater_on>;<door_open>;<state>
```

Beispiel:

```text
20260329-21:05:36.431 [CSV_CLIENT_PLOT];248;2728;248;230;2530;230;1;0;1
```

Bedeutung:

- `rawHot`
- `hot_mV`
- `Thot`
- `rawChamber`
- `chamberMilliVolts`
- `Tch`
- `heater_on`
- `door_open`
- `state`

### 7.2 `CSV_HOST_PLOT`

Format:

```text
[CSV_HOST_PLOT];<chamber_temp>;<hotspot_temp>;<target_temp>;<temp_min,temp_max>;<state>
```

Beispiel:

```text
20260329-21:05:36.431 [CSV_HOST_PLOT];230;248;600;570,650;1
```

Bedeutung:

- `chamber_temp`
- `hotspot_temp`
- `target_temp`
- `temp_min,temp_max`
- `state`

Wichtig:

- `temp_min,temp_max` ist ein einzelnes CSV-Feld
- dieses Feld ist aktuell im Plot-Parser bewusst `non-numeric`
- `Tch` und `Thot` im Host-Plot entsprechen denselben internen Werten wie im Client-Plot

## 8. Zustandslogik

Die Simulation verwendet aktuell folgende Zustandswerte:

- `0`
  Heizung aus, noch nicht im Zielbereich
- `1`
  Heizung aktiv
- `2`
  Chamber liegt im Zielbereich
- `3`
  Door-Open-Situation

Diese Werte sind einfache Simulationszustände, keine dokumentierte externe Protokollspezifikation.

## 9. Tuning-Parameter

Die wichtigsten Stellwerte sind momentan lokale Variablen direkt in
[replay_simulation.py](../src/udp_log_viewer/replay_simulation.py#L121).

### 9.1 Grundparameter

- `ambient = 22.0`
  Umgebungstemperatur
- `cut_off_temperature = 150.0`
  harter Heater-Cutoff fuer den HotSpot
- `target_band = 1.5`
  Bereich um die Solltemperatur, ab dem der Heater frueher abgeschaltet werden kann

### 9.2 Tuer-Simulation

- Startwahrscheinlichkeit:
  `random.random() < 0.035`
- Dauer:
  `random.randint(6, 14)`

Damit entstehen unregelmaessige `DOOR_OPEN`-Phasen.

### 9.3 Heater-Timing

- Restzeit nach Door-Open:
  `max(..., 6)`
- Restzeit nach HotSpot-Cutoff:
  `max(..., 10)` oder spaeter `max(..., 12)`
- Restzeit nach normalem Ausschalten:
  `random.randint(8, 14)`
- Einschaltbedingung:
  `state.chamber < state.target - 2.5`
- Einschaltimpuls:
  `random.randint(6, 12)`

### 9.4 Chamber-Heizanstieg

Beim Heizen:

```text
chamber_gain = 0.16 + min(target_gap * 0.012, 0.36) + random.uniform(-0.02, 0.04)
```

Wirkung:

- `0.16`
  Grundanstieg
- `target_gap * 0.012`
  staerkerer Anstieg bei grossem Abstand zur Zieltemperatur
- `cap 0.36`
  Begrenzung des Zusatzanstiegs
- `random.uniform(-0.02, 0.04)`
  leichte Varianz

### 9.5 HotSpot-Heizanstieg

Beim Heizen:

```text
hotspot_target_gain = chamber_gain * (1.18 + random.uniform(0.00, 0.10))
hotspot_bias = 0.05 + min(target_gap * 0.005, 0.10)
```

Wirkung:

- `1.18 .. 1.28`
  HotSpot steigt proportional steiler als Chamber
- `hotspot_bias`
  zusaetzlicher Aufschlag, damit der HotSpot die Chamber sichtbar ueberholt

Zusaetzlich wird der reale Anstieg beim Heizen noch begrenzt auf:

```text
min_hotspot_rise = chamber_rise * 1.15
max_hotspot_rise = chamber_rise * 1.28
```

Das bedeutet:

- HotSpot soll mindestens `15 %` schneller steigen als Chamber
- HotSpot soll hoechstens `28 %` schneller steigen als Chamber

### 9.6 Verhalten bei Heater-OFF

Im Off-Betrieb gilt:

- `Chamber` kuehlt nur langsam aus
- Restwaerme aus dem HotSpot kann `Chamber` noch kurz weiter anheben
- `HotSpot` kuehlt schneller in Richtung `Chamber` und `ambient`

### 9.7 Verhalten bei Door-Open

Bei geoeffneter Tuer:

- Heater wird sofort deaktiviert
- `Chamber` bewegt sich staerker in Richtung `ambient`
- `HotSpot` faellt ebenfalls, aber gekoppelt an `Chamber` und Umgebung

## 10. Harte Grenzen

Aktuell werden diese Grenzen angewendet:

- `Chamber` zwischen `18.0` und `90.0`
- `HotSpot` mindestens `Chamber - 2.0`
- `HotSpot` maximal `150.0`

Bei `HotSpot >= 150.0` gilt:

- Heater sofort `OFF`
- `heater_ticks_remaining = 0`
- verlaengerte Restzeit bis zum naechsten Heizimpuls

## 11. Warum Chamber nicht exakt auf der Target-Linie liegt

Die Simulation ist bewusst nicht als perfekte Regelung implementiert.

`Chamber` soll:

- die `target`-Linie ansteuern
- ihr aber nicht mathematisch exakt pro Tick folgen
- leicht ueber- oder unterschwingen duerfen
- durch Restwaerme und Pausen traeg reagieren

Dadurch wirkt die Kurve eher wie ein realer Ofen als wie eine direkt gekoppelte Soll-Ist-Funktion.

## 12. Typische Anpassungen

Wenn die Simulation angepasst werden soll, sind diese Stellschrauben in der Regel die wichtigsten:

### HotSpot steiler machen

- Multiplikator in `hotspot_target_gain` erhoehen
- `hotspot_bias` erhoehen
- `min_hotspot_rise` und `max_hotspot_rise` anheben

### Chamber traeger machen

- `chamber_gain` verkleinern
- Off-Kopplung `max(0.0, state.hotspot - state.chamber) * 0.030` reduzieren

### Zieltemperatur genauer treffen

- `target_band` verkleinern
- Einschaltbedingung und Restzeiten enger machen

### Mehr Overshoot

- Restzeiten nach normalem Heater-`OFF` verkuerzen
- Chamber-Off-Anteil aus HotSpot-Restwaerme vergroessern

### Mehr Schutz gegen Ueberhitzung

- Abschaltbedingung frueher machen
- `cut_off_temperature` senken
- Restzeit nach Cutoff vergroessern

## 13. Bekannte Vereinfachungen

Die Simulation bildet aktuell nicht ab:

- echte PID-Regelung
- mehrere Heizleistungen oder PWM-Stufen
- unterschiedliche Rezeptphasen
- separate Sensorfehler
- exakte thermodynamische Materialmodelle

Sie ist bewusst ein gut abstimmbares Heuristikmodell.

## 14. Erweiterungsempfehlung

Falls die Simulation haeufig weiter getunt wird, ist der naechste sinnvolle Schritt:

- die lokalen Stellwerte in eine benannte `SimulationTuning`-Dataclass auszulagern
- die Dokumentation direkt an diese Struktur zu koppeln

Dann lassen sich spaetere Anpassungen an `HotSpot`, `Chamber`, `Door-Open`, `Cutoff` und `Target` sauberer pflegen.
