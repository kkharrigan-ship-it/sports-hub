"""Data-feed Sports added in Milestone 2: PWHL (10), swimming and diving (11), MotoGP (12)."""

import json
from datetime import date
from typing import Any

import httpx

from conftest import FIXTURES, FakeInternet, refreshed_entry, sport_entry
from sports_hub.config import load_sports
from sports_hub.refresh import refresh

TODAY = date(2026, 10, 24)


def entry(client: httpx.Client, sport_id: str, today: date = TODAY) -> dict[str, Any]:
    return refreshed_entry(client, sport_id, today)


# --- 10: PWHL ------------------------------------------------------------------


def test_pwhl_shows_its_opening_games_before_the_season_starts(client: httpx.Client) -> None:
    # The 2026-27 season opens Dec 5, inside the 56-day window (Oct 24 + 56 = Dec 19).
    events = entry(client, "pwhl")["events"]

    opener = events[0]
    assert opener["name"] == "Seattle Torrent at Vancouver Goldeneyes"
    assert opener["start"] == "2026-12-05T20:00:00Z"  # 3:00 pm EST
    assert opener["location"] == "Pacific Coliseum, Vancouver, BC"


def test_pwhl_uses_the_current_regular_season_not_preseason(client: httpx.Client) -> None:
    # The seasons feed lists the 2026-27 preseason (Oct-Nov) next to the regular
    # season. Only the regular season's schedule is saved, so picking the
    # preseason would leave PWHL unavailable with an Alert.
    result = refresh(today=TODAY, client=client, previous=None, sports=load_sports())

    pwhl = sport_entry(result, "pwhl")
    assert pwhl["status"] == "in-season"
    assert "pwhl" not in [a.sport_id for a in result.alerts]


def test_pwhl_feed_wrapped_in_parentheses_still_parses(client: httpx.Client, internet: FakeInternet) -> None:
    wrapped = b"(" + (FIXTURES / "pwhl_modulekit_schedule_11.json").read_bytes() + b")"
    internet.serve_query("lscluster.hockeytech.com", "view=schedule", wrapped)

    assert entry(client, "pwhl")["events"][0]["name"] == "Seattle Torrent at Vancouver Goldeneyes"


def test_pwhl_changed_shape_is_an_alert(client: httpx.Client, internet: FakeInternet) -> None:
    internet.serve_query("lscluster.hockeytech.com", "view=schedule", b'{"SiteKit": {}}')

    result = refresh(today=TODAY, client=client, previous=None, sports=load_sports())

    assert sport_entry(result, "pwhl")["status"] == "unavailable"
    assert [a.sport_id for a in result.alerts] == ["pwhl"]


# --- 11: swimming and diving ---------------------------------------------------


def test_swimming_shows_top_level_competitions_on_their_local_dates(client: httpx.Client) -> None:
    events = entry(client, "swimming")["events"]

    # World Cup stops are over by Oct 24; next up are the short-course Worlds.
    # (The Youth Olympic Games are not top level and are left out.)
    first = events[0]
    assert first["name"] == "World Aquatics Swimming Championships (25m) 2026"
    assert (first["date"], first["end_date"]) == ("2026-12-01", "2026-12-06")  # Beijing local
    assert first["location"] == "Beijing, People's Republic of China"
    assert first["all_day"] is True
    assert not any("Youth" in e["name"] or "Masters" in e["name"] for e in events)


def test_diving_shows_world_cups_but_not_grand_prix_meets(client: httpx.Client) -> None:
    # Grand Prix meets are a lower tier than the World Cup, so they're left out.
    names = [e["name"] for e in entry(client, "diving")["events"]]

    assert names[0] == "World Aquatics Diving World Cup 2027"
    assert "World Aquatics Diving World Cup 2027 - Super Final" in names
    assert not any("Open Diving" in n or "Diving Cup" in n or "Madrid" in n for n in names)


def test_world_championships_are_in_but_masters_are_out(client: httpx.Client) -> None:
    # Both run in Budapest from June 26, 2027.
    names = [e["name"] for e in entry(client, "diving", today=date(2027, 6, 1))["events"]]

    assert "World Aquatics Championships - Budapest 2027" in names
    assert not any("Masters" in n for n in names)


def test_local_dates_are_right_far_east_of_utc(client: httpx.Client, internet: FakeInternet) -> None:
    # Auckland is UTC+13 in January: local midnight on Jan 15 is 11:00Z on Jan 14.
    auckland = {"content": [{
        "name": "Swimming World Cup Auckland", "dateFrom": "2027-01-14T11:00:00Z", "dateTo": "2027-01-16T11:00:00Z",
        "location": {"city": "Auckland", "countryName": "New Zealand"}, "competitionType": {"code": "SWC"},
    }]}
    internet.serve_query("api.worldaquatics.com", "disciplines=SW", json.dumps(auckland).encode())

    (event,) = entry(client, "swimming", today=date(2027, 1, 1))["events"]

    assert (event["date"], event["end_date"]) == ("2027-01-15", "2027-01-17")


