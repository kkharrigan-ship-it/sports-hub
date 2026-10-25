# 05: Broken source keeps last-good data and raises an alert

**What to build:**
- When a Sport's source fails (network error, an unexpected response shape, or data that doesn't parse), only that Sport is affected.
- That Sport keeps its last-good Events, marked "stale since [date]", and the Refresh result includes a plain-English alert naming the Sport and the reason.
- Every other Sport updates normally.
- A successful Refresh saves the new last-good state, so the next run can fall back to it.

Sending the alert email is out of scope here (Milestone 4); this ticket only produces the alerts.

**Blocked by:** 01 (F1 end-to-end walking skeleton)

**Status:** ready-for-agent

- [x] Every fetcher checks the shape of what it receives, and raises a typed source error instead of guessing.
- [x] The Refresh catches source errors per Sport: that Sport keeps its previous Events (still trimmed to the current window), and its stale-since date appears in `data.json`.
- [x] A failing Sport that has no previous state shows as unavailable instead of crashing the Refresh.
- [x] Alerts are part of the Refresh result. Each one names the Sport, gives a short reason, and contains no secrets.
- [x] Last-good state is written after a Refresh and read back on the next one.
- [x] Tests go through the Refresh entry point with a deliberately broken saved response for one Sport. They show that the other Sports update, the broken one is stale with its previous Events, and one alert is produced.
