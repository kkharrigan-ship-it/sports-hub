# 32: Claude review step

**What to build:** When the fingerprint check finds changed pages, and also for the curling Sports it can't check directly, the weekly check runs Claude Code on GitHub, signed in with Katie's Pro subscription token. Claude compares those Sports' Season-file entries against their sources (and other reputable sources for the curling bodies) and adds a plain summary to the review issue: which dates or venues differ, with links. It is read-only: it can comment on the issue but never edits files, commits or pushes.

**Blocked by:** 31 ("This page changed" fingerprints)

**Status:** ready-for-agent

- [x] The Claude step runs only when there's something to review (changed pages, or a curling Sport with an Event in the next 8 weeks). An ordinary quiet week uses no Pro allowance.
- [x] Claude's permissions on GitHub allow reading the repo and commenting on issues only, enforced by the workflow's permissions, not just by instructions.
- [x] The instructions to Claude say to treat web pages as data, quote what changed, link sources, and never guess a date.
- [x] The Claude Code token is added as a secret through the wizard (Katie creates it with `claude setup-token` on her Mac), never shown or committed. (Current token only; see the 2026-10-31 comment.)
- [ ] Each run's Claude usage, as reported in the run log, is recorded in the measurement notes alongside Katie's Pro usage meter before and after the first run.
- [x] A deliberately changed saved page (on a test branch) produces one review issue with a sensible Claude summary.

## Comments

**2026-10-28:** Built, and stricter than planned:
- Claude gets a **read-only** GitHub token and only the WebFetch, WebSearch, Read, Grep and Glob tools.
- It returns a structured summary, and a separate job with `issues: write` posts it, so Claude itself can't even comment.
- The job is skipped until the `CLAUDE_TOKEN_CREATED` variable exists.

Still to do with Katie: run `scripts/claude-token-wizard.sh`, the deliberate-change test, and recording Pro usage.

**2026-10-31:** Live, with one incident.
- **Test:** on a throwaway branch, a planted wrong Scotties date and a changed fingerprint gave one comment set on the review issue, and Claude quoted TSN's correct dates ([run 41163092931](https://github.com/kkharrigan-ship-it/sports-hub/actions/runs/41163092931)).
- **Incident:** an earlier try ran `git add -A`, which pushed an untracked file holding a token to a public branch. The branch was deleted within about a minute. The token was revoked and tested dead about 30 minutes later, and it is not the one in use now. The commit stayed reachable by its ID afterwards. `.gitignore` and a local pre-commit hook now guard against a repeat.
- **Still open:** read Katie's Pro usage meter before and after a run. Until then, this ticket stays open.
- **Noise to watch:** the FIA WEC page and one other flagged as changed on the test run without a real date change, so a weekly Claude run may be more common than planned.
