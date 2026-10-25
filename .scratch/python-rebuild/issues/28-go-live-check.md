# 28: Go-live check

**What to build:** Proof that Milestone 4 works for real:
- two scheduled runs succeed and update the live Hub
- one deliberately broken run emails Katie
- the run times from GitHub's logs are recorded for the cost comparison
- Katie's hand test of the calendar files is done against the live link

**Blocked by:** 27 (Guided setup wizard)

**Status:** ready-for-agent

- [ ] Two scheduled runs (not manual) complete successfully. The live Hub's "Updated" date changes each time.
- [ ] A deliberate break (e.g. a temporarily broken Season file entry on a test branch, or a manual run with a fault switch) produces an alert email in Katie's inbox within a few minutes. The Hub keeps its last good version.
- [ ] Each run's duration and GitHub Actions minutes are recorded in the measurement notes. The repo is public, so this costs $0.
- [ ] Katie subscribes to one Sport's feed from the live Hub in her calendar app, and adds one "+ cal" Event to Apple Calendar and one to Google Calendar. Ticket 22's pending check is ticked.
- [ ] Anything that went wrong during go-live is written up with its fix.

## Comments

**2026-10-25:**
- The first run failed in setup: `astral-sh/setup-uv@v10` doesn't exist. Katie got the "failed before the Refresh could start" email, as designed.
- Fixed by pinning `v10.3.2`.
- The second (manual) run passed all four jobs. The Hub is live at https://kkharrigan-ship-it.github.io/sports-hub/ with 19 Sports, and the feeds are served.
- Still to do: two *scheduled* runs (the first is Mon 2026-10-26), the deliberate-break test, and Katie's calendar hand test.
