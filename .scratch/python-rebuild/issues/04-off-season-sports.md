# 04: Off-season Sports

**What to build:** A Sport with no upcoming Events shows as off-season in `data.json`, with a "Returns [date]" label and a short off-season note. Until the Season file arrives in Milestone 2, the label and note come from the Sports config. This matters now: F1's 2027 calendar isn't published yet, so Jolpica returns no 2027 races.

**Blocked by:** 01 (F1 end-to-end walking skeleton)

**Status:** ready-for-agent

- [x] Each Sport in `data.json` has a status: in-season or off-season.
- [x] An off-season Sport carries its "Returns" label and note when the config provides them, and degrades gracefully when it doesn't.
- [x] A fetcher that legitimately returns no Events (for example, a season not yet published) is treated as off-season, not as an error.
- [x] Tests go through the Refresh entry point, with a fixed "today" after the 2026 F1 finale and an empty saved 2027 response. They show F1 marked off-season with its label.
