"""Hub outputs a Refresh produces beyond data.json: calendar feeds (22) and the ESPN+ reminder data (23)."""

from datetime import date, datetime, timezone
from typing import Any

import httpx
from icalendar import Calendar

from conftest import FIXTURES, FakeInternet
from sports_hub.config import load_sports
from sports_hub.refresh import RefreshResult, refresh

TODAY = date(2026, 10, 24)


def run(client: httpx.Client, today: date = TODAY) -> RefreshResult:
    return refresh(today=today, client=client, previous=None, sports=load_sports())


def feed_events(result: RefreshResult, name: str) -> list[Any]:
    return list(Calendar.from_ical(result.feeds[name]).walk("VEVENT"))


def by_summary(events: list[Any], summary: str) -> Any:
    return next(e for e in events if str(e["SUMMARY"]) == summary)


# --- 22: calendar feeds ------------------------------------------------------------


def test_there_is_a_feed_per_sport_and_one_for_all(client: httpx.Client) -> None:
    result = run(client)

    assert set(result.feeds) == {f"{s.id}.ics" for s in load_sports()} | {"all.ics"}
    assert result.data["sports"][0]["feed"] == "feeds/f1.ics"


def test_timed_event_has_its_utc_start_and_watch_option(client: httpx.Client) -> None:
    qualifying = by_summary(feed_events(run(client), "f1.ics"), "Formula 1: Las Vegas Grand Prix (Qualifying)")

    assert qualifying.decoded("DTSTART") == datetime(2026, 11, 21, 4, 0, tzinfo=timezone.utc)
    assert qualifying.decoded("DTEND") == datetime(2026, 11, 21, 6, 0, tzinfo=timezone.utc)
    assert str(qualifying["LOCATION"]) == "Las Vegas, USA"
    assert "Watch: Apple TV" in str(qualifying["DESCRIPTION"])


def test_multi_day_event_is_an_all_day_entry_spanning_its_dates(client: httpx.Client) -> None:
    euros = by_summary(feed_events(run(client), "curling-intl.ics"), "Curling (Intl): European Curling Championships")

    # All-day ends are exclusive in iCal: Oct 27 to Nov 1 inclusive ends on Nov 2.
    assert euros.decoded("DTSTART") == date(2026, 10, 27)
    assert euros.decoded("DTEND") == date(2026, 11, 2)


def test_feeds_go_beyond_the_hub_window(client: httpx.Client) -> None:
    # The Hub shows 56 days; a calendar subscription should get the whole season.
    summaries = [str(e["SUMMARY"]) for e in feed_events(run(client), "wec.ics")]

    assert "FIA WEC: 24 Hours of Le Mans" in summaries


def test_event_ids_are_stable_between_refreshes(client: httpx.Client) -> None:
    first = by_summary(feed_events(run(client), "f1.ics"), "Formula 1: Abu Dhabi Grand Prix (Race)")
    later = by_summary(feed_events(run(client, date(2026, 11, 20)), "f1.ics"), "Formula 1: Abu Dhabi Grand Prix (Race)")

    assert str(first["UID"]) == str(later["UID"])


def test_the_all_sports_feed_holds_every_sport(client: httpx.Client) -> None:
    result = run(client)

    total = sum(len(feed_events(result, f"{s.id}.ics")) for s in load_sports())
    assert len(feed_events(result, "all.ics")) == total


# --- 23: ESPN+ reminder data ----------------------------------------------------------


def test_upcoming_slams_are_listed_with_when_to_remind(client: httpx.Client) -> None:
    reminders = run(client).data["reminders"]

    masters = reminders[0]
    assert masters == {
        "id": "GSOC Masters|2026-11-03",
        "kind": "espn-plus",
        "name": "GSOC Masters",
        "date": "2026-11-03",
        "end_date": "2026-11-08",
        "show_from": "2026-10-27",
    }
    assert [r["name"] for r in reminders] == ["GSOC Masters", "GSOC National", "GSOC Open", "GSOC Players' Cup"]


def test_finished_slams_are_not_reminded(client: httpx.Client) -> None:
    names = [r["name"] for r in run(client, date(2026, 11, 25)).data["reminders"]]

    assert names == ["GSOC Open", "GSOC Players' Cup"]


def test_feed_names_the_best_ranked_watch_option(client: httpx.Client) -> None:
    # Snowboard lists Outside TV (free) before Peacock (which we have); "have" ranks first.
    events = feed_events(run(client), "snowboard.ics")

    assert all("Watch: Peacock" in str(e["DESCRIPTION"]) for e in events)


def test_every_feed_entry_has_a_timestamp(client: httpx.Client) -> None:
    events = feed_events(run(client), "f1.ics")

    assert all("DTSTAMP" in e for e in events)


def test_a_session_moved_to_a_new_time_keeps_its_calendar_id(client: httpx.Client, internet: FakeInternet) -> None:
    before = by_summary(feed_events(run(client), "f1.ics"), "Formula 1: Las Vegas Grand Prix (Qualifying)")
    moved = (FIXTURES / "jolpica_f1_2026.json").read_text(encoding="utf-8").replace(
        '"Qualifying":{"date":"2026-11-21","time":"04:00:00Z"}', '"Qualifying":{"date":"2026-11-21","time":"05:30:00Z"}'
    )
    assert moved != (FIXTURES / "jolpica_f1_2026.json").read_text(encoding="utf-8"), "fixture text changed shape"
    internet.serve("api.jolpi.ca", "/ergast/f1/2026.json", moved.encode())

    after = by_summary(feed_events(run(client), "f1.ics"), "Formula 1: Las Vegas Grand Prix (Qualifying)")

    assert after.decoded("DTSTART") == datetime(2026, 11, 21, 5, 30, tzinfo=timezone.utc)
    assert str(after["UID"]) == str(before["UID"])


def test_hub_data_lists_watch_options_already_ranked(client: httpx.Client) -> None:
    sports = {s["id"]: s for s in run(client).data["sports"]}

    assert [w["label"] for w in sports["snowboard"]["watch"]] == ["Peacock", "Outside TV"]  # VPN dropped: legal options exist
    assert [w["type"] for w in sports["wec"]["watch"]] == ["consider"]


def test_hub_data_shares_the_feed_ids_and_event_length(client: httpx.Client) -> None:
    result = run(client)
    f1 = next(s for s in result.data["sports"] if s["id"] == "f1")
    vegas = next(e for e in f1["events"] if e["name"] == "Las Vegas Grand Prix" and e["session"] == "Qualifying")

    feed_uid = str(by_summary(feed_events(result, "f1.ics"), "Formula 1: Las Vegas Grand Prix (Qualifying)")["UID"])
    assert vegas["uid"] == feed_uid
    assert result.data["event_length_hours"] == 2


def test_reminders_have_an_id_per_slam_and_date(client: httpx.Client) -> None:
    masters = run(client).data["reminders"][0]

    assert masters["id"] == "GSOC Masters|2026-11-03"
