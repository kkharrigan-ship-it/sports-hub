"""Refresh behaviour for the FIS snow Sports (ticket 02) and biathlon (ticket 03)."""

import json
from datetime import date
from typing import Any

import httpx

from conftest import FIXTURES, FakeInternet, sport_entry
from sports_hub.config import load_sports
from sports_hub.refresh import refresh

TODAY = date(2026, 10, 24)
FIS_FEED = ("www.fis-ski.com", "/DB/services/public/icalendar-feed-fis-events.html")


def events_of(client: httpx.Client, sport_id: str, today: date = TODAY) -> list[dict[str, Any]]:
    result = refresh(today=today, client=client, previous=None, sports=load_sports())
    events: list[dict[str, Any]] = sport_entry(result, sport_id)["events"]
    return events


def test_training_runs_are_left_out(client: httpx.Client, internet: FakeInternet) -> None:
    # The saved feed has no training runs yet (they're added nearer race week),
    # so relabel the Soelden men's race as one.
    feed = (FIXTURES / "fis_AL.ics").read_text(encoding="utf-8")
    feed = feed.replace("Gender: Men\\Event: Giant Slalom", "Gender: Men\\Event: Downhill Training", 1)
    internet.serve(*FIS_FEED, feed.encode())

    sessions = [e["session"] for e in events_of(client, "alpine") if e["name"] == "Soelden World Cup"]

    assert sessions == ["Women's Giant Slalom"]


def test_alpine_races_have_name_location_and_utc_start(client: httpx.Client) -> None:
    events = events_of(client, "alpine")

    soelden_men = next(e for e in events if e["date"] == "2026-10-25")
    assert soelden_men["name"] == "Soelden World Cup"
    assert soelden_men["session"] == "Men's Giant Slalom"
    assert soelden_men["location"] == "Soelden, AUT"
    assert soelden_men["start"] == "2026-10-25T09:00:00Z"


def test_start_times_are_right_either_side_of_the_dst_change(client: httpx.Client) -> None:
    # Europe left summer time on 2026-10-25. Both Soelden races start at 10:00-ish
    # local time, so their UTC times differ by the hour that changed:
    # Sat 10:30 CEST = 08:30Z, Sun 10:00 CET = 09:00Z.
    events = events_of(client, "alpine")

    starts = {e["session"]: e["start"] for e in events if e["name"] == "Soelden World Cup"}
    assert starts == {
        "Women's Giant Slalom": "2026-10-24T08:30:00Z",
        "Men's Giant Slalom": "2026-10-25T09:00:00Z",
    }


def test_snowboard_events_without_a_time_are_all_day(client: httpx.Client) -> None:
    events = events_of(client, "snowboard")

    pgs = next(e for e in events if e["name"] == "Snow Ruyi World Cup" and e["session"] == "Women's Parallel Giant Slalom")
    assert pgs["date"] == "2026-11-28"
    assert pgs["all_day"] is True
    assert pgs["start"] is None
    assert pgs["location"] == "Snow Ruyi, CHN"


def test_qualification_rounds_are_left_out(client: httpx.Client) -> None:
    for sport_id in ("snowboard", "freestyle"):
        sessions = [e["session"] for e in events_of(client, sport_id)]
        assert sessions, sport_id
        assert not any("Qualification" in s for s in sessions), sport_id


def test_freestyle_appears_with_world_cup_events(client: httpx.Client) -> None:
    events = events_of(client, "freestyle")

    assert len(events) >= 6
    assert all(e["name"].endswith("World Cup") for e in events)


def test_biathlon_races_come_from_ibu(client: httpx.Client) -> None:
    events = events_of(client, "biathlon")

    # Known-good values from the IBU Kontiolahti competitions.
    individual = next(e for e in events if e["session"] == "Men's 20km Individual")
    assert individual["name"] == "Kontiolahti World Cup"
    assert individual["location"] == "Kontiolahti, FIN"
    assert individual["start"] == "2026-11-26T15:15:00Z"


def test_biathlon_stays_at_a_handful_of_requests(client: httpx.Client, internet: FakeInternet) -> None:
    # Polite fetching (spec): the season has 11 meetings, but the window to
    # 2026-12-19 only touches three, so a Refresh shouldn't ask about the rest.
    events_of(client, "biathlon")

    biathlon_requests = [r for r in internet.requests if r.url.host == "www.biathlonresults.com"]
    assert len(biathlon_requests) <= 4


def test_biathlon_keeps_looking_when_the_current_meeting_is_nearly_over(
    client: httpx.Client, internet: FakeInternet
) -> None:
    # Dec 6: only Hochfilzen's two relays remain. The next meeting starts beyond
    # the 56-day window, but the Hub still needs six upcoming races, so it must
    # be looked up too. Races already run must not count towards the six.
    meetings = [
        {"EventId": "BT2627SWRLCP02", "StartDate": "2026-11-30T12:00:00Z", "EndDate": "2026-12-06T12:00:00Z",
         "ShortDescription": "Hochfilzen", "Organizer": "Hochfilzen", "Nat": "AUT", "EventClassificationId": "BTSWRLCP"},
        {"EventId": "BT2627SWRLCP07", "StartDate": "2027-03-01T12:00:00Z", "EndDate": "2027-03-07T12:00:00Z",
         "ShortDescription": "Later", "Organizer": "Later", "Nat": "CZE", "EventClassificationId": "BTSWRLCP"},
    ]
    internet.serve("www.biathlonresults.com", "/modules/sportapi/api/Events", json.dumps(meetings).encode())

    events = events_of(client, "biathlon", today=date(2026, 12, 6))

    assert len(events) >= 6
    assert [e["session"] for e in events[:2]] == ["Women's 4x6km Relay", "Men's 4x7.5km Relay"]
    assert {e["name"] for e in events} == {"Hochfilzen World Cup", "Later World Cup"}


def test_sparse_window_extends_to_the_next_six_events(client: httpx.Client) -> None:
    # On Sep 1 the 56-day window (to Oct 27) has no biathlon at all, so the Hub
    # shows the next six races instead: the whole Kontiolahti opener.
    events = events_of(client, "biathlon", today=date(2026, 9, 1))

    assert [e["session"] for e in events] == [
        "Men's 20km Individual",
        "Women's 15km Individual",
        "Single Mixed Relay (W+M)",
        "Mixed Relay (W+M)",
        "Men's 10km Sprint",
        "Women's 7.5km Sprint",
    ]
