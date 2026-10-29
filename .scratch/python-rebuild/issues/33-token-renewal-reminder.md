# 33: Claude token renewal reminder

**What to build:** Katie gets an alert email about a month before the Claude Code token's expected expiry (one unconfirmed source says the token lasts a year). If the token stops working earlier, the weekly check fails with a clear alert saying how to renew it, never silently.

**Blocked by:** 32 (Claude review step)

**Status:** ready-for-agent

- [ ] The date the token was created is recorded (not the token itself) when it's added through the wizard.
- [x] From 11 months after that date, the weekly check emails one reminder (not one every week) with the renewal steps.
- [x] A rejected token produces an alert email naming the problem and the fix, and the rest of the check (fingerprints) still runs.
- [x] Tests use the fake mail sender and a fixed "today" for the reminder timing and the rejected-token message.

## Comments

**2026-10-28:** The reminder is stateless: only the weekly run that falls in the one week 11 months after `CLAUDE_TOKEN_CREATED` sends it (tested over four weeks). A failed Claude step sends an alert with the renewal steps. The token date gets recorded by the token wizard.
