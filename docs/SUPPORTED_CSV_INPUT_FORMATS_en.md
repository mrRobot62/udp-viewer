# Supported CSV Input Formats for UDP Viewer

This document does not define the sender-side protocol.

It only documents which CSV-like input lines UDP Viewer currently
recognizes, how those lines are routed to visualizers, and how fields
are interpreted inside the application.

## 1. Core Rule

The visualizer accepts a CSV-like line only if:

1. a `VisualizerConfig` is active
2. the line contains a recognizable filter token such as `[CSV_TEMP]`
   or `[CSV_LOGIC]`
3. that token matches the visualizer `filter_string` exactly
4. the data field count matches the configured field count exactly

## 2. Accepted Layout Variants

The parser currently tolerates several layouts.

### Variant A

```text
<timestamp> ; [CSV_TEMP] ; <field1> ; <field2> ; ...
```

### Variant B

```text
<timestamp>;[CSV_TEMP];<field1>;<field2>;...
```

### Variant C

```text
<timestamp> [CSV_TEMP];<field1>;<field2>;...
```

### Variant D

```text
[CSV_TEMP];<field1>;<field2>;...
```

## 3. Whitespace Handling

Whitespace around semicolons is tolerated and ignored by the parser.

## 4. Routing Through `filter_string`

Each visualizer has a `filter_string`, for example:

- `[CSV_TEMP]`
- `[CSV_LOGIC]`

The token must match exactly.

That means:

- `[CSV_TEMP]` does not match `[CSV_OTHER]`
- `CSV_TEMP` without brackets does not match `[CSV_TEMP]`
- case and character sequence must match exactly

## 5. Field Count

The incoming data field count must match the configured visualizer field
count exactly.

If it does not, the line is rejected for that visualizer.

## 6. Numeric Interpretation

For each configured field:

- empty input becomes `None`
- `numeric = false` prevents numeric parsing
- numeric fields are parsed using `float()`
- the parsed value is divided by `scale`

If `scale <= 0`, the application internally falls back to `1`.

## 7. Failure Behavior

A line is rejected for a visualizer when:

- no supported filter token is found
- the token does not match `filter_string`
- the field count does not match

If a single numeric field cannot be converted, that field may become
`None` while the rest of the line is still accepted, as long as the line
otherwise matches structurally.

## 8. Default Plot Profile Example

The application ships with a default temperature-oriented profile such
as:

- title: `CSV_TEMP Graph`
- filter: `[CSV_TEMP]`

Typical fields:

1. `rawHot`
2. `hot_mV`
3. `Thot`
4. `rawChamber`
5. `chamberMilliVolts`
6. `Tch`
7. `heater_on`
8. `door_open`
9. `state`

## 9. Default Logic Profile Example

The application also ships with a default logic profile:

- title: `Logic Graph`
- filter: `[CSV_LOGIC]`

Typical channels:

1. `ch0`
2. `ch1`
3. `ch2`
4. `ch3`
5. `ch4`
6. `ch5`
7. `ch6`
8. `ch7`

## 10. Important Boundary

UDP Viewer does not define the sender system.

The sender remains authoritative for the semantic meaning of each CSV
field. UDP Viewer can only visualize that data when:

- `filter_string` matches
- field count matches
- field meaning is configured correctly in the visualizer

## 11. Relevant Source Files

- [csv_log_parser.py](../src/udp_log_viewer/data_visualizer/csv_log_parser.py)
- [config_store.py](../src/udp_log_viewer/data_visualizer/config_store.py)
- [visualizer_config.py](../src/udp_log_viewer/data_visualizer/visualizer_config.py)
- [visualizer_field_config.py](../src/udp_log_viewer/data_visualizer/visualizer_field_config.py)
