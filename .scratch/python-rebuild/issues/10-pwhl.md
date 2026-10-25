# 10: PWHL from the HockeyTech feed

**What to build:** The PWHL appears on the Hub with every upcoming game (teams as the Event name, arena location, UTC puck-drop). The data comes from the public HockeyTech feed that the league's own site uses. The 2026-27 season opens Dec 5, so until then the Hub shows the first six games.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] `pwhl` is in the Sports config (category `ice`) with Watch options from the 2026-27 watch guide (PWHL YouTube and ION as free; Scripps Sports as free).
- [x] The fetcher finds the current regular season from the seasons feed, rather than hard-coding a season number.
- [x] The feed's wrapper around its JSON is removed before parsing. A change in that wrapper or in the shape raises a SourceError.
- [x] Each game is an Event named "Away at Home", with its arena location and UTC start time.
- [x] Tests use saved real HockeyTech responses (seasons and schedule), go through the Refresh entry point, and need no network.
