# 25: Failure-alert email

**What to build:** When a Refresh raises Alerts, or stops entirely (the date-safety guard, a broken config or Season file, or an unreadable last-good state), Katie gets one plain-English email listing what went wrong and what to do. Sending goes through a small mail sender with two implementations: a real one that sends from Katie's Gmail with an app password, and an in-memory fake for tests (Seam 2). The Gmail address and app password come only from environment variables (GitHub secrets) and never appear in logs or messages.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The Refresh command can send alerts when asked to. Locally it stays quiet unless the mail settings are present, and when they're missing it says so plainly instead of failing.
- [x] A Refresh with error or warning Alerts sends exactly one email to the alert recipient. The subject says how many problems there are. The body lists each Sport and its reason in plain words, plus the link to the live Hub.
- [x] A stopped Refresh (date guard, ConfigError, StateError) sends an email saying the Hub wasn't updated and why, and the command still exits with an error.
- [x] A clean Refresh with no Alerts sends nothing.
- [x] The mail settings are read from environment variables named in the README. Their values never appear in output, logs, email bodies or exceptions.
- [x] Tests use the fake mail sender (Seam 2), together with the Refresh entry point where needed. They cover: alerts produce one email with the right content; a clean run sends none; a stopped run sends a "not updated" email; secrets never appear in what's sent or printed.
- [x] If Gmail refuses to send (wrong password, network down), the command prints a clear error, and the run still fails visibly, so GitHub's own failure email reaches Katie as a backstop.

## Comments

**2026-10-24 (review fixes):**
- If `--send-alerts` is given but the mail settings are missing, the Hub is now still built and published, and the command exits 3 so the run shows red. It no longer stops before building.
- The module is renamed `alert_mail`, so it doesn't clash with the glossary's Notification.
- The fake sender moved to the tests.
- The secrets test now checks every email that was actually sent, plus all printed output, for the password and both addresses.
