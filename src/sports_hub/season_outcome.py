"""The weekly Season-file check's last step: emails Katie only when she needs to act.

- The fingerprint check itself failed: say so, with the log link.
- Any later step failed (opening the issue, saving fingerprints, Claude, posting
  its summary): one email naming them. If Claude was one, the likeliest cause
  is its login token, so it explains how to renew it.
- About a month before the token's expected one-year expiry: one reminder. It's
  stateless: only the scheduled run that lands in that one week sends it (a
  manual run that week doesn't, so it can't arrive twice).

Standard library plus sports_hub.mail only, like run_outcome.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Mapping

from sports_hub.mail import GmailSender, MailError, MailSender, MailSettings, Message

TOKEN_LIFETIME = timedelta(days=365)       # unconfirmed; one source says a year
REMIND_BEFORE = timedelta(days=30)
CHECK_INTERVAL = timedelta(days=7)         # the check runs weekly
CLAUDE_STEP = "Claude comparing the flagged entries with their sources"
STEPS = [
    ("ISSUE_RESULT", "opening or updating the review issue"),
    ("SAVE_RESULT", "saving this week's fingerprints"),
    ("CLAUDE_RESULT", CLAUDE_STEP),
    ("POST_RESULT", "posting Claude's summary on the review issue"),
]
RENEW_STEPS = (
    "1. In Terminal on your Mac, run:  claude setup-token\n"
    "2. Sign in when it asks, and copy the token it prints.\n"
    "3. Run:  gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo {repo}\n"
    "   and paste the token when asked (it's hidden as you paste).\n"
    "4. Run:  gh variable set CLAUDE_TOKEN_CREATED --repo {repo} --body YYYY-MM-DD\n"
    "   with today's date, so the next reminder comes at the right time.\n"
)


def finish_check(env: Mapping[str, str], sender: MailSender | None, today: date) -> int:
    run_url = env.get("RUN_URL", "")
    renew_steps = RENEW_STEPS.format(repo=env.get("GITHUB_REPOSITORY", "<owner>/sports-hub"))
    if env.get("CHECK_RESULT") != "success":
        _send(sender, env, "Sports Hub: the weekly Season-file check failed",
              f"The weekly check of the Season file's source pages didn't finish.\n\nWhat happened: {run_url}\n")
        return 1
    failed = [step for key, step in STEPS if env.get(key) == "failure"]
    if failed == [CLAUDE_STEP]:
        _send(sender, env, "Sports Hub: the Claude check couldn't run",
              "This week's fingerprint check still ran and opened its review, but the Claude step that compares dates "
              "failed. The most likely reason is that its login token (the CLAUDE_CODE_OAUTH_TOKEN secret) has expired "
              "or been revoked; it could also be a passing GitHub or Claude outage. The log below says which.\n\n"
              f"If it's the token, here's how to renew it:\n{renew_steps}\nWhat happened: {run_url}\n")
        return 1
    if failed:
        renew = (f"\nIf the Claude step failed because of its login token, here's how to renew it:\n{renew_steps}"
                 if CLAUDE_STEP in failed else "")
        _send(sender, env, "Sports Hub: part of the weekly Season-file check failed",
              "The pages were checked, but these steps failed:\n"
              + "".join(f"- {step}\n" for step in failed)
              + "\nFingerprints are only saved once the review issue is open, so a changed page is never forgotten: "
              f"if the issue couldn't be opened, next week's check flags it again.\n{renew}\nWhat happened: {run_url}\n")
        return 1

    created = _date(env.get("CLAUDE_TOKEN_CREATED"))
    if created and env.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        remind_on = created + TOKEN_LIFETIME - REMIND_BEFORE
        if remind_on <= today < remind_on + CHECK_INTERVAL:
            expires = created + TOKEN_LIFETIME
            _send(sender, env, f"Sports Hub: renew the Claude token by {expires.strftime('%b')} {expires.day}, {expires.year}",
                  "The token that lets Claude check the Season file each week was created on "
                  f"{created.isoformat()} and is expected to stop working around {expires.isoformat()}.\n\nTo renew it:\n{renew_steps}")
    return 0


def _send(sender: MailSender | None, env: Mapping[str, str], subject: str, text: str) -> None:
    try:
        settings = MailSettings.from_env(env)
    except MailError as exc:
        print(f"No email sent: {exc}.")
        return
    try:
        (sender or GmailSender(settings)).send(Message(to=settings.alert_to, subject=subject, text=text))
        print("Email sent.")
    except MailError as exc:
        print(f"Couldn't send the email: {exc}")


def _date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None
