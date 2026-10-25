# 20: Watchlist and favourite Sports

**What to build:** Two per-device ways to personalise the Hub:
- **Watchlist** (from the old Hub): star individual Events and see them together in a ⭐ Watchlist view.
- **Favourite Sports** (new): star a whole Sport so it's pinned to the top of the Sports view.

Both live in the viewer's browser. Shared favourites between Katie and Jason are a later milestone.

**Blocked by:** 16 (Hub skeleton)

**Status:** ready-for-agent

- [x] Starring an Event adds it to the Watchlist view; unstarring removes it. The stars survive reloads on that device.
- [x] Watchlist Events that have passed drop off. Events that no longer appear in `data.json` are shown as "no longer listed" rather than silently vanishing.
- [x] Favourite Sports appear first in the Sports view, in config order, then the rest.
- [x] If browser storage is blocked, the page still works (stars just don't persist) and says so once.
- [x] It is checked in a browser preview with a fixed `data.json`: star, reload, and the star persists.
