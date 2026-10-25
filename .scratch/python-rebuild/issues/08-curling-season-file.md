# 08: Curling (both Sports) in the Season file

**What to build:**
- **Curling (Canada):** the Hub shows the 2026-27 Grand Slam of Curling and the Curling Canada events.
- **Curling (Intl):** the Hub shows World Curling events, starting with the European Championships on Oct 27.

All are researched into the Season file with source links. Grand Slam events are marked as Slams, so the ESPN+ reminder in Milestone 3 can find them.

**Blocked by:** 07 (Season file, starting with WEC and SailGP)

**Status:** ready-for-agent

- [x] `curling-ca` and `curling-intl` are in the Sports config with Watch options and rights flags from the 2026-27 watch guide (ESPN+ as `consider` with a price for the Grand Slams).
- [x] The Season file lists every 2026-27 Grand Slam and Curling Canada national event, plus the World Curling events for the season. Each entry has dates, location and a source link.
- [x] Grand Slam entries carry a Slam marker that appears in `data.json`.
- [x] Where draw times aren't published yet, events are all-day rather than given invented times.
- [x] A Refresh test shows both curling Sports with their next Events. The Euros appear for curling-intl on 2026-10-24.
