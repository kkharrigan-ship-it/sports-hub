# 03: Biathlon via IBU

**What to build:** Biathlon appears in `data.json`, with each World Cup race as its own Event. The data comes from the IBU results API in two steps: first the season's events, then the competitions (races) inside each event.

**Blocked by:** 01 (F1 end-to-end walking skeleton)

**Status:** ready-for-agent

- [x] The Sports config adds `biathlon` (category `snow`) with Watch options from the 2026-27 watch guide.
- [x] Each race becomes an Event with its race name (e.g. women's sprint), the venue location and a UTC start time.
- [x] Only World Cup-level events are included.
- [x] Only events that touch the Refresh window are looked up in the second step, so a run stays at a handful of requests.
- [x] Tests use saved real IBU responses for both steps, go through the Refresh entry point, and need no network.
