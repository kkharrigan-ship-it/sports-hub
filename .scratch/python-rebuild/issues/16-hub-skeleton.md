# 16: Hub skeleton

**What to build:** Each Refresh now builds the Hub as well as `data.json`: a static page that Katie can open in a browser on any device. It shows one card per Sport:
- the Sport's name, its category colour and its next Events (name, session, date and time, location)
- its Status: in season, off season with its "Returns" label and note, or unavailable
- "stale since" marks on any Event shown from last-good state

The header shows when the Hub was last refreshed. The look carries over from the old Hub: dark theme tokens, the DM Sans and DM Mono fonts, and the category colours. The page reads `data.json` and needs no server.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The Refresh command writes the page, its stylesheet and its script next to `data.json` in the output folder, alongside the data. It never writes a half-built site if the Refresh fails.
- [x] Opening the output folder through a local preview shows all 19 Sports in config order, each with its next Events, or its "Returns" label and note when off season.
- [x] A Sport whose source is unavailable says so plainly. Stale Events show "stale since [date]".
- [x] The header shows "Last updated" from `data.json`.
- [x] The page works with JavaScript reading `data.json` only, with no other network calls except the Google Fonts stylesheet.
- [x] It is checked in a real browser preview against a fixed `data.json` (Seam 3), at desktop and phone widths.
