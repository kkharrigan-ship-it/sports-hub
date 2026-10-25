# 02: FIS snow Sports (alpine, snowboard, freestyle)

**What to build:** Alpine Skiing, Snowboarding and Freestyle Skiing appear in `data.json` with their upcoming World Cup Events. They come from the official FIS iCal service, which uses one feed pattern for all three Sports (selected by sector code).

**Blocked by:** 01 (F1 end-to-end walking skeleton)

**Status:** ready-for-agent

- [x] The Sports config adds `alpine`, `snowboard` and `freestyle` (category `snow`) with Watch options from the 2026-27 watch guide.
- [x] Each Sport's Events carry the race name, the venue location, and a UTC start time where the feed gives one.
- [x] Events that have no specific time are kept as date-only (all-day) Events, not given an invented midnight time.
- [x] Training sessions and lower-tier races are filtered out, so only World Cup competition Events appear.
- [x] Tests use saved real FIS feed responses for all three Sports, go through the Refresh entry point, and need no network.
- [x] One test covers an Event around a daylight-saving changeover and shows its UTC time is correct.
