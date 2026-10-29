"""The Season-file check's last step (tickets 32-33), with the fake mail sender (Seam 2)."""

from datetime import date

from conftest import FakeSender
from sports_hub.season_outcome import finish_check

MAIL = {
    "SPORTS_HUB_MAIL_USER": "hub.sender@example.com",
    "SPORTS_HUB_MAIL_APP_PASSWORD": "made-up",
    "SPORTS_HUB_ALERT_TO": "katie@example.com",
    "RUN_URL": "https://github.com/x/sports-hub/actions/runs/7",
    "CLAUDE_TOKEN_CREATED": "2026-10-28",
}


def outcome(today: date, check: str = "success", claude: str = "skipped", **extra: str) -> tuple[int, FakeSender]:
    sender = FakeSender()
    env = {**MAIL, "CHECK_RESULT": check, "CLAUDE_RESULT": claude, **extra}
    return finish_check(env, sender, today), sender


def test_a_quiet_week_sends_nothing() -> None:
    assert outcome(date(2026, 11, 4)) == (0, FakeSender())


def test_a_failed_claude_step_explains_how_to_renew_the_token() -> None:
    code, sender = outcome(date(2026, 11, 4), claude="failure")

    assert code == 1
    (message,) = sender.sent
    assert message.subject == "Sports Hub: the Claude check couldn't run"
    assert "claude setup-token" in message.text
    assert "CLAUDE_CODE_OAUTH_TOKEN" in message.text
    assert "fingerprint check still ran" in message.text
    assert "most likely" in message.text  # it can't know it was the token


def test_any_failed_later_step_is_reported_in_one_email() -> None:
    code, sender = outcome(date(2026, 11, 4), ISSUE_RESULT="failure", SAVE_RESULT="skipped")

    assert code == 1
    (message,) = sender.sent
    assert message.subject == "Sports Hub: part of the weekly Season-file check failed"
    assert "- opening or updating the review issue" in message.text
    assert "next week's check flags it again" in message.text
    assert "claude setup-token" not in message.text


def test_a_failed_post_is_reported_with_the_token_steps_when_claude_also_failed() -> None:
    _, sender = outcome(date(2026, 11, 4), claude="failure", POST_RESULT="failure")

    (message,) = sender.sent
    assert "- posting Claude's summary on the review issue" in message.text
    assert "claude setup-token" in message.text


def test_the_renewal_reminder_comes_once_eleven_months_on() -> None:
    weeks = [date(2027, 9, 22) + (date(2027, 9, 29) - date(2027, 9, 22)) * n for n in range(4)]  # four weekly runs

    sent = [outcome(day)[1].sent for day in weeks]

    reminders = [messages for messages in sent if messages]
    assert len(reminders) == 1
    assert reminders[0][0].subject == "Sports Hub: renew the Claude token by Oct 28, 2027"


def test_a_manual_run_in_the_reminder_week_does_not_send_it_again() -> None:
    assert outcome(date(2027, 9, 29), GITHUB_EVENT_NAME="workflow_dispatch")[1].sent == []
    assert len(outcome(date(2027, 9, 29), GITHUB_EVENT_NAME="schedule")[1].sent) == 1


def test_no_token_date_means_no_reminder() -> None:
    env_without = {k: v for k, v in MAIL.items() if k != "CLAUDE_TOKEN_CREATED"}
    sender = FakeSender()

    for n in range(52):
        finish_check({**env_without, "CHECK_RESULT": "success", "CLAUDE_RESULT": "skipped"}, sender,
                     date(2027, 1, 6) + (date(2027, 1, 13) - date(2027, 1, 6)) * n)

    assert sender.sent == []


def test_a_failed_fingerprint_check_is_reported() -> None:
    code, sender = outcome(date(2026, 11, 4), check="failure")

    assert code == 1
    assert sender.sent[0].subject == "Sports Hub: the weekly Season-file check failed"
