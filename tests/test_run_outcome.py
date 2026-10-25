"""The workflow's last email about a run (ticket 26), tested with the fake mail sender (Seam 2)."""

from conftest import FakeSender
from sports_hub.run_outcome import BUILT, BUILT_EMAIL_UNSENT, STOPPED_ALERTED, STOPPED_NOT_ALERTED, finish

MAIL = {
    "SPORTS_HUB_MAIL_USER": "hub.sender@example.com",
    "SPORTS_HUB_MAIL_APP_PASSWORD": "made-up",
    "SPORTS_HUB_ALERT_TO": "katie@example.com",
    "RUN_URL": "https://github.com/x/sports-hub/actions/runs/1",
}


def outcome(code: int | None, publish: str = "success", save: str = "success") -> tuple[int, FakeSender]:
    sender = FakeSender()
    env = {**MAIL, "REFRESH_CODE": "" if code is None else str(code), "PUBLISH_RESULT": publish, "SAVE_RESULT": save}
    return finish(env, sender), sender


def test_a_good_run_sends_nothing_and_passes() -> None:
    assert outcome(BUILT) == (0, FakeSender())


def test_a_failure_before_the_refresh_ran_is_emailed() -> None:
    code, sender = outcome(None, publish="skipped", save="skipped")

    assert code == 1
    (message,) = sender.sent
    assert message.subject == "Sports Hub: the scheduled run failed"
    assert "installing or testing" in message.text
    assert "https://github.com/x/sports-hub/actions/runs/1" in message.text


def test_a_stopped_refresh_that_already_emailed_is_not_emailed_again() -> None:
    code, sender = outcome(STOPPED_ALERTED, publish="skipped", save="skipped")

    assert (code, sender.sent) == (1, [])


def test_a_stopped_refresh_whose_email_failed_gets_one_now() -> None:
    code, sender = outcome(STOPPED_NOT_ALERTED, publish="skipped", save="skipped")

    assert code == 1
    assert sender.sent[0].subject == "Sports Hub: not updated"


def test_publishing_failing_after_a_good_refresh_says_exactly_that() -> None:
    code, sender = outcome(BUILT, publish="failure")

    assert code == 1
    (message,) = sender.sent
    assert message.subject == "Sports Hub: refreshed, but not fully published"
    assert "publishing failed" in message.text
    assert "wasn't updated" not in message.text  # doesn't contradict the Alert email


def test_an_unsent_alert_fails_the_run_without_another_email() -> None:
    code, sender = outcome(BUILT_EMAIL_UNSENT)

    assert (code, sender.sent) == (1, [])


def test_missing_mail_settings_never_crash_the_last_step() -> None:
    code = finish({"REFRESH_CODE": "", "RUN_URL": "x"}, FakeSender())

    assert code == 1
