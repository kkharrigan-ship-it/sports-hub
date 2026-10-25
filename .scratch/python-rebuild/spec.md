# Spec: Sports Hub Python rebuild

Status: ready-for-agent
Design brief: `design-brief.md` (same folder). Vocabulary: `CONTEXT.md`.

## Problem Statement

Katie follows 19 niche and international Sports and shares the schedule with Jason. Today a Cowork scheduled skill has Claude web-search every Sport each week and rewrite a ~95 KB HTML artifact. The result is fragile:

- Runs have been irregular, and one run used dates that were two weeks out of date.
- The skill's streaming guide has drifted out of sync with the Hub's own data.
- The save path no longer matches reality.
- Jason's weekly Digest stopped arriving after June 2026, and nobody was told.

Katie and Jason also don't share one interface. Katie has the Cowork artifact plus a claude.ai copy she republishes by hand; Jason only had an email. Calendar sync only works inside Cowork. Neither of them can trust the information is current without checking.

## Solution

A small Python project that runs a **Refresh** on GitHub Actions twice a week (Mon and Thu). It publishes one shared, interactive **Hub** to GitHub Pages that both Katie and Jason bookmark.

- **Structured Sports** are fetched directly from official or community data feeds, with no AI involved: F1, FIS Alpine, Snowboard and Freestyle, biathlon, PWHL, swimming, diving, MotoGP and the Six Nations.
- **Hard Sports** come from a hand-checked **Season file**: both curling Sports, gymnastics, World Skate, WEC, SailGP, Diamond League and Ireland's November tests.
- **Weekly Season-file check:** compares the file against official pages and raises a review item for Katie. It never edits data.
- **Monday Notification** email goes to both of them with highlights and the link.
- **Failure alert** goes to Katie whenever anything breaks or goes stale.

**The Hub itself:**
- filters and search
- per-device favourites
- a time-zone toggle
- ranked Watch options
- subscribable calendar feeds
- a reminder before each Grand Slam of Curling event
- "recheck before season" flags

## User Stories

### Viewing the Hub
1. As Katie, I want to open one link on any device and see what's on, so that I don't depend on Cowork being open.
2. As Jason, I want to open the same Hub link as Katie, so that we're looking at the same information.
3. As a viewer, I want to see each Sport's upcoming Events for the next 8 weeks, so that I can plan ahead.
4. As a viewer, I want to see a Sport's next 6 Events even if they fall beyond 8 weeks, so that sparse Sports never look empty.
5. As a viewer, I want an off-season Sport to show "Returns [date]" and a short note, so that I know when it comes back.
6. As a viewer, I want each Event to show its date, start time, name and location, so that I know when and where it is.
7. As a viewer, I want to switch Event times between CST, ET, GMT and my device's local time, so that times make sense wherever I am.
8. As a viewer, I want my time-zone choice remembered on my device, so that I don't reset it every visit.
9. As a viewer, I want to filter Events by Sport and by category (ice, snow, motor, track, aqua, rugby), so that I can focus on what I care about.
10. As a viewer, I want to search Events by text, so that I can find a specific race or venue quickly.
11. As a viewer, I want to mark Sports as favourites on my device, so that my Hub opens with what I follow.
12. As a viewer, I want a "this week" view, so that I can see at a glance what's on in the next 7 days.
13. As a viewer, I want to see when the Hub was last refreshed, so that I can trust it's current.
14. As a viewer, I want a Sport whose data is stale to say "stale since [date]", so that I know not to fully trust it.
15. As a viewer, I want category icons only on category pills and never stuck in front of Sport names, so that names stay clean.
16. As a viewer, I want the Hub to work well on my phone, so that I can check it on the sofa.

