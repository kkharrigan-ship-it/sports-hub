# Sports Hub

A shared schedule of 19 sports. It refreshes itself twice a week and is published as a web page with calendar feeds.

- **What it is and why:** [CONTEXT.md](CONTEXT.md) (vocabulary and decisions) and [.scratch/python-rebuild/design-brief.md](.scratch/python-rebuild/design-brief.md).
- **Where watch options come from:** [docs/research/watch-guide-2026-27.md](docs/research/watch-guide-2026-27.md).
- **Hand-checked dates:** [config/seasons/2026-27.yaml](config/seasons/2026-27.yaml). You can edit this file; the top of it explains how.

## How it runs

GitHub runs the **Refresh** workflow (`.github/workflows/refresh.yml`) every **Monday and Thursday at 07:00 UTC**: 2am in Memphis in summer, 1am in winter. It's early on purpose: GitHub can start scheduled runs hours late, and this still gets the Monday email out before breakfast. The workflow has four jobs, each with only the permissions it needs:

1. **build:** installs the project, runs the tests (a failing test stops everything), then fetches every Sport and builds the Hub: the page, `data.json` and one calendar feed per Sport. On Mondays it also emails the week's highlights (the Notification), at most once per Monday
2. **publish:** puts the Hub on GitHub Pages
3. **save:** commits the last-good state (`state/last_good.json`) back into the repo
4. **finish:** emails Katie about anything she hasn't already heard, and marks the run red if something went wrong

**To run it by hand:** go to the repo's **Actions** tab, choose **Refresh**, then **Run workflow**. Past runs and their logs are listed on the same page.

**If something goes wrong,** Katie gets one email that says what actually happened:

| What happened | Email | The Hub |
|---|---|---|
| Some Sports' sources failed | "N problems in the … Refresh", listing each one | Updated; those Sports show last-good Events, marked stale |
| The Refresh stopped (bad config, a date problem, unreadable state) | "not updated", with the reason | Unchanged |
| Installing or testing failed | "the scheduled run failed", with a link to the log | Unchanged |
| The Refresh worked but publishing or saving failed | "refreshed, but not fully published" | May still show the previous version |
| The alert email itself couldn't be sent | None (mail is what's broken); the run is marked red | Updated |

As a backstop, GitHub also emails the repo owner whenever a scheduled run fails.

### The weekly Season-file check

A second workflow, **Season-file check** (`.github/workflows/season-check.yml`), runs every **Wednesday at 07:00 UTC**:

1. It visits each page the Season file cites, and compares a fingerprint of the page's text with last week's.
2. If a page changed, it opens one GitHub issue labelled **season-review**, or adds to the open one, listing the page and the upcoming Season-file entries that cite it. Sites that block automated visitors can't be fingerprinted, so each of their events gets two looks instead: the week it comes within 8 weeks, and the week it's two weeks away. A quiet week opens nothing and uses no Claude allowance.
3. If the Claude token is set up, Claude compares those entries with their sources and posts a summary on the issue. It can only read web pages, the review and the Season file (no git credentials are left on disk), so it can't change or leak anything.
4. Nothing in the Season file changes automatically. Fix any date that moved, then close the issue.
5. If any step fails, Katie gets one email saying which. Fingerprints are only saved once the issue is open, so a change is never lost.

To give the check its Claude login (once, and again roughly yearly):

```bash
bash scripts/claude-token-wizard.sh
```

## Secrets

Secrets live only in the repo's **Settings → Secrets and variables → Actions**. Their values are never written to files, logs or emails.

| Name | What it holds |
|---|---|
| `SPORTS_HUB_MAIL_USER` | The Gmail address the Hub sends from |
| `SPORTS_HUB_MAIL_APP_PASSWORD` | A Gmail **app password** for that account (needs Google 2-Step Verification) |
| `SPORTS_HUB_ALERT_TO` | Who gets failure alerts (comma-separated) |
| `SPORTS_HUB_NOTIFY_TO` | Who gets the Monday Notification (comma-separated; sent as Bcc, so nobody sees the others' addresses) |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Pro login token for the weekly Season-file check (from `claude setup-token`) |

Plus one repo **variable** (not secret): `CLAUDE_TOKEN_CREATED`, the date the token was made. A reminder email goes out about a month before its expected one-year expiry.

The guided setup walks through creating the repo, turning on Pages and adding these secrets. Run it from the project folder:

```bash
bash scripts/setup-wizard.sh
```

## Working on it locally

Needs [uv](https://docs.astral.sh/uv/), which installs Python 3.12 itself.

```bash
export UV_PROJECT_ENVIRONMENT=.venv.nosync   # keeps the virtualenv out of iCloud sync
uv sync
uv run pytest -q                              # tests use saved responses, no network
uv run mypy                                   # type checks
uv run sports-hub refresh --out dist          # a live Refresh into ./dist
python3 -m http.server 8765 --directory dist  # then open http://127.0.0.1:8765
```

Add `?now=2026-11-03T15:00:00Z` to the page's address to see it as it would look at another time.
