# Simulation Reference

This document describes the currently implemented simulation logic of
UDP Viewer, with a special focus on the plot-temperature simulation.

Current basis:

- code line `0.16.0`
- relevant implementation in [replay_simulation.py](../src/udp_log_viewer/replay_simulation.py)

## 1. Purpose

The simulation exists to generate plausible test traffic without a real
sender system for:

- text logs
- plot-temperature data
- logic channels

The temperature model is intentionally practical rather than physically
exact. It aims to create believable test behavior such as:

- visible warm-up
- chamber thermal inertia
- faster hotspot response
- random `DOOR_OPEN` phases
- hotspot safety cutoff near `150 °C`

## 2. Simulation Types

Current simulation paths:

- text simulation
- plot-temperature simulation
- logic simulation

### 2.1 Text simulation

Generates generic log lines such as:

- `[HOST/INFO]`
- `[OVEN/INFO]`
- `[HEATER/INFO]`
- `[UI/DEBUG]`

### 2.2 Plot-temperature simulation

This is the most important simulation path for plot windows.

Each tick emits two related CSV lines:

- `CSV_CLIENT_PLOT`
- `CSV_HOST_PLOT`

Both come from the same internal state, so chamber and hotspot values
remain aligned across the two formats.

### 2.3 Logic simulation

Generates binary channel traffic for:

- `CSV_CLIENT_LOGIC`
- `CSV_HOST_LOGIC`

## 3. Temperature State

The temperature state currently includes:

- `seq`
- `chamber`
- `hotspot`
- `target`
- `heater_on`
- `door_open`
- `state`
- `heater_ticks_remaining`
- `rest_ticks_remaining`
- `door_ticks_remaining`

## 4. Tick Flow

Each simulation tick roughly performs:

1. increment `seq`
2. update door-open state
3. decide heater state
4. update chamber and hotspot temperatures
5. apply limits and cutoff logic
6. assign the exported state code
7. emit `CSV_CLIENT_PLOT` and `CSV_HOST_PLOT`

## 5. Current Model Idea

The main model assumptions are:

- hotspot reacts quickly near the heater
- chamber reacts more slowly
- chamber may continue rising briefly after heater off due to residual heat
- door-open phases cool chamber and hotspot with different dynamics

The heater is not modeled as a full PID controller. The current logic is
closer to pulse and rest timing with simple thresholds.

## 6. Output Formats

### 6.1 `CSV_CLIENT_PLOT`

Format:

```text
[CSV_CLIENT_PLOT];<rawHot>;<hot_mV>;<Thot>;<rawChamber>;<chamberMilliVolts>;<Tch>;<heater_on>;<door_open>;<state>
```

### 6.2 `CSV_HOST_PLOT`

Format:

```text
[CSV_HOST_PLOT];<chamber_temp>;<hotspot_temp>;<target_temp>;<temp_min,temp_max>;<state>
```

Important:

- `temp_min,temp_max` is intentionally one CSV field
- that field is treated as non-numeric in the current plot parser

## 7. State Values

Current exported state meanings:

- `0`: heater off, below target band
- `1`: heater active
- `2`: chamber inside target band
- `3`: door-open condition

These are simulation-side state codes, not a formal external protocol.

## 8. Tuning Areas

The most important tuning values currently live directly inside
[replay_simulation.py](../src/udp_log_viewer/replay_simulation.py).

Relevant categories:

- ambient temperature
- hotspot cutoff temperature
- target band
- random door-open duration and probability
- heater pulse duration and rest duration
- chamber gain while heating
- hotspot gain while heating

## 9. Relevant Source Files

- [replay_simulation.py](../src/udp_log_viewer/replay_simulation.py)
- [main.py](../src/udp_log_viewer/main.py)
- [config_store.py](../src/udp_log_viewer/data_visualizer/config_store.py)
