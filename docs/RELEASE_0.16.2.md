# Release 0.16.2

Release date: 2026-04-05

## Summary

Version `0.16.2` is a bugfix and usability release for project handling,
exit/save behavior, visualizer tooltips, and graph-window status
feedback.

## Highlights

- saving the `PROJECT` dialog no longer closes already open visualizer
  windows
- `RESET` now clears the active project context back to the default
  project state, and the `PROJECT` dialog also offers a dedicated `NEW`
  button for the same reset behavior
- closing the application while connected and after receiving data now
  offers `Save…`, `No`, and `Cancel`
- relevant dialogs and graph controls now provide clearer tooltips,
  including corrected dynamic `Window Size` tooltips
- plot and logic graph windows now show a footer status line with
  session start and duration
- plot windows can show compact `MAX/Mean/Current` statistics for
  selected `Line` series, controlled by the new `Statistic` column in
  the plot configuration dialog

## Validation

The release branch was validated with the focused automated test sets
for exit-save handling, project reset behavior, tooltip helpers,
visualizer footer status rendering, statistic persistence, and window
handling, including:

- `tests/test_main_exit_save.py`
- `tests/test_main_project_reset.py`
- `tests/test_project_dialog.py`
- `tests/test_visualizer_footer_status.py`
- `tests/test_visualizer_statistics_flag.py`
- `tests/test_visualizer_manager_close.py`
- `tests/test_window_size_tooltip.py`

## Related Files

- [CHANGELOG.md](../CHANGELOG.md)
- [USER_GUIDE_en.md](../docs/USER_GUIDE_en.md)
- [USER_GUIDE_de.md](../docs/USER_GUIDE_de.md)
- [RELEASE_0.16.2_de.md](../docs/RELEASE_0.16.2_de.md)
