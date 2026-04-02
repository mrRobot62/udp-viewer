# Release 0.16.1

Release date: 2026-04-01

## Summary

Version `0.16.1` is a focused maintenance release for the main window
project workflow and slot-rule editor.

## Highlights

- project creation now handles file-system and permission errors
  gracefully instead of crashing when the selected root folder is not
  writable
- the `PROJECT` action shows a clear error dialog if the project folder
  or README cannot be created
- project names now support up to `50` characters
- color selection has been removed from `Filter` and `Exclude` rules in
  the main window because those rule types do not use color semantics
- legacy stored colors for `Filter` and `Exclude` rules are normalized
  to `None` on load and save to keep settings and chip rendering clean

## Validation

The release branch was validated with the relevant automated test sets
for versioning, rule-slot behavior, settings persistence, and project
initialization, including:

- `tests/test_core_behavior.py`
- `tests/test_phase2_refactor.py`
- `tests/test_project_runtime.py`
- `tests/test_settings_store.py`

## Related Files

- [README.md](../README.md)
- [README_de.md](../README_de.md)
- [RELEASE_0.16.1_de.md](../docs/RELEASE_0.16.1_de.md)
