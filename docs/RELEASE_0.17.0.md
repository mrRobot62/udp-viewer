# Release 0.17.0

Release date: 2026-04-10

## Summary

Version `0.17.0` significantly expands the visualizer configuration.
The main focus is better color selection, compact user-defined footer
status lines, and centrally managed footer presets.

## Highlights

- plot and logic visualizers now provide 16 clearly distinguishable
  preset colors
- each visualizer color can alternatively be entered as an HTML color
  code in `#RRGGBB` format
- central footer presets are managed under `Preferences` -> `Visualizer`
- footer presets have a name, type (`All`, `Plot`, `Logic`), and format
  string
- preset names are limited to 12 characters to keep dropdowns readable
- plot and logic slot dialogs provide a preset dropdown and individual
  `Footer Format`
- footer status lines are limited to a compact two-line display so long
  status text no longer expands graph windows horizontally

## Footer Placeholders

Global placeholders for plot and logic:

- `{samples}`
  number of all samples in the slot buffer
- `{start}`
  timestamp of the first sample
- `{end}`
  timestamp of the last sample
- `{duration}`
  duration between first and last sample

Internal plot placeholders:

- `{FieldName}`
  current value of the field
- `{current:FieldName}`
  current value of the field
- `{latest:FieldName}`
  alias for `current`
- `{mean:FieldName}`
  average of the currently rendered numeric plot values
- `{avg:FieldName}`
  alias for `mean`
- `{median:FieldName}`
  median of the currently rendered numeric plot values
- `{tail_avg:FieldName}`
  average across the last quarter of the currently visible values
- `{thr_avg:FieldName}`
  average only inside the target band
- `{max:FieldName}`
  maximum of the currently rendered numeric plot values

`mean`, `avg`, `median`, `tail_avg`, `thr_avg`, `max`, `current`, and
`latest` are not values from the UDP data stream. They are calculated
inside UDP Viewer from the currently rendered numeric plot data. With an
active sliding window, they refer to the visible data window.

Logic placeholders:

- `{ch0}`, `{ch1}`, ...
  latest state of the corresponding logic channel

## Formatting

Footer placeholders support Python-style format specs:

- `{samples:04d}`
  integer with leading zeros, e.g. `0007`
- `{Thot:.1f}`
  floating point value with one decimal place
- `{Thot:05.1f}`
  minimum width 5 including the decimal point, e.g. `072.3`
- `{mean:Thot:05.1f}`
  formatted mean value
- `{avg:Thot:05.1f}`
  formatted mean value through the `avg` alias
- `{median:Thot:05.1f}`
  formatted median value
- `{tail_avg:Thot:05.1f}`
  formatted average across the last quarter
- `{thr_avg:Thot:05.1f}`
  formatted average inside the target band
- `{max:Thot:05.1f}`
  formatted maximum value
- `{current:Thot:05.1f}`
  formatted current value
- `{ch0:02.0f}`
  formatted logic value

Note: the width in Python format specs is the total minimum width,
including decimal point and decimals. For `3 digits before the decimal
point + 1 decimal`, `05.1f` is usually appropriate for positive values.

## Validation

The release state was validated with focused automated tests and a
compile check:

- `tests/test_visualizer_footer_status.py`
- `tests/test_visualizer_color_selection.py`
- `tests/test_core_behavior.py`
- `tests/test_preferences_store.py`
- `python -m compileall src/udp_log_viewer`

## Related Files

- [CHANGELOG.md](../CHANGELOG.md)
- [README.md](../README.md)
- [USER_GUIDE_en.md](../docs/USER_GUIDE_en.md)
- [CONFIGURATION_REFERENCE_en.md](../docs/CONFIGURATION_REFERENCE_en.md)
- [SUPPORTED_CSV_INPUT_FORMATS_en.md](../docs/SUPPORTED_CSV_INPUT_FORMATS_en.md)
- [RELEASE_0.17.0_de.md](../docs/RELEASE_0.17.0_de.md)