### Watching
17. As a viewer, I want each Sport and Event to show how to watch it, so that I don't have to look it up.
18. As Katie or Jason, I want options we already pay for (Apple TV, Peacock) shown first, so that I reach for what I have.
19. As a viewer, I want free legal options shown next, so that I avoid paying when I don't need to.
20. As a viewer, I want VPN-only options shown only when no owned or free legal option exists, clearly tagged, so that I use them knowingly.
21. As a viewer, I want "consider" options (paid services we don't have) labelled with a rough price, so that I can decide if it's worth it.
22. As Katie, I want a banner 7 days before each Grand Slam of Curling event reminding me to switch ESPN+ on, so that I only pay in Slam months.
23. As Katie, I want Sports whose broadcast rights are unconfirmed to carry a "recheck before season" badge, so that I verify them before the opener.
24. As Katie, I want Watch options kept in one editable config file, so that they never drift between two places again.

### Calendar
25. As a viewer, I want to subscribe to a calendar feed per Sport, so that Events appear and update in my Google or Apple Calendar automatically.
26. As a viewer, I want an add-to-calendar button on each Event, so that I can add one-offs.
27. As a viewer, I want calendar entries to carry the correct start time and Watch option, so that the reminder is useful on its own.
28. As a viewer, I want a changed Event time to update in my subscribed calendar, so that I'm not caught out by a rescheduled session.

### Notification
29. As Jason, I want a Monday email saying the Hub is refreshed, with this week's highlights and the link, so that I know what's on without remembering to check.
30. As Katie, I want the same Monday email, so that I know the Refresh ran.
31. As a recipient, I want the email grouped by day with times in CST, so that it's quick to scan.
32. As a recipient, I want a warm "nothing on this week, next up is …" message on quiet weeks, so that the email is still useful.
33. As Katie, I want only one Notification a week even though the Hub refreshes twice, so that Jason isn't spammed.

### Reliability
34. As Katie, I want a failure alert email when a Refresh fails, so that problems never go unnoticed again.
35. As Katie, I want one broken source to affect only its own Sport, so that the rest of the Hub still updates.
36. As Katie, I want a Sport with a broken source to keep its last good Events and be marked stale, so that the Hub never goes blank.
37. As Katie, I want the alert to name which Sport failed and why in plain words, so that I know what to look at.
38. As Katie, I want "today" taken from the real clock and the build to refuse to publish data older than the previous build, so that the stale-date incident can't happen again.
39. As Katie, I want a sudden large drop in a Sport's Event count flagged, so that a silently changed data feed is caught.
40. As Katie, I want a sign that a source has changed its format to raise an alert instead of producing wrong Events, so that bad data never reaches the Hub.
41. As Katie, I want every run's history visible in GitHub, so that I can see what happened and when.

### Season file and weekly check
42. As Katie, I want hard-to-fetch Sports' dates kept in a simple, readable Season file, so that I can check and edit them myself.
43. As Katie, I want a weekly check that notices when an official calendar page changes, so that I learn about date changes without visiting 8 websites.
44. As Katie, I want the check to describe what changed as a review item, not edit the Season file itself, so that nothing changes without my say.
45. As Katie, I want sites that block automated visitors (the curling bodies) covered by a Claude check that reads other sources, so that those Sports aren't left unchecked.
46. As Katie, I want the Claude check to run on my Pro subscription, so that it costs no extra money.
47. As Katie, I want a reminder before the Claude login token expires, so that the check doesn't quietly stop.

### Setup, cost and handover
48. As Katie, new to GitHub, I want a guided step-by-step setup, so that I can get the repo, Pages, secrets and schedule working without prior knowledge.
49. As Katie, I want secrets (Gmail app password, Claude token) stored only as GitHub secrets, so that the public repo never exposes them.
50. As Katie, I want a measured comparison of the old and new versions (usage, run time, accuracy, reliability), so that I know whether this was worth it.
51. As Katie, I want the Cowork version to keep running for two weeks alongside, so that I have a safety net before switching it off.
52. As a maintainer, I want to add a new Sport by adding config plus at most one fetcher, so that the Hub can grow.

## Implementation Decisions

- **Runtime:** Python 3.12. Dependencies are httpx (HTTP), icalendar (reading FIS feeds and writing calendar feeds), PyYAML (config) and pytest (dev only). No web framework, no database, no templating engine.
- **Domain model:**
  - An **Event** carries Sport id, start as a timezone-aware UTC timestamp (or date-only for all-day Events), name, location and optional session label.
  - A **Sport** carries id, display name, category, source kind, ranked Watch options and a rights-unconfirmed flag.
  - All 19 Sport ids are kept exactly as they were.
- **Sports config:** one YAML file lists every Sport with category, source kind, Watch options (type: have/free/vpn/consider, label, optional price and note) and rights status. It's the single source of truth for Watch options, seeded from the 2026-27 watch guide research.
- **Season file:** one YAML file per season holds hand-checked Events for the hard Sports, plus off-season notes and "Returns" dates. It's read by a fetcher like any other source.
- **Fetchers:** one module per source kind, each with the same contract: given an HTTP client and a date window, return Events or raise a typed source error. Planned sources:
  - Jolpica for F1
  - the FIS iCal service for three Sports (by sector code)
  - the IBU biathlon results API
  - the HockeyTech feed for PWHL (wrapped response must be unwrapped)
  - the World Aquatics competitions API for swimming and diving (by discipline)
  - the MotoGP Pulselive API
  - the Six Nations fixtures page data
  - an attempt at ISU skating, falling back to the Season file if it proves fragile
- **Shape checks:** each fetcher checks the shape of what it receives and raises a source error on mismatch, rather than guessing.
- **Refresh entry point:** a single function takes "today", an HTTP client and the previous last-good state, and returns a result with every Sport's Events (or stale fallback), alerts and build outputs. The command line and the GitHub workflow are thin wrappers around it.
- **Window rules:** Events in the next 56 days. If a Sport has fewer than 6, extend to its next 6. If none, mark the Sport off-season using the Season file's "Returns" date and note.
- **Validation:**
  - The date-safety guard compares "today" with the previous build's date and refuses to publish if it goes backwards.
  - A Sport whose Event count falls sharply against the previous run raises a warning alert.
  - A failed Sport keeps last-good Events with a stale-since date.
- **Last-good state:** a small JSON document per Sport, committed back to the repo by the workflow after each successful Refresh.
- **Build outputs:**
  - a `data.json` consumed by the Hub page (Sports, Events, Watch options, last-updated, stale flags, Slam reminder dates)
  - one calendar feed per Sport, plus one combined feed
  - the static site files
- **Hub page:**
  - vanilla HTML, CSS and JS reading `data.json`
  - favourites and time-zone choice stored in the viewer's browser storage, wrapped so the page still works if storage is blocked
  - visual style carried over from the current Hub (DM Sans and DM Mono, existing colours and layout)
  - time zones converted in the browser using real IANA zones
- **Mail sender:** a single small interface with an SMTP implementation (Gmail with an app password, from environment variables) and an in-memory fake for tests. It sends the Monday Notification and the failure alert. Logs never include addresses or credentials.
- **Workflows:**
  - **Refresh** runs Mon and Thu early morning Central: build, commit state, publish to Pages, and send the Notification on Mondays only.
  - **Season-file check** runs weekly. It fingerprints the official calendar pages and, when a page changed or for the curling Sports, runs Claude Code (authenticated with Katie's subscription token) to compare against the Season file and open a review issue. Claude has read-only intent: it never commits data.
- **Secrets**, as GitHub secrets: the Gmail app password, the sender address, the recipient addresses and the Claude Code login token. An API key with a $2/month cap is a documented fallback, not configured by default.
- **Hosting:** a public GitHub repo named `sports-hub`, published with GitHub Pages.

## Testing Decisions

- **Good tests check behaviour from the outside.** Given inputs, they assert on outputs (Events in `data.json`, calendar feed contents, alerts, emails sent), never on fetcher internals, private functions or intermediate structures. Rewriting a fetcher must not break a test unless its output changes.
- **Seam 1 (primary), the Refresh entry point.** Tests supply:
  - a fixed "today"
  - an HTTP client backed by saved real responses from each source, with no live network
  - a previous last-good state

  They assert on the result. Covered here:
  - each source's parsing and shape checks
  - the window and next-6 rules
  - off-season labels
  - time-zone correctness, including DST edges
  - the date-safety guard
  - stale fallback
  - the Event-count-drop warning
  - calendar feed contents
- **Seam 2, the mail sender.** The in-memory fake records messages. Tests assert:
  - the Monday Notification content, grouping and quiet-week wording
  - that it's sent only on Mondays
  - the failure alert contents
  - that no secrets appear in messages or logs
- **Seam 4, config loading** (added in Milestone 2; agreed with Katie 2026-10-24). Loading the Sports config and Season file is tested directly, for behaviour a Refresh can't see:
  - hand-editing mistakes stop with a clear ConfigError naming the Sport, entry and field;
  - the config holds exactly the agreed 19 Sports, with Watch options and rights flags matching the watch guide.
- **Seam 3, the Hub page.** It's checked in a real browser preview against a fixed `data.json`. The check is scripted where simple (filters, favourites persistence, time-zone toggle) and visual for layout, including phone width. There are no separate JS unit tests.
- **Fixtures:** saved responses are captured once from the live sources and stored with the tests. Refreshing them is a deliberate, reviewed action.
- **Not automated:** GitHub workflow wiring and the Claude Code review step. Those are proven by live runs (two successful scheduled Refreshes, one deliberately broken run that alerts, and one deliberately changed fixture that produces one review item).
- **Prior art:** none in this repo yet. The first tests through Seam 1 set the pattern for the rest.

## Out of Scope

- Shared favourites, watchlist and reactions or comments between Katie and Jason (a later spec; needs shared storage and login).
- A visual redesign of the Hub (style carries over).
- Google Calendar API sync (replaced by subscribable feeds).
- Fixing the Make webhook (replaced by direct email).
- Any Claude API usage by default (fallback only).
- Automatically editing the Season file from the weekly check.
- Accounts, login or private hosting.
- Streaming deep links or checking availability live.

## Further Notes

- **Milestone order and acceptance criteria** are in `design-brief.md` §8. Milestone 1 (data core for F1, the three FIS Sports and biathlon, running locally) is the first slice to implement. Each milestone stops for Katie's approval.
- **Measurement plan** (`design-brief.md` §7):
  - The baseline is one manual Cowork run measured against Katie's Pro usage meter and a 10-Event accuracy spot check.
  - The comparison happens during the two-week parallel run.
  - Estimates are always labelled as such.
- **Watch options** that are unconfirmed for 2026-27 are flagged in the research file and seed the rights-unconfirmed flags.
- **Claude login token:** Anthropic's GitHub Actions docs confirm it works on Pro. One unconfirmed source says it expires after a year, so the renewal reminder should be dated a year from creation.
- **Unofficial data feeds** (HockeyTech, World Aquatics, IBU, Pulselive) are undocumented and may change; the shape checks and alerts exist for this reason.
