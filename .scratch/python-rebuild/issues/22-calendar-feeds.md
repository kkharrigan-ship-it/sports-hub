# 22: Calendar feeds

**What to build:** Katie and Jason can put Events in their own calendars:
- **Subscribe:** each Refresh writes one subscribable calendar feed per Sport, plus one for all Sports. A Sport card's "Subscribe" link gives that feed's address, so a calendar app keeps it up to date.
- **Add one:** each Event has an "Add to calendar" button that downloads just that Event.
- **Watchlist export:** the Watchlist can be exported as one calendar file. This replaces the old Cowork Google Calendar sync.

A personal "my favourites" feed needs shared storage and comes in a later milestone.

**Blocked by:** 16 (Hub skeleton)

**Status:** ready-for-agent

- [x] The Refresh writes one feed per Sport and an all-Sports feed. Each entry has a stable id, so calendar apps update Events in place when times change rather than duplicating them.
- [x] Timed Events carry their UTC start and a default length; all-day and multi-day Events are all-day entries spanning their dates.
- [x] Each entry's description includes the session, location and the Sport's top Watch option.
- [x] Feed contents are tested through the Refresh entry point (Seam 1): a known Event's entry, an all-day multi-day Event, and a stable id across two Refreshes.
- [ ] The per-Event button and Watchlist export produce files that open in Apple Calendar and Google Calendar (checked by hand once). **Pending: Katie to try one of each.**
