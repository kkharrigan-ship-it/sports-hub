"""Off-season Sports (04), stale fallback and alerts (05), date guard and drop warning (06).

All tested through the Refresh entry point. The previous state goes through its
JSON file format between runs, as it does in the real CLI.
"""

from datetime import date

import httpx
import pytest

from conftest import FIXTURES, FakeInternet, sport_entry, through_disk
from sports_hub.model import Sport, WatchOption
from sports_hub.refresh import DateWentBackwards, RefreshResult, refresh

F1 = Sport(
    id="f1",
    name="Formula 1",
    category="motor",
    sources=("jolpica",),
    watch=(WatchOption("Apple TV", "have"),),
    returns="Returns March 2027",
    offseason_note="The 2027 calendar hasn't been published yet.",
)
ALPINE = Sport(id="alpine", name="Alpine Skiing", category="snow", sources=("fis",), params={"sector": "AL"})
BIATHLON = Sport(id="biathlon", name="Biathlon", category="snow", sources=("ibu",))
SPORTS = [F1, ALPINE, BIATHLON]


def run(client: httpx.Client, today: date, previous: RefreshResult | None = None) -> RefreshResult:
    state = through_disk(previous.state) if previous else None
    return refresh(today=today, client=client, previous=state, sports=SPORTS)


# --- 04: off-season Sports ---------------------------------------------------


def test_sport_with_nothing_upcoming_is_off_season_with_its_label(client: httpx.Client) -> None:
    # After the Dec 6 finale, Jolpica's 2027 calendar is still empty.
    f1 = sport_entry(run(client, date(2026, 12, 10)), "f1")

    assert f1["status"] == "off-season"
    assert f1["events"] == []
    assert f1["returns"] == "Returns March 2027"
    assert f1["note"] == "The 2027 calendar hasn't been published yet."


def test_off_season_without_a_label_still_works(client: httpx.Client) -> None:
    bare = Sport(id="f1", name="Formula 1", category="motor", sources=("jolpica",))
    result = refresh(today=date(2026, 12, 10), client=client, previous=None, sports=[bare])

    f1 = sport_entry(result, "f1")
    assert f1["status"] == "off-season"
    assert f1["returns"] is None
    assert result.alerts == []


def test_sport_with_events_is_in_season(client: httpx.Client) -> None:
    assert sport_entry(run(client, date(2026, 10, 24)), "f1")["status"] == "in-season"


# --- 05: stale fallback and alerts -------------------------------------------


def test_broken_source_keeps_last_good_events_and_alerts(client: httpx.Client, internet: FakeInternet) -> None:
    good = run(client, date(2026, 10, 20))
    internet.break_host("www.fis-ski.com")

    result = run(client, date(2026, 10, 24), previous=good)

    alpine = sport_entry(result, "alpine")
    assert alpine["status"] == "in-season"
    assert alpine["stale_since"] == "2026-10-20"
    assert alpine["events"], "last-good Events should still be shown"
    assert all(e["date"] >= "2026-10-24" for e in alpine["events"]), "trimmed to the current window"
    assert [(a.level, a.sport_id) for a in result.alerts] == [("error", "alpine")]
    assert "couldn't reach www.fis-ski.com" in result.alerts[0].message


def test_other_sports_still_update_when_one_breaks(client: httpx.Client, internet: FakeInternet) -> None:
    internet.break_host("www.fis-ski.com")

    result = run(client, date(2026, 10, 24))

    assert sport_entry(result, "f1")["events"]
    assert sport_entry(result, "f1")["stale_since"] is None
    assert sport_entry(result, "biathlon")["events"]


def test_broken_source_with_no_history_is_unavailable(client: httpx.Client, internet: FakeInternet) -> None:
    internet.break_host("www.biathlonresults.com", httpx.Response(500))

    result = run(client, date(2026, 10, 24))

    biathlon = sport_entry(result, "biathlon")
    assert biathlon["status"] == "unavailable"
    assert biathlon["events"] == []
    assert result.alerts[0].message == "www.biathlonresults.com answered HTTP 500"


def test_changed_response_shape_is_an_alert_not_wrong_events(client: httpx.Client, internet: FakeInternet) -> None:
    internet.serve("api.jolpi.ca", "/ergast/f1/2026.json", b'{"MRData": {"Races": []}}')

    result = run(client, date(2026, 10, 24))

    assert sport_entry(result, "f1")["status"] == "unavailable"
    assert [a.sport_id for a in result.alerts] == ["f1"]
    assert "expected race table" in result.alerts[0].message


def test_stale_since_stays_at_the_last_successful_fetch(client: httpx.Client, internet: FakeInternet) -> None:
    good = run(client, date(2026, 10, 20))
    internet.break_host("www.fis-ski.com")

    first_failure = run(client, date(2026, 10, 22), previous=good)
    second_failure = run(client, date(2026, 10, 24), previous=first_failure)

    assert sport_entry(second_failure, "alpine")["stale_since"] == "2026-10-20"


# --- 06: date guard and drop warning ------------------------------------------


def test_refresh_refuses_a_date_earlier_than_the_last_refresh(client: httpx.Client) -> None:
    good = run(client, date(2026, 10, 24))

    with pytest.raises(DateWentBackwards, match="2026-10-10.*2026-10-24"):
        run(client, date(2026, 10, 10), previous=good)


def test_refresh_allows_the_same_date_again(client: httpx.Client) -> None:
    good = run(client, date(2026, 10, 24))

    again = run(client, date(2026, 10, 24), previous=good)

    assert again.data["last_updated"] == "2026-10-24"


def test_collapsed_event_count_raises_a_warning(client: httpx.Client, internet: FakeInternet) -> None:
    good = run(client, date(2026, 10, 20))
    internet.serve("www.fis-ski.com", "/DB/services/public/icalendar-feed-fis-events.html", _alpine_feed_with_one_race())

    result = run(client, date(2026, 10, 24), previous=good)

    assert [(a.level, a.sport_id) for a in result.alerts] == [("warning", "alpine")]
    assert "dropped" in result.alerts[0].message


def test_natural_season_end_is_not_a_drop(client: httpx.Client) -> None:
    # Dec 1: F1 has Abu Dhabi left. Dec 10: it's over and 2027 isn't published.
    before_finale = run(client, date(2026, 12, 1))

    after = run(client, date(2026, 12, 10), previous=before_finale)

    assert [a for a in after.alerts if a.sport_id == "f1"] == []


def _alpine_feed_with_one_race() -> bytes:
    text = (FIXTURES / "fis_AL.ics").read_text(encoding="utf-8")
    head, *events = text.split("BEGIN:VEVENT")
    tail = "END:VCALENDAR"
    return (head + "BEGIN:VEVENT" + events[0].split("END:VEVENT")[0] + "END:VEVENT\r\n" + tail).encode()
