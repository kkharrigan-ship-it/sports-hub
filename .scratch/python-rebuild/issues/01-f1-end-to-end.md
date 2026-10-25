# 01: F1 end-to-end walking skeleton

**What to build:** Running the build command on Katie's Mac performs a Refresh for Formula 1 and writes `data.json` containing F1's upcoming Events. This slice lays down the whole path that every later Sport reuses:
- the Python 3.12 project
- the Event and Sport model
- the Sports config, with only F1 in it
- the Jolpica F1 fetcher
- the single Refresh entry point (it takes "today", an HTTP client and the previous last-good state)
- the window rules
- `data.json` output

See spec §Implementation Decisions (domain model, fetcher contract, Refresh entry point, window rules) and §Testing Decisions (Seam 1).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The project installs on Python 3.12 with only the dependencies agreed in the spec (httpx, icalendar, PyYAML, plus pytest for development).
- [x] The Sports config lists F1 with id `f1`, category `motor` and its Watch option (Apple TV, type `have`).
- [x] The F1 fetcher returns one Event per session (practice, sprint, qualifying, race) with timezone-aware UTC start times, the Grand Prix name and the circuit location.
- [x] The Refresh keeps Events within 56 days of "today". If a Sport has fewer than 6 in that window, it extends to that Sport's next 6.
- [x] `data.json` includes the last-updated date (taken from "today"), every Sport from the config and its Events.
- [x] A build command runs the Refresh with the real clock and live network, and writes `data.json`.
- [x] Tests go through the Refresh entry point with a fixed "today" and a saved real Jolpica response. They run with no network and pass.
- [x] Tests cover the 56-day cut-off, the next-6 extension and session times in UTC.
