# Hub parity check (ticket 24, 2026-10-24)

Checked in the browser preview against a live Refresh, with a fixed clock (`?now=2026-10-30T15:00:00Z`), at desktop width and at phone width (375px). Both themes were checked.

## Design brief §2: behaviour to keep

| Requirement | Result |
|---|---|
| All 19 Sports, same ids | ✅ 19 cards/chips; ids unchanged |
| Next 56 days, or next 6 if fewer | ✅ from the Refresh (tested in Python) |
| Off-season "Returns [date]" label and note | ✅ "Between seasons" chips with label and note visible; unavailable Sports listed separately |
| Event fields: date, start time, name, location, Watch options | ✅ card rows, Timeline, Watchlist |
| Times shown in CST/ET/GMT (now in the browser, plus Local) | ✅ switching zones changes times; daylight saving handled (UK BST until Oct 25) |
| Watch option types have/free/vpn/consider, ranked, VPN as a fallback only | ✅ legend plus ranked badges; VPN only where there's no owned or free legal option |
| Category icons only on pills, never before Sport names | ✅ scripted check finds no icons in Sport names, Timeline or What's on |
| "Last updated" from the real run date | ✅ header |
| Add to calendar: subscribable feeds and per-Event buttons | ✅ webcal Subscribe link per Sport; "+ cal" downloads .ics with the feed's id, session, location and best Watch option, folded to 75 bytes; Watchlist export. Hand test in Apple/Google Calendar still pending |
| Weekly message to Jason | ⏳ Milestone 5 (Notification) |

## Old Hub features

| Feature | Result |
|---|---|
| Sports, Timeline and ⭐ Watchlist views | ✅ last view remembered |
| What's on: This Weekend / Next 7 Days / Next 14 Days | ✅ empty groups say so warmly; 3 per group on phones |
| LIVE badges and LIVE banner | ✅ timed Events live for 2h; multi-day Events through their last day |
| Category pills | ✅ plus search; "no matches" offers to clear |
| Starred Events kept across sessions | ✅ survives reload; a notice appears if the browser blocks storage |
| Google Calendar sync (Cowork only) | Replaced by feeds and .ics export, by design |

## New in Milestone 3

| Feature | Result |
|---|---|
| Favourite Sports pinned first | ✅ |
| Recheck-before-season badge | ✅ |
| ESPN+ Grand Slam reminder | ✅ shows from 7 days before (Oct 27 for the Masters); dismissible per Slam |
| Stale marks per Event | ✅ |

## Accessibility and phone

- Every button, link and input has an accessible name (scripted check). Decorative dots are hidden from screen readers.
- Data put into the page is escaped. Categories and Watch types are checked against the known values before going into class names or styles, and Subscribe links only point at the Hub's own feeds.
- Toggles use `aria-pressed`; focus outlines are visible.
- Tap targets are at least 28px high.
- No sideways scroll at 375px.
- Light theme follows the device setting; dark keeps the old Hub's tokens.
