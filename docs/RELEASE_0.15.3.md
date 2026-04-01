# Release 0.15.3

Release date: 2026-03-31

## Summary

Version `0.15.3` focuses on bugfixing and usability improvements for plot and logic visualization, log-file handling, project-scoped artifact management, and visualizer configuration workflows.

## Highlights

- improved latest-value rendering in plot windows to reduce label overlap
- multi-line plot tooltips for better readability
- hover support in plot windows with horizontal guide line and cross cursor
- configurable default log folder via `Preferences > Log Path`
- runtime-only `PROJECT` mode with a root folder, automatic project subfolder creation, and project-based file naming
- refined `PROJECT` dialog sizing and validation for longer names and long output paths
- clearer live-log and save-path reporting in the main window
- `APPLY` support in plot and logic config dialogs
- corrected slot-change handling so save/discard prompts only appear for real edits
- terminology update from `Temperature` to `Plot` in the user-facing plot UI
- corrected host plot simulation output to use `target_min` and `target_max`

## Included Fixes

- `SAVE` now opens with an explicit path based on the configured log folder
- disconnect-save flow keeps the save confirmation visible in the status bar
- live session logs follow the configured `Log Path`
- host plot legacy filter aliases such as `CSV_CLIENT_TEMP` and `CSV_HOST_TEMP` are normalized on load
- plot and logic dialogs now place `CANCEL | APPLY | SAVE` on the right side
- plot and logic graph windows use a wider `Window Size` field
- project dialogs use English tooltips and show the effective project output folder

## Validation

The release was validated with the automated test suites used during the bugfix thread, including project runtime helpers, visualizer slot/config behavior, parser consistency, preferences persistence, settings persistence, and sliding-window behavior.

## Packaging

- macOS artifact: DMG via `./build_dmg.sh`
- Windows artifact: Setup EXE via the existing GitHub Actions release workflow

## Related Files

- [CHANGELOG.md](../CHANGELOG.md)
- [BUILD_AND_PACKAGING_REFERENCE_en.md](../docs/BUILD_AND_PACKAGING_REFERENCE_en.md)
- [BUILD_AND_PACKAGING_REFERENCE_de.md](../docs/BUILD_AND_PACKAGING_REFERENCE_de.md)
