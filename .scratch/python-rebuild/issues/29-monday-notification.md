# 29: Monday Notification email

**What to build:** Each Monday's Refresh sends one Notification email to Katie and Jason. It covers the next 7 days:
- Events grouped by day, with times in CST
- same-Sport, same-day sessions on one line, as the old Digest did (e.g. "Formula 1, Mexico City GP: Practice 3 & Qualifying")
- each line's best-ranked Watch option
- the ESPN+ Reminder if one is due that week
- a link to the Hub

On a quiet week it says so warmly and names the next Event coming up. Thursday Refreshes send no Notification.

**Blocked by:** 25 (Failure-alert email), 26 (The GitHub workflow)

**Status:** ready-for-agent

- [x] The Notification is built from the Refresh's own data, so it always matches the Hub.
- [x] It goes out only on Monday runs (by the Refresh's "today" in Memphis), to the recipients in a secret, sent individually or as BCC so neither person's address is shown to the other.
- [x] It is plain text with a simple readable layout (so there is nothing to escape) and no tracking images.
- [x] Days with nothing on are skipped. A week with nothing at all gives the warm "nothing on, next up is…" wording.
- [x] If the Refresh had Alerts, the Notification still goes out (with fresh and last-good Events), and Katie's separate failure-alert email covers the problems.
- [x] Tests use the fake mail sender (Seam 2) and the Refresh entry point with saved responses. They cover: a Monday sends one Notification; a Thursday sends none; grouping of same-day sessions; times in CST across a daylight-saving change; quiet-week wording; no addresses or secrets in the output.

## Comments

**2026-10-25 (review):**
- **Duplicate protection.** The build job now reads the newest saved state from `main` before the Refresh. A "Re-run" or a queued manual run on a Monday therefore sees that the Notification already went out. If the save job itself failed, a later Monday run could still repeat it, which is rare and acceptable.
- **Line format.** Lines read "Formula 1: Mexico City Grand Prix (Practice 3 & Qualifying)". The ticket's example used a slightly different punctuation; this one matches the Hub.
