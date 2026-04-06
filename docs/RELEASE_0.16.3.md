# Release 0.16.3

Release date: 2026-04-06

## Summary

Version `0.16.3` is a focused bugfix release for exit/save handling
after disconnected sessions, listener shutdown robustness, and release
documentation consistency.

## Highlights

- the exit save dialog now appears whenever the current session already
  contains log data, even if the UDP listener has already been stopped
  or the data only remains in the saved live-session file
- listener shutdown now retries with a longer wait timeout when the
  first stop attempt does not finish in time
- English and German README files now point to the current release
  notes and use clearer demo-project wording
- bundled `README.pdf` and `README_de.pdf` were regenerated for the
  `0.16.3` release state

## Validation

The release branch was validated with the focused automated test sets
for exit-save handling and listener shutdown behavior, including:

- `tests/test_main_exit_save.py`
- `tests/test_listener_runtime.py`

## Related Files

- [CHANGELOG.md](../CHANGELOG.md)
- [README.md](../README.md)
- [README_de.md](../README_de.md)
- [RELEASE_0.16.3_de.md](../docs/RELEASE_0.16.3_de.md)
