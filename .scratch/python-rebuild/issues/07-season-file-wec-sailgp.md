# 07: Season file, starting with WEC and SailGP

**What to build:** The hard-to-fetch Sports get a hand-checked **Season file**: one readable YAML file per season (2026-27 first). The Refresh reads it like any other source.
- **Entries:** each entry gives a Sport id, an Event name, an optional session, a date, an optional start time with its time zone (converted to UTC; no time means all-day), a location and a source link.
- **Off-season text:** the file also holds each Sport's off-season "Returns" label and note. These move out of the Sports config (F1's label moves too).

FIA WEC and SailGP are the first two Sports, with their real 2026-27 dates researched and linked.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The Season file format is documented at the top of the file in plain words, so Katie can edit it.
- [x] Entries with a time and zone become UTC Events, and entries with only a date become all-day Events.
- [x] A malformed entry (missing date, unknown Sport id, bad time zone) stops the Refresh with a ConfigError naming the entry. It does not silently skip it.
- [x] Every entry carries a source link to where its date was checked.
- [x] `wec` and `sailgp` are in the Sports config with Watch options and rights flags from the 2026-27 watch guide, and their Events come from the Season file.
- [x] "Returns" labels and off-season notes are read from the Season file for all Sports; F1's label is moved there.
- [x] Tests go through the Refresh entry point using a small test Season file. They cover a timed entry across a DST change, an all-day entry, an off-season label and a malformed entry.
