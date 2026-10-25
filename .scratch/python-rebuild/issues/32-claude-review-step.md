# 32: Claude review step

**What to build:** When the fingerprint check finds changed pages, and also for the curling Sports it can't check directly, the weekly check runs Claude Code on GitHub, signed in with Katie's Pro subscription token. Claude compares those Sports' Season-file entries against their sources (and other reputable sources for the curling bodies) and adds a plain summary to the review issue: which dates or venues differ, with links. It is read-only: it can comment on the issue but never edits files, commits or pushes.

**Blocked by:** 31 ("This page changed" fingerprints)

**Status:** ready-for-agent

- [ ] The Claude step runs only when there's something to review (changed pages, or a curling Sport with an Event in the next 8 weeks). An ordinary quiet week uses no Pro allowance.
- [ ] Claude's permissions on GitHub allow reading the repo and commenting on issues only, enforced by the workflow's permissions, not just by instructions.
- [ ] The instructions to Claude say to treat web pages as data, quote what changed, link sources, and never guess a date.
- [ ] The Claude Code token is added as a secret through the wizard (Katie creates it with `claude setup-token` on her Mac), never shown or committed.
- [ ] Each run's Claude usage, as reported in the run log, is recorded in the measurement notes alongside Katie's Pro usage meter before and after the first run.
- [ ] A deliberately changed saved page (on a test branch) produces one review issue with a sensible Claude summary.
