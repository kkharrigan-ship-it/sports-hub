# Design brief: Sports Hub Python rebuild

Status: needs-triage (awaiting Katie's approval)
Date: 2026-10-24
Vocabulary: see `CONTEXT.md` (Hub, Refresh, Notification, Sport, Event, Watch option, Season file).

## 1. Problem and users

The Cowork skill rebuilds a 95 KB HTML artifact by having Claude web-search 19 sports every week. It has:
- drifted (wrong save path, streaming data out of sync with its own instructions);
- used stale dates once;
- run irregularly;
- stopped delivering Jason's Digest after June 2026, without anyone noticing.

It also needs Katie to republish a claude.ai copy by hand.

**Users:** Katie and Jason, equally. Both want **one shared, interactive Hub** they can open anywhere, and a weekly heads-up when it's fresh.

## 2. Behaviour to keep

Everything below is required unless it is marked as changed.

- **Coverage:** all 19 Sports with their existing ids: pwhl, curling-ca, curling-intl, speed-skating, short-track, swimming, diving, gymnastics, alpine, snowboard, freestyle, biathlon, f1, motogp, sailgp, wec, diamond-league, world-skate, ireland-rugby.
- **Event window:** Events in the next **8 weeks**. If a Sport has fewer than that, show its next 6 Events even beyond the window.
- **Off-season Sports** show a "Returns [date]" label and a short off-season note.
- **Event fields:** date, start time, name, location and Watch options.
- **Times:** stored as real timestamps and shown in CST/ET/GMT. *Changed:* the time-zone toggle now lives in the viewer's browser.
- **Watch option types:** have / free / vpn / consider. *Changed:* they're ranked, and VPN appears only as a fallback.
- **Category icons** appear only on category pills, never in front of Sport names.
- **"Last updated"** is shown on the Hub, taken from the real run date.
- **Calendar:** you can add Events to a calendar. *Changed:* subscribable feeds plus per-Event buttons, replacing the Google Calendar sync that only worked inside Cowork.
- **Weekly message to Jason.** *Changed:* it becomes the Monday Notification to both of you, with highlights and the link, replacing the full plain-text Digest.

## 3. Requirements

### Functional
- **F1 Refresh:** fetch, validate and build `data.json`, per-Sport `.ics` feeds, and the static Hub.
- **F2 Interactivity:** filter and search by Sport and category, per-device favourites (browser storage), and a time-zone toggle (CST/ET/GMT/local).
- **F3 Calendar feeds:** one `.ics` per Sport plus an "all favourites" feed. Each Event also gets an add-to-calendar button.
- **F4 Watch guide:** shown on each Sport and Event, from `config/sports.yaml`.
- **F5 Recheck flags:** Sports whose broadcast rights are unconfirmed show a "recheck before the season starts" badge.
- **F6 ESPN+ reminder:** a banner shows 7 days before each Grand Slam of Curling event.
- **F7 Notification:** a Monday email to Katie and Jason.
- **F8 Failure alert:** an email to Katie whenever a Refresh fails or a Sport goes stale.
- **F9 Season-file check:** weekly. It flags differences between the Season file and official sources as a review item, and never overwrites anything automatically.

### Non-functional
- **Reliability first.** A broken source must never break the whole Hub. That Sport keeps its last good data with a "stale since" note, and Katie gets an alert.
- **Date safety.** "Today" always comes from the runner's clock. The build refuses to publish if the newest data is older than the previous build's.
- **No secrets in the repo.** Secrets live only in GitHub secrets, and logs never print email addresses or tokens.
- **Polite fetching.** At most a few requests per source per run, with a descriptive User-Agent.
- **Small and boring.** Python 3.12, a handful of dependencies (§6), no frameworks, no database.

### Constraints
- Claude **Pro** subscription only, so Claude API calls would cost extra money.
- Runs on GitHub Actions and is hosted on GitHub Pages, from a public repo.
- Katie is new to GitHub, so setup is a guided, step-by-step walkthrough.

## 4. Pain points vs. improvements

| Today's pain | Required fix | Optional improvement |
|---|---|---|
| Silent failures; the Digest stopped in June | F8 failure alert; GitHub keeps a log of every run | A small run-history panel in the Hub |
| Stale dates | Date safety guard | — |
| Streaming data drifts | One `sports.yaml` that you edit | Recheck flags (F5) |
| Manual claude.ai republish | Auto-publish to Pages | — |
| Calendar sync only works in Cowork | `.ics` feeds (F3) | — |
| About 19 web searches per run | Structured feeds for about 10 Sports, the Season file for the rest | — |
| Two separate interfaces | One shared Hub | Shared favourites and reactions (later milestone) |

## 5. Assumptions, risks, unknowns

- **Unofficial data sources may change** (risk, high likelihood). The PWHL, World Aquatics, IBU and MotoGP feeds aren't official public APIs. Each fetcher checks the data's shape and fails loudly, which triggers F8. Saved sample data keeps the tests working offline.
- **Some sites block bots.** World Curling and curling.ca refuse automated requests, so those Sports rely on the Season file. The weekly check can't reach those two sites, so the Claude step reads other sources about them.
- **Claude on GitHub using Pro is confirmed.** Anthropic's GitHub Actions docs say a Claude Code login token (`CLAUDE_CODE_OAUTH_TOKEN`) works on Pro plans; you create it once on your Mac with `claude setup-token`. Two caveats: these runs use your Pro allowance, and one third-party source says the token expires after a year (not confirmed). The plan sets a renewal reminder and keeps an API key with a $2 cap as the fallback.
- **Gmail app password.** Gmail only allows app passwords when two-step verification is on. If you'd rather not enable it, the fallback is a free email service (e.g. Resend).
- **Public repo.** The code and both YAML files are visible to anyone; the Watch options are written neutrally.
- **Unknowns:**
  - ISU skating may parse or may need the Season file; we'll know in M2.
  - Several broadcast rights are unconfirmed for 2026-27 (see the watch guide).
  - We don't know why Make stopped sending the Digest. That doesn't matter now that it's being replaced.

## 6. Proposed architecture

```
sports-hub/
├── config/
│   ├── sports.yaml          # 19 Sports: name, category, source, Watch options, recheck flags
│   └── seasons/2026-27.yaml # Season file: hand-checked Events for the ~8 hard Sports
├── src/sports_hub/
│   ├── model.py             # Event / Sport dataclasses (UTC timestamps)
│   ├── fetchers/            # one module per source; all return list[Event]
│   │   ├── jolpica_f1.py  fis_ical.py  ibu.py  pwhl.py
│   │   ├── world_aquatics.py  motogp.py  six_nations.py  isu.py?
│   │   └── season_file.py   # reads config/seasons/*.yaml
│   ├── validate.py          # shape checks, date-safety guard, sudden drops in Event counts
│   ├── state.py             # last good data per Sport (committed to repo as JSON)
│   ├── build.py             # data.json + .ics feeds + copies site/
│   ├── notify.py            # Monday email + failure alert (SMTP)
│   └── check.py             # page fingerprints for the Season-file check
├── site/                    # index.html, app.js, style.css — vanilla JS reading data.json
├── tests/                   # pytest; fixtures = saved source responses
└── .github/workflows/
    ├── refresh.yml          # Mon + Thu: build → publish to Pages; Mon: Notification
    └── season-check.yml     # weekly: fingerprints → if changed, Claude Code compares → opens a review issue
```

**Python vs. Claude:**
- **Python, with no AI:** fetching structured sources, converting times, the 8-week and next-6 window rules, off-season labels, validation, HTML and `.ics` output, and emails. This is everything the old skill asked Claude to do *apart from* finding the schedules, and it's where the stale-date and drift problems came from.
- **Claude (Claude Code on your Pro plan):** only the weekly Season-file check, and only when a fingerprint changes or a curling site needs checking. It writes a review note, never the data.
- **Your judgement:** you approve Season-file changes and the Watch options.

**Dependencies:**
- `httpx` (web requests)
- `icalendar` (reads the FIS feeds and writes our `.ics` feeds)
- `pyyaml` (config files)
- `pytest` (tests, development only)

That's all. HTML is built with plain Python string templates, so no Jinja is needed.

## 7. Cost and performance measurement plan

**Old version (baseline), measured with you on one manual Cowork run:**
- Note your Pro usage meter (Settings → Usage) before and after the run.
- Time the run from start to finish.
- Count Events and check 10 random ones against the official sites.

Token counts aren't shown in Cowork, so tokens will be **estimated** from the run transcript length and clearly labelled as estimates.

**New version, measured over the two-week parallel run:**
- GitHub Actions minutes and run time per Refresh, from the Actions logs. This is free on a public repo.
- The Claude Code step's usage, from its run log, plus your Pro usage meter before and after that step.
- Any API dollars (expected $0).
- Accuracy: the same 10-Event spot check, plus a comparison of the old and new Event lists for the next 4 weeks.
- Reliability: how many scheduled runs succeeded, failure alerts sent, and stale Sports.

**Comparison method.** Both versions run in the same weeks. The comparison table separates **measured** from **estimated** numbers. Quality must be at least as good: the same 19 Sports and no missing Events in the overlap.

## 8. Milestones

Each one ends with tests passing and a stop for your OK.

1. **M1 — Data core (local).** Event model, `sports.yaml` skeleton, fetchers for **F1, FIS ×3 and IBU**, validation, date guard, `data.json` output.
   *Accept:* `python -m sports_hub build` writes `data.json` for 5 Sports with correct times; tests pass offline using saved data; a stale-date test refuses to build.
2. **M2 — All 19 Sports.**
   - Remaining fetchers: PWHL, Aquatics ×2, MotoGP, Six Nations, and an ISU attempt.
   - The 2026-27 Season file for the hard Sports.
   - Full Watch options from the research.
   - Last-good-data fallback.

   *Accept:* every Sport has upcoming Events or a "Returns" label; breaking one fetcher keeps that Sport's last good data and marks it stale.
3. **M3 — The Hub page.** Static site with filters, favourites, time-zone toggle, watch badges, `.ics` feeds and buttons, the ESPN+ banner and recheck flags. Visual style carried over from the current Hub.
   *Accept:* local preview works on desktop and phone; a checklist confirms parity with §2.
4. **M4 — GitHub and automation (guided).** Repo, Pages, Monday/Thursday schedule and failure alert, with a step-by-step setup walkthrough for you.
   *Accept:* two scheduled runs succeed and publish; a deliberately broken run emails you.
5. **M5 — Monday Notification** to you and Jason.
   *Accept:* a test email arrives in both inboxes and the content matches the Hub.
6. **M6 — Season-file check.** Fingerprints plus the Claude Code step, raising a review item.
   *Accept:* a deliberately changed fixture produces one clear review item; the Pro usage is recorded.
7. **M7 — Parallel run and handover.** Two weeks next to Cowork, the comparison table from §7, then Cowork is switched off.

**Later:** shared favourites, watchlist and reactions (needs shared storage; separate design).

## 9. Decisions needed before M1

1. Approve this brief, or tell me what to change.
2. **Look of the Hub:** carry over the current Hub's style (fonts, colours, layout), or refresh it in M3? *Recommend: carry over in M3, refresh later if you want.*
3. **Repo name:** `sports-hub`, which gives a link like `<your-username>.github.io/sports-hub`.
