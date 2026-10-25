"""Refresh behaviour for Formula 1 (ticket 01), tested through the Refresh entry point."""

from datetime import date
from typing import Any

import httpx

from conftest import sport_entry
from sports_hub.config import load_sports
from sports_hub.refresh import refresh

TODAY = date(2026, 10, 24)


def f1_events(client: httpx.Client, today: date = TODAY) -> list[dict[str, Any]]:
    result = refresh(today=today, client=client, previous=None, sports=load_sports())
    events: list[dict[str, Any]] = sport_entry(result, "f1")["events"]
    return events


def test_f1_sessions_appear_with_utc_times(client: httpx.Client) -> None:
    vegas_qualifying = next(
        e for e in f1_events(client) if e["name"] == "Las Vegas Grand Prix" and e["session"] == "Qualifying"
    )
    # Known-good values from the Jolpica 2026 calendar.
    assert vegas_qualifying["start"] == "2026-11-21T04:00:00Z"
    assert vegas_qualifying["all_day"] is False
    assert vegas_qualifying["location"] == "Las Vegas, USA"


def test_f1_includes_every_session_of_a_weekend(client: httpx.Client) -> None:
    vegas = [e["session"] for e in f1_events(client) if e["name"] == "Las Vegas Grand Prix"]
    assert vegas == ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]


def test_events_are_limited_to_the_next_56_days(client: httpx.Client) -> None:
    events = f1_events(client)

    dates = [e["date"] for e in events]
    assert min(dates) >= "2026-10-24"
    # 2026-10-24 + 56 days = 2026-12-19; the Abu Dhabi finale (Dec 6) is inside.
    assert max(dates) <= "2026-12-19"
    assert any(e["name"] == "Abu Dhabi Grand Prix" and e["session"] == "Race" for e in events)


def test_sprint_weekends_include_sprint_sessions(client: httpx.Client) -> None:
    singapore = [e["session"] for e in f1_events(client, date(2026, 9, 1)) if e["name"] == "Singapore Grand Prix"]
    assert singapore == ["Practice 1", "Sprint Qualifying", "Sprint", "Qualifying", "Race"]


def test_end_of_season_keeps_only_the_remaining_sessions(client: httpx.Client) -> None:
    # On Dec 5 only Abu Dhabi's Saturday and Sunday sessions remain. Fewer than six
    # exist, so the next-6 rule keeps what there is rather than inventing more.
    sessions = [e["session"] for e in f1_events(client, date(2026, 12, 5))]
    assert sessions == ["Practice 3", "Qualifying", "Race"]


def test_data_records_last_updated_from_today(client: httpx.Client) -> None:
    result = refresh(today=TODAY, client=client, previous=None, sports=load_sports())

    assert result.data["last_updated"] == "2026-10-24"


def test_off_season_f1_shows_its_returns_label_from_the_config(client: httpx.Client) -> None:
    result = refresh(today=date(2026, 12, 10), client=client, previous=None, sports=load_sports())

    f1 = sport_entry(result, "f1")
    assert f1["status"] == "off-season"
    assert f1["returns"], "the real config must give F1 a Returns label"
    assert f1["note"]
