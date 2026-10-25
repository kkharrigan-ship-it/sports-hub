# 1. ISU skating Events come from the ISU events pages, not the Season file

Date: 2026-10-24 · Status: accepted

## Context

Ticket 14 time-boxed an attempt (about an hour) to read Speed Skating and Short Track Events from isu-skating.com, falling back to the Season file if that proved fragile. The ISU has no public API.

## Decision

Read each discipline's events page (`/en/speed-skating/events/`, `/en/short-track/events/`). The page embeds every event of the season as page data with `from_date_utc`, `to_date_utc`, the venue `time_zone`, city, country and an event sub-type. Junior events are filtered out by that sub-type.

The investigation took about ten minutes. The 2026-27 lists it produced matched an independent research pass against the ISU calendar news pages: the same stops, cities and dates. The one difference: research listed the Beijing World Cup as 13–15 Nov, and the page data agrees once its UTC range is converted to Beijing time.

## Consequences

- Both Sports update themselves on every Refresh (twice a week), so no hand-maintained dates are needed.
- The reader depends on the page's data layout: the order of those keys and an Event `name` shortly before them. A layout change raises a SourceError, and the Sport falls back to its last-good Events with an Alert.
- If the page layout changes repeatedly, move both Sports into the Season file. The research list from 2026-10-24 is a starting point.
- One event (Shanghai) gives its time zone as `UTC`, so its local dates may be off by a day at most.
