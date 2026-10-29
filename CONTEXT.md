# Sports Hub — Context

A weekly-refreshed schedule of 19 niche and international sports, shared between Katie and Jason.
This project rebuilds the Cowork scheduled skill (`../../Scheduled/sports-hub-refresh/SKILL.md`) in Python.

## Glossary

- **Hub** — the shared web page both Katie and Jason use to see what's on. One interface for both (replaces the Cowork artifact + manually republished claude.ai copy).
- **Refresh** — one scheduled run that fetches schedules, rebuilds the Hub, and sends the Notification.
- **Notification** — the message telling Jason (and Katie) the Hub has been refreshed, with a link. Replaces the standalone Digest email.
- **Digest** — the old plain-text "What's on this week" email to Jason. Deprecated term; stopped arriving after June 2026.
- **Sport** — one of the 19 tracked competitions, keyed by a stable id (e.g. `f1`, `curling-ca`).
- **Event** — one dated session/competition for a Sport: name, date (and end date if multi-day), UTC start time or all-day, location, optional session and tags, and for Season-file entries the source link where its date was checked.
- **Session** — the part of an Event (e.g. Qualifying, Race), or for one-off matches the competition it belongs to (e.g. Six Nations).
- **Watch option** — a way to view an Event, typed `have` / `free` / `vpn` / `consider`.
- **Last-good state** — what a Refresh leaves for the next one: the date it ran and each Sport's Events from its most recent successful fetch. Used for stale fallback and the date-safety guard.
- **Stale** — an Event shown from last-good state because its source failed this Refresh, labelled "stale since [date]". A Sport's stale-since is its oldest stale Event; with several sources, only the failed source's Events are stale.
- **Alert** — a problem a Refresh reports: `error` (a Sport's source failed) or `warning` (its Event count collapsed).
- **Alert email** — the email to Katie listing a Refresh's Alerts. The Hub was still updated.
- **Not-updated email** — the email to Katie when a Refresh stops before building the Hub (or a later step fails), saying why. Distinct from the Monday **Notification** to Katie and Jason.
- **Watchlist** — the Events a viewer has starred on their own device, shown together in the Hub's Watchlist view.
- **Favourite Sport** — a Sport a viewer has pinned to the top of the Sports view on their own device. (Shared favourites between Katie and Jason are a later milestone.)
- **Reminder** — a banner the Hub shows ahead of something Katie needs to act on; so far only the ESPN+ reminder from 7 days before each Grand Slam of Curling.
- **Between seasons** — the Hub's heading for off-season Sports (with their "Returns" label and note) and in-season Sports whose listed Events have all passed until the next Refresh. Unavailable Sports are listed separately.
- **Category** — ice, snow, motor, track (shown as "track & other"), aqua (shown as "aquatics") or rugby.
- **Season-file check** — the weekly job that fingerprints every page the Season file cites and raises a Review issue when one changed, or when an entry on a site that refuses automated visitors is due a look (the week it comes within 8 weeks, and the week it's two weeks away).
- **Review issue** — the open GitHub issue labelled `season-review` that collects the check's findings and Claude's summary. Katie closes it once she's checked; the Season file is never edited automatically.
- **Status** — each Sport is `in-season` (has Events in the window), `off-season` (nothing upcoming; shows its "Returns" label) or `unavailable` (source failed with no last-good state).

## Priorities (agreed 2026-10-24)

1. Reliability — runs never silently fail, skip, or use a stale date.
2. Accuracy — no wrong or missing Events.
3. Less manual work — no hand republishing, no checking whether it ran.
4. Cost.
5. Independence from Cowork.
6. New features.

## Constraints

- Katie has a Claude **Pro** subscription. Pro does not include API access, so any Claude API call from Python is a new per-token dollar cost.
- Runs on **GitHub Actions** (scheduled). Katie is new to GitHub and will need guided setup.
- Watch-option data needs a fresh review: neither the old skill nor the last Hub snapshot is trusted as correct.
- Katie's current services: Apple TV, Peacock, ExpressVPN. Prefers free options; open to a new subscription if clearly best.

## Decisions so far (2026-10-24)

- **Calendar**: per-Sport subscribable calendar feeds plus per-Event "add to calendar" buttons. Replaces the Cowork Google Calendar sync.
- **Notification**: email from Katie's Gmail (app password as a GitHub secret) to Katie and Jason, Mondays, with this week's highlights and the Hub link. A separate failure alert goes to Katie if a Refresh breaks.
- **Refresh cadence**: twice weekly (Mon + Thu); Notification only on Monday.
- **Data sources**: deterministic fetchers where a structured source exists (PWHL, swimming, diving, alpine, snowboard, freestyle, biathlon, F1, MotoGP, Six Nations, and ISU speed skating / short track per ADR 0001). A Sport may combine several sources (Ireland: Season file + Six Nations page). Hard sports (curling ×2, FIG, World Skate, WEC, SailGP, Diamond League, Ireland Nov tests) come from a hand-checked **Season file**; a weekly check flags differences for Katie rather than overwriting.
- **Transition**: Cowork version keeps running until the Python Hub has two good weeks, then is switched off.

- **Hosting**: static site on GitHub Pages from a **public** repo. Secrets live only in GitHub secrets.
- **Interactivity (v1)**: filter/search by Sport, per-device favourites, time-zone toggle — all in-browser. Shared favourites/watchlist and reactions/comments are a **later milestone** (they need shared storage).
- **Season-file check**: free "page changed" fingerprinting for fetchable sites, plus Claude Code in GitHub Actions on Katie's Pro subscription for the rest — **pending verification** that subscription use is supported/allowed; fallback is the Claude API with a $2/month hard cap.
- **Watch options**: Katie and Jason have the same services (Apple TV, Peacock, ExpressVPN), so one set of badges. Order: owned/free legal first; VPN options shown only as a tagged fallback when no legal free/owned option exists. See `docs/research/watch-guide-2026-27.md`.
- **ESPN+**: subscribe only in Grand Slam of Curling months; the Hub shows a reminder a week before each Slam.
- **Season recheck**: the Hub flags Sports whose broadcast rights are unconfirmed so they get rechecked before their season opener.
