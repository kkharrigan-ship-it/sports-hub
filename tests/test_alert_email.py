"""Alert emails (ticket 25), tested with the fake mail sender (Seam 2).

The command-line Refresh is run with a fixed "today", the saved-response
internet and a fake mail sender, so nothing is really fetched or sent.
"""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from conftest import FakeInternet, FakeSender
from sports_hub.cli import run
from sports_hub.run_outcome import BUILT, BUILT_EMAIL_UNSENT, STOPPED_ALERTED, STOPPED_NOT_ALERTED

TODAY = date(2026, 10, 24)
SECRET = "abcd efgh ijkl mnop"  # a made-up app password; it must never be printed or sent
ENV = {
    "SPORTS_HUB_MAIL_USER": "hub.sender@example.com",
    "SPORTS_HUB_MAIL_APP_PASSWORD": SECRET,
    "SPORTS_HUB_ALERT_TO": "katie@example.com",
    "SPORTS_HUB_URL": "https://example.github.io/sports-hub/",
}


def refresh_cli(tmp_path: Path, client: httpx.Client, sender: FakeSender, *, env: dict[str, str] = ENV,
                today: date = TODAY, send_alerts: bool = True) -> int:
    argv = ["refresh", "--out", str(tmp_path / "hub"), "--state", str(tmp_path / "state.json")]
    if send_alerts:
        argv.append("--send-alerts")
    return run(argv, today=today, client=client, env=env, sender=sender)


def test_a_clean_refresh_sends_nothing(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender) == BUILT
    assert sender.sent == []


def test_alerts_send_one_plain_email_to_katie(tmp_path: Path, client: httpx.Client, internet: FakeInternet) -> None:
    internet.break_host("www.fis-ski.com")
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender) == BUILT

    (message,) = sender.sent
    assert message.to == ("katie@example.com",)
    assert message.subject == "Sports Hub: 3 problems in the Sat, Oct 24 Refresh"
    assert "Alpine Skiing: couldn't reach www.fis-ski.com" in message.text
    assert "https://example.github.io/sports-hub/" in message.text
    assert "still updated" in message.text


def test_a_stopped_refresh_says_the_hub_was_not_updated(tmp_path: Path, client: httpx.Client) -> None:
    (tmp_path / "state.json").write_text(json.dumps({"refreshed_on": "2026-12-31", "sports": {}}))
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender) == STOPPED_ALERTED

    (message,) = sender.sent
    assert message.subject == "Sports Hub: not updated on Sat, Oct 24"
    assert "the last Refresh was 2026-12-31" in message.text
    assert not (tmp_path / "hub").exists()


def test_an_unreadable_state_file_is_explained(tmp_path: Path, client: httpx.Client) -> None:
    (tmp_path / "state.json").write_text("not json")
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender) == STOPPED_ALERTED
    assert "delete it to start fresh" in sender.sent[0].text


def test_without_the_flag_nothing_is_sent_even_with_settings(tmp_path: Path, client: httpx.Client,
                                                             internet: FakeInternet) -> None:
    internet.break_host("www.fis-ski.com")
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender, send_alerts=False) == BUILT
    assert sender.sent == []


def test_missing_mail_settings_still_build_the_hub_and_say_so(tmp_path: Path, client: httpx.Client,
                                                              capsys: pytest.CaptureFixture[str]) -> None:
    sender = FakeSender()

    code = refresh_cli(tmp_path, client, sender, env={"SPORTS_HUB_MAIL_USER": "x@example.com"})

    assert code == BUILT_EMAIL_UNSENT
    assert (tmp_path / "hub" / "index.html").exists()
    err = capsys.readouterr().err
    assert "SPORTS_HUB_MAIL_APP_PASSWORD" in err and "SPORTS_HUB_ALERT_TO" in err
    assert sender.sent == []


def test_when_gmail_refuses_the_hub_is_still_built(tmp_path: Path, client: httpx.Client, internet: FakeInternet,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    internet.break_host("www.fis-ski.com")

    assert refresh_cli(tmp_path, client, FakeSender(refuse=True)) == BUILT_EMAIL_UNSENT
    assert (tmp_path / "hub" / "data.json").exists()
    assert "couldn't send the email \"Sports Hub: 3 problems" in capsys.readouterr().err


def test_a_stopped_refresh_whose_email_fails_says_so_in_its_code(tmp_path: Path, client: httpx.Client) -> None:
    (tmp_path / "state.json").write_text("not json")

    assert refresh_cli(tmp_path, client, FakeSender(refuse=True)) == STOPPED_NOT_ALERTED


def test_secrets_and_addresses_never_appear_in_output_or_email(tmp_path: Path, client: httpx.Client,
                                                               internet: FakeInternet,
                                                               capsys: pytest.CaptureFixture[str]) -> None:
    sender = FakeSender()
    internet.break_host("www.fis-ski.com")
    refresh_cli(tmp_path, client, sender)  # an Alert email
    refresh_cli(tmp_path, client, FakeSender(refuse=True))  # a refused send
    (tmp_path / "state.json").write_text("not json")
    refresh_cli(tmp_path, client, sender)  # a not-updated email

    assert len(sender.sent) == 2
    printed = capsys.readouterr()
    emails = "".join(m.subject + m.text for m in sender.sent)
    assert SECRET not in printed.out + printed.err + emails
    for address in ("hub.sender@example.com", "katie@example.com"):
        assert address not in printed.out + printed.err
        assert address not in emails
