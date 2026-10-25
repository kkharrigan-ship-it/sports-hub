# 14: Speed Skating and Short Track

**What to build:** Speed Skating (ISU World Cup) and Short Track (ISU World Tour) appear on the Hub. First, a time-boxed attempt to read their events from the ISU website's embedded page data. If that proves fragile (no stable structure, or no dates without heavy reverse-engineering), both Sports go into the Season file instead. Either way, the decision is recorded.

**Blocked by:** 07 (Season file, starting with WEC and SailGP)

**Status:** ready-for-agent

- [x] `speed-skating` and `short-track` are in the Sports config (category `ice`) with Watch options from the 2026-27 watch guide, and are flagged rights-unconfirmed.
- [x] The attempt is capped at roughly an hour of investigation. The outcome (feed or Season file) and the reason are recorded as an ADR.
- [x] If a feed: tests use saved real ISU pages, go through the Refresh entry point, and need no network, and a change in the page's data structure raises a SourceError.
- [x] If the Season file: every 2026-27 World Cup and World Tour stop is listed with a source link.
- [x] Short Track shows its Vancouver stop (Oct 23-25) on 2026-10-24.
