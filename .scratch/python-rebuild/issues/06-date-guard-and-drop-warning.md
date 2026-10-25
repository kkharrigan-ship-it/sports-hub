# 06: Date-safety guard and Event-count-drop warning

**What to build:** The Refresh refuses to publish when its "today" is earlier than the previous build's date. This guards against the old stale-date incident, where a run anchored everything to a date two weeks old. It also adds a warning alert when a Sport's Event count collapses compared with the previous run, which catches a source that has silently changed.

**Blocked by:** 05 (Broken source keeps last-good data and raises an alert)

**Status:** ready-for-agent

- [x] If "today" is before the previous build's last-updated date, the Refresh fails with a clear error and writes no outputs.
- [x] If "today" equals or follows the previous build's date, the Refresh proceeds normally.
- [x] A sharp drop in a Sport's in-window Event count, compared with the previous run, adds a warning alert. Going to zero at a season's natural end (off-season) does not count as a drop.
- [x] The build command exits with a non-zero status when the guard trips, so a scheduled run shows as failed.
- [x] Tests go through the Refresh entry point and cover: a backwards date (refused), the same date (allowed), a collapsed count (warns), and a season end (doesn't warn).
