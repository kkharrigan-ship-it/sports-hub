# 28: Go-live check

**What to build:** Proof that Milestone 4 works for real:
- two scheduled runs succeed and update the live Hub
- one deliberately broken run emails Katie
- the run times from GitHub's logs are recorded for the cost comparison
- Katie's hand test of the calendar files is done against the live link

**Blocked by:** 27 (Guided setup wizard)

**Status:** ready-for-agent

- [x] Two scheduled runs (not manual) complete successfully. The live Hub's "Updated" date changes each time.
- [x] A deliberate break (e.g. a temporarily broken Season file entry on a test branch, or a manual run with a fault switch) produces an alert email in Katie's inbox within a few minutes. The Hub keeps its last good version.
- [x] Each run's duration and GitHub Actions minutes are recorded in the measurement notes. The repo is public, so this costs $0.
- [x] Katie subscribes to one Sport's feed from the live Hub in her calendar app, and adds one "+ cal" Event to Apple Calendar and one to Google Calendar. Ticket 22's pending check is ticked.
- [x] Anything that went wrong during go-live is written up with its fix.

## Comments

**2026-10-25:**
- The first run failed in setup: `astral-sh/setup-uv@v10` doesn't exist. Katie got the "failed before the Refresh could start" email, as designed.
- Fixed by pinning `v10.3.2`.
- The second (manual) run passed all four jobs. The Hub is live at https://kkharrigan-ship-it.github.io/sports-hub/ with 19 Sports, and the feeds are served.
- Still to do: two *scheduled* runs (the first is Mon 2026-10-26), the deliberate-break test, and Katie's calendar hand test.

**2026-10-25 (break test):**
- Run 40214138052 on a throwaway `break-test` branch used a Season-file entry with its date removed.
- The tests caught it, which is earlier than the Refresh's own config check, so a bad hand edit can't reach the Hub.
- Publish and save were skipped; the finish job logged "Failure email sent."; the live Hub kept its last good version.
- The branch has been deleted. Katie confirmed the email arrived (2026-10-25).

**2026-10-25:** Katie completed the calendar checks on the live Hub (Subscribe, plus "+ cal" in Apple and Google Calendar).

**2026-10-26:** The first scheduled run (Monday) succeeded. GitHub started it about 6 hours late (17:11 UTC) because scheduled runs are best-effort. The second scheduled run is Thursday 2026-10-29.

**2026-10-31:** The Thursday run (40885982704) succeeded, so that's two scheduled runs. The live Hub's Last-Modified header reads 13:54 UTC on 2026-10-29, inside that run. Both scheduled runs started about 6-7 hours late; moving the slot to 07:00 UTC is what brought Thursday's in before 14:00 UTC. Timings are in `docs/research/measurements.md`. Ticket 28 is complete.
