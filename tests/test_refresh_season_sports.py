"""Season-file Sports with the real 2026-27 Season file (tickets 07-09, 13, 14)."""

from datetime import date
from typing import Any

import httpx

from conftest import FakeInternet, refreshed_entry, sport_entry, through_disk
from sports_hub.config import load_sports
from sports_hub.refresh import refresh

TODAY = date(2026, 10, 24)


def entry(client: httpx.Client, sport_id: str, today: date = TODAY) -> dict[str, Any]:
    return refreshed_entry(client, sport_id, today)


def test_wec_finale_is_monza_after_bahrain_was_cancelled(client: httpx.Client) -> None:
    events = entry(client, "wec")["events"]

    assert events[0]["name"] == "6 Hours of Monza"
    assert events[0]["date"] == "2026-11-08"


def test_sailgp_shows_the_gulf_double_header(client: httpx.Client) -> None:
    names = [e["name"] for e in entry(client, "sailgp")["events"]]

    assert names[:2] == ["Dubai Sail Grand Prix", "Abu Dhabi Sail Grand Prix"]


def test_curling_intl_shows_the_european_championships(client: httpx.Client) -> None:
    events = entry(client, "curling-intl")["events"]

    euros = next(e for e in events if e["name"] == "European Curling Championships")
    assert (euros["date"], euros["end_date"], euros["all_day"]) == ("2026-10-27", "2026-11-01", True)


def test_grand_slams_carry_the_slam_tag(client: httpx.Client) -> None:
    events = entry(client, "curling-ca")["events"]

    slams = [e["name"] for e in events if "slam" in e["tags"]]
    assert slams[:2] == ["GSOC Masters", "GSOC National"]
    assert events[0]["source"].startswith("https://www.thegrandslamofcurling.com/")
    assert "slam" not in next(e for e in events if e["name"] == "Canadian Mixed Curling Championship")["tags"]


def test_a_finished_multi_day_event_drops_off(client: httpx.Client) -> None:
    # The Victoria Invitational ended Oct 18; on Oct 24 it's gone.
    names = [e["name"] for e in entry(client, "curling-ca")["events"]]

    assert "GSOC Invitational" not in names


def test_a_running_multi_day_event_still_shows(client: httpx.Client) -> None:
    names = [e["name"] for e in entry(client, "curling-ca", today=date(2026, 10, 16))["events"]]

    assert names[0] == "GSOC Invitational"


# --- 13: Ireland rugby from two sources ------------------------------------------


def test_ireland_shows_november_tests_from_the_season_file(client: httpx.Client) -> None:
    events = entry(client, "ireland-rugby")["events"]

    argentina = events[0]
    assert argentina["name"] == "Ireland v Argentina"
    assert argentina["start"] == "2026-11-06T20:10:00Z"  # 20:10 in Dublin (GMT in November)
    assert argentina["location"] == "Aviva Stadium, Dublin"


def test_ireland_six_nations_kickoffs_come_from_the_fixtures_page(client: httpx.Client) -> None:
    events = entry(client, "ireland-rugby", today=date(2027, 1, 20))["events"]

    assert [(e["name"], e["start"]) for e in events] == [
        ("Ireland v England", "2027-02-05T20:10:00Z"),
        ("Italy v Ireland", "2027-02-13T14:10:00Z"),
        ("Wales v Ireland", "2027-02-20T14:10:00Z"),
        ("Scotland v Ireland", "2027-03-05T20:10:00Z"),
        ("Ireland v France", "2027-03-13T20:10:00Z"),
    ]
    assert events[0]["location"] == "Aviva Stadium"
    assert events[0]["session"] == "Six Nations"


def test_both_sources_appear_together_in_time_order(client: httpx.Client) -> None:
    # Nov 20: only the South Africa test is inside the window, so the next-6
    # rule fills up with the Six Nations from the other source.
    events = entry(client, "ireland-rugby", today=date(2026, 11, 20))["events"]

    assert [e["name"] for e in events] == [
        "Ireland v South Africa",
        "Ireland v England",
        "Italy v Ireland",
        "Wales v Ireland",
        "Scotland v Ireland",
        "Ireland v France",
    ]


def test_one_failed_source_still_shows_the_other_with_an_alert(
    client: httpx.Client, internet: FakeInternet
) -> None:
    internet.break_host("www.sixnationsrugby.com")

    result = refresh(today=date(2026, 11, 1), client=client, previous=None, sports=load_sports())

    ireland = sport_entry(result, "ireland-rugby")
    assert ireland["status"] == "in-season"
    assert ireland["events"][0]["name"] == "Ireland v Argentina"
    assert [a.sport_id for a in result.alerts] == ["ireland-rugby"]
    assert result.alerts[0].message.startswith("the Six Nations fixtures page: ")


def test_failed_source_falls_back_to_its_own_last_good_events(client: httpx.Client, internet: FakeInternet) -> None:
    good = refresh(today=date(2026, 11, 20), client=client, previous=None, sports=load_sports())
    internet.break_host("www.sixnationsrugby.com")

    result = refresh(today=date(2026, 11, 22), client=client, previous=through_disk(good.state), sports=load_sports())

    ireland = sport_entry(result, "ireland-rugby")
    assert ireland["stale_since"] == "2026-11-20"
    stale_by_name = {e["name"]: e["stale_since"] for e in ireland["events"]}
    assert stale_by_name["Ireland v England"] == "2026-11-20"  # from last-good state


def test_fresh_events_are_not_marked_stale_when_the_other_source_fails(
    client: httpx.Client, internet: FakeInternet
) -> None:
    good = refresh(today=date(2026, 11, 1), client=client, previous=None, sports=load_sports())
    internet.break_host("www.sixnationsrugby.com")

    result = refresh(today=date(2026, 11, 2), client=client, previous=through_disk(good.state), sports=load_sports())

    events = sport_entry(result, "ireland-rugby")["events"]
    november = [e for e in events if e["session"] == "Nations Championship"]
    assert november and all(e["stale_since"] is None for e in november)
    assert all(e["stale_since"] == "2026-11-01" for e in events if e["session"] == "Six Nations")


# --- 09: gymnastics, World Skate, Diamond League ----------------------------------


def test_gymnastics_worlds_in_rotterdam_still_show_on_their_last_weekend(client: httpx.Client) -> None:
    events = entry(client, "gymnastics")["events"]

    assert events[0]["name"] == "Artistic Gymnastics World Championships"
    assert events[0]["location"] == "Rotterdam, Netherlands"


def test_announced_but_distant_season_shows_its_next_six(client: httpx.Client) -> None:
    # Nothing in the Diamond League until May, but the 2027 calendar is out.
    dl = entry(client, "diamond-league")

    assert dl["status"] == "in-season"
    assert [e["name"] for e in dl["events"]][:2] == ["Diamond League Doha", "Diamond League Shanghai/Keqiao"]
    assert len(dl["events"]) == 6


def test_nothing_announced_is_off_season_with_its_label(client: httpx.Client) -> None:
    world_skate = entry(client, "world-skate", today=date(2026, 12, 1))

    assert world_skate["status"] == "off-season"
    assert world_skate["returns"] == "Returns 2027 (dates TBA)"
