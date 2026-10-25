# 11: Swimming and diving from World Aquatics

**What to build:** Swimming and Diving appear on the Hub, with their World Cup stops, World Championships and other top-level World Aquatics competitions. One API serves both, filtered by discipline.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] `swimming` and `diving` are in the Sports config (category `aqua`) with Watch options from the 2026-27 watch guide (Peacock as `have`).
- [x] Each competition is an Event with its name, city and country, and its dates. Multi-day competitions are shown on their first day with the end date included in `data.json`, unless session times are available.
- [x] Only top-level competitions are included. Junior, masters and open-water events are excluded unless the guide says otherwise.
- [x] A change in the API's response shape raises a SourceError.
- [x] Tests use saved real World Aquatics responses for both disciplines, go through the Refresh entry point, and need no network.
