# 17: Time zones and LIVE badges

**What to build:** Viewers choose how times are shown (CST, ET, GMT or their device's local time), and the Hub remembers the choice on that device. Timed Events show their start in the chosen zone; all-day Events show only their date; multi-day Events show their date range. Anything happening right now gets a LIVE badge.

**Blocked by:** 16 (Hub skeleton)

**Status:** ready-for-agent

- [x] The toggle offers CST, ET, GMT and Local, with CST as the default. Times are converted in the browser using real time zones, so daylight saving is handled.
- [x] The choice survives a reload on the same device. If browser storage is blocked, the page falls back to CST.
- [x] All-day Events never show a time; multi-day Events show "date to date".
- [x] An Event shows LIVE from its start until it ends: for timed Events, a sensible default length (shown in the code); for multi-day Events, until the end of the last day.
- [x] It is checked in a browser preview with a fixed `data.json` and a known clock: switching zones changes the times shown, and a known Event is LIVE.