def test_competition_without_a_city_shows_its_country(client: httpx.Client) -> None:
    events = entry(client, "diving", today=date(2027, 3, 1))["events"]

    mexico = next(e for e in events if e["date"] == "2027-03-04")
    assert mexico["location"] == "Mexico"


# --- 12: MotoGP ----------------------------------------------------------------


def test_motogp_weekend_shows_qualifying_sprint_and_race(client: httpx.Client) -> None:
    events = entry(client, "motogp")["events"]

    malaysia = [(e["session"], e["start"]) for e in events if e["name"] == "Grand Prix of Malaysia"]
    # Known-good times from Pulselive, local +08:00 converted to UTC.
    assert malaysia == [
        ("Qualifying", "2026-10-31T03:15:00Z"),
        ("Sprint", "2026-10-31T07:00:00Z"),
        ("Race", "2026-11-01T07:00:00Z"),
    ]
    assert next(e for e in events if e["name"] == "Grand Prix of Malaysia")["location"] == (
        "Petronas Sepang International Circuit, Malaysia"
    )


def test_motogp_leaves_out_tests_and_smaller_classes(client: httpx.Client) -> None:
    events = entry(client, "motogp", today=date(2026, 11, 25))["events"]

    names = {e["name"] for e in events}
    assert not any("Test" in n for n in names)
    assert [e["session"] for e in events if e["name"] == "Grand Prix of Valencia"] == ["Qualifying", "Sprint", "Race"]


def test_motogp_is_off_season_when_next_year_is_not_published(client: httpx.Client, internet: FakeInternet) -> None:
    internet.serve_query("api.motogp.pulselive.com", "seasonYear=2027", b"[]")

    motogp = entry(client, "motogp", today=date(2026, 12, 10))

    assert motogp["status"] == "off-season"
    assert motogp["returns"] == "Returns Mar 2027"


def test_next_season_weekends_without_sessions_are_all_day(client: httpx.Client) -> None:
    # After Valencia, 2027 is published as weekends only (no session times yet).
    events = entry(client, "motogp", today=date(2026, 12, 10))["events"]

    thailand = events[0]
    assert thailand["name"] == "Grand Prix of Thailand"
    assert thailand["all_day"] is True
    assert thailand["session"] is None
    assert thailand["end_date"] is not None


# --- 14: ISU speed skating and short track ---------------------------------------


def test_short_track_shows_the_vancouver_stop_still_running(client: httpx.Client) -> None:
    events = entry(client, "short-track")["events"]

    vancouver = events[0]
    assert vancouver["name"] == "ISU Short Track World Tour #1"
    # Local dates in Vancouver, recovered from the UTC range and venue zone.
    assert (vancouver["date"], vancouver["end_date"]) == ("2026-10-23", "2026-10-25")
    assert vancouver["location"] == "Vancouver, Canada"


def test_junior_events_are_left_out(client: httpx.Client) -> None:
    for sport_id in ("short-track", "speed-skating"):
        names = [e["name"] for e in entry(client, sport_id)["events"]]
        assert names, sport_id
        assert not any("Junior" in n for n in names), sport_id


def test_speed_skating_world_cup_opens_in_beijing(client: httpx.Client) -> None:
    opener = entry(client, "speed-skating")["events"][0]

    assert opener["name"] == "ISU CNSG Speed Skating World Cup #1"
    assert (opener["date"], opener["end_date"]) == ("2026-11-13", "2026-11-15")
    assert opener["location"] == "Beijing, China"


def test_isu_event_with_an_unknown_time_zone_is_an_alert_not_a_guess(
    client: httpx.Client, internet: FakeInternet
) -> None:
    page = (FIXTURES / "isu_short-track_events.html").read_text(encoding="utf-8")
    internet.serve("isu-skating.com", "/en/short-track/events/", page.replace("America/Los_Angeles", "Pacific/Nowhere").encode())

    result = refresh(today=TODAY, client=client, previous=None, sports=load_sports())

    assert sport_entry(result, "short-track")["status"] == "unavailable"
    assert any("unknown time zone" in a.message for a in result.alerts if a.sport_id == "short-track")


def test_isu_page_without_event_data_is_an_alert(client: httpx.Client, internet: FakeInternet) -> None:
    internet.serve("isu-skating.com", "/en/short-track/events/", b"<html>redesigned</html>")

    result = refresh(today=TODAY, client=client, previous=None, sports=load_sports())

    assert sport_entry(result, "short-track")["status"] == "unavailable"
    assert "short-track" in [a.sport_id for a in result.alerts]
