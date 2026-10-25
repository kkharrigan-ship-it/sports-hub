"""The Monday Notification to Katie and Jason (ticket 29), via the CLI with the fake mail sender (Seam 2)."""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from conftest import FakeInternet, FakeSender
from sports_hub.cli import run
from sports_hub.mail import Message
from sports_hub.run_outcome import BUILT, BUILT_EMAIL_UNSENT

MONDAY = date(2026, 10, 26)
ENV = {
    "SPORTS_HUB_MAIL_USER": "hub.sender@example.com",
    "SPORTS_HUB_MAIL_APP_PASSWORD": "made-up app password",
    "SPORTS_HUB_ALERT_TO": "katie@example.com",
    "SPORTS_HUB_NOTIFY_TO": "katie@example.com, jason@example.com",
    "SPORTS_HUB_URL": "https://example.github.io/sports-hub/",
}


def refresh_cli(tmp_path: Path, client: httpx.Client, sender: FakeSender, today: date = MONDAY,
                env: dict[str, str] = ENV) -> int:
    argv = ["refresh", "--out", str(tmp_path / "hub"), "--state", str(tmp_path / "state.json"),
            "--send-alerts", "--send-notification"]
    return run(argv, today=today, client=client, env=env, sender=sender)


def notification(sender: FakeSender) -> Message:
    (message,) = [m for m in sender.sent if m.subject.startswith("🏅")]
    return message


def test_monday_sends_one_notification_to_both(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender) == BUILT

    message = notification(sender)
    assert message.to == ("katie@example.com", "jason@example.com")
    assert message.subject == "🏅 What's on this week: Sports Hub, Oct 26"
    assert "https://example.github.io/sports-hub/" in message.text


def test_thursday_sends_no_notification(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender, today=date(2026, 10, 29)) == BUILT
    assert sender.sent == []


def test_a_second_run_on_the_same_monday_does_not_repeat_it(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)
    refresh_cli(tmp_path, client, sender)

    assert len([m for m in sender.sent if m.subject.startswith("🏅")]) == 1


def test_same_day_sessions_share_a_line_with_central_times_across_the_clock_change(
    tmp_path: Path, client: httpx.Client
) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)
    text = notification(sender).text

    # Sat Oct 31 is still daylight time (CDT); Sun Nov 1 the clocks have gone back (CST).
    saturday = text[text.index("SAT, OCT 31"):text.index("SUN, NOV 1")]
    assert "Formula 1: Mexico City Grand Prix (Practice 3 & Qualifying)" in saturday
    assert "12:30 PM & 4:00 PM" in saturday
    sunday = text[text.index("SUN, NOV 1"):]
    assert "Formula 1: Mexico City Grand Prix (Race)" in sunday
    assert "2:00 PM" in sunday
    assert "📺 Apple TV" in saturday


def test_days_with_nothing_on_are_skipped(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)

    # Layout: a day heading between two rule lines, then that day's Events.
    lines = notification(sender).text.splitlines()
    headings = [i for i, line in enumerate(lines) if line.isupper() and ", " in line]
    assert headings, "expected at least one day"
    for i in headings:
        assert lines[i - 1].startswith("───") and lines[i + 1].startswith("───")
        assert lines[i + 2].strip() and not lines[i + 2].startswith("───"), f"{lines[i]} has no Events"


def test_multi_day_events_appear_once_with_their_dates(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)
    text = notification(sender).text

    assert text.count("European Curling Championships") == 1
    assert "Tue, Oct 27 – Sun, Nov 1" in text


def test_a_quiet_week_names_what_comes_next(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender, today=date(2027, 12, 20))

    text = notification(sender).text
    assert "Nothing on this week" in text


def test_the_espn_reminder_is_mentioned_in_its_week(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)

    # The Masters starts Nov 3; its reminder starts Oct 27, inside this week.
    assert "ESPN+" in notification(sender).text and "GSOC Masters" in notification(sender).text


def test_alerts_do_not_stop_the_notification(tmp_path: Path, client: httpx.Client, internet: FakeInternet) -> None:
    internet.break_host("www.fis-ski.com")
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender) == BUILT
    assert notification(sender)
    assert any(m.subject.startswith("Sports Hub: 3 problems") for m in sender.sent)


def test_missing_recipients_still_build_the_hub_and_say_so(tmp_path: Path, client: httpx.Client,
                                                           capsys: pytest.CaptureFixture[str]) -> None:
    env = {k: v for k, v in ENV.items() if k != "SPORTS_HUB_NOTIFY_TO"}
    sender = FakeSender()

    assert refresh_cli(tmp_path, client, sender, env=env) == BUILT_EMAIL_UNSENT
    assert "SPORTS_HUB_NOTIFY_TO" in capsys.readouterr().err
    assert (tmp_path / "hub" / "index.html").exists()


def test_no_addresses_or_secrets_in_the_notification_or_output(tmp_path: Path, client: httpx.Client,
                                                               capsys: pytest.CaptureFixture[str]) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)

    printed = capsys.readouterr()
    text = notification(sender).subject + notification(sender).text
    for secret in ("made-up app password", "hub.sender@example.com", "katie@example.com", "jason@example.com"):
        assert secret not in text
        assert secret not in printed.out + printed.err


def test_the_notification_matches_the_hub(tmp_path: Path, client: httpx.Client) -> None:
    sender = FakeSender()
    refresh_cli(tmp_path, client, sender)

    data = json.loads((tmp_path / "hub" / "data.json").read_text())
    text = notification(sender).text
    wec = next(s for s in data["sports"] if s["id"] == "wec")
    assert wec["events"][0]["name"] not in text  # Monza (Nov 8) is next week, not this one
    short_track = next(s for s in data["sports"] if s["id"] == "short-track")
    montreal = next(e for e in short_track["events"] if e["date"] == "2026-10-30")
    assert montreal["name"] in text
