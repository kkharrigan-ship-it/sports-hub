"""How a scheduled run ended, and the last email the workflow sends about it.

The Refresh command reports what happened with its exit code. After every
other step has run (publishing, saving state), the workflow's final job calls
`finish()` with each job's result. It emails Katie only about what she hasn't
already heard, in words that match what actually happened, and fails the run
whenever something went wrong so GitHub shows it in red.

Standard library plus sports_hub.mail only: this must work even when
installing the project failed.
"""

from __future__ import annotations

from typing import Mapping

from sports_hub.mail import GmailSender, MailError, MailSender, MailSettings, Message

# Exit codes of `sports-hub refresh`.
BUILT = 0                  # the Hub was built; any Alerts were emailed
STOPPED_ALERTED = 1        # stopped before building; Katie was emailed why
STOPPED_NOT_ALERTED = 2    # stopped before building; the email couldn't be sent (or isn't set up)
BUILT_EMAIL_UNSENT = 3     # the Hub was built, but an Alert email or the Notification couldn't be sent (or isn't set up)

BUILT_CODES = (BUILT, BUILT_EMAIL_UNSENT)


def finish(env: Mapping[str, str], sender: MailSender | None) -> int:
    """Read the run's results from the environment, send at most one email, return the exit code.

    Expects BUILD_RESULT, PUBLISH_RESULT and SAVE_RESULT (GitHub job results:
    success, failure, cancelled or skipped), REFRESH_CODE (the Refresh's exit
    code, empty if it never ran) and RUN_URL.
    """
    code = _int(env.get("REFRESH_CODE"))
    run_url = env.get("RUN_URL", "")
    later_failed = [name for name, key in (("publishing", "PUBLISH_RESULT"), ("saving the state", "SAVE_RESULT"))
                    if env.get(key) == "failure"]

    if code is None:
        subject = "Sports Hub: the scheduled run failed"
        text = ("The run failed before the Refresh could start (installing or testing), so the Hub wasn't updated. "
                "It's still showing the last good version.")
    elif code == STOPPED_NOT_ALERTED:
        subject = "Sports Hub: not updated"
        text = "The Refresh stopped, so the Hub wasn't updated. It's still showing the last good version."
    elif code in BUILT_CODES and later_failed:
        subject = "Sports Hub: refreshed, but not fully published"
        text = (f"Today's Refresh worked, but {' and '.join(later_failed)} failed, "
                "so the live Hub may still show the previous version.")
    else:
        # Nothing new to tell Katie: all went well, she's already been emailed,
        # or email itself is what's broken (the run still shows red).
        ok = code == BUILT and not later_failed
        return 0 if ok else 1

    _send(sender, env, subject, f"{text}\n\nWhat happened (GitHub's log): {run_url}\n")
    return 1


def _send(sender: MailSender | None, env: Mapping[str, str], subject: str, text: str) -> None:
    try:
        settings = MailSettings.from_env(env)
    except MailError as exc:
        print(f"No failure email sent: {exc}. GitHub's own failure email still goes out.")
        return
    try:
        (sender or GmailSender(settings)).send(Message(to=settings.alert_to, subject=subject, text=text))
        print("Failure email sent.")
    except MailError as exc:
        print(f"Couldn't send the failure email: {exc}")


def _int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None
