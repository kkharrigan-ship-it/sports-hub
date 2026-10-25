"""The Season file (ticket 07), tested through the Refresh entry point.

Each test writes a small Season file, loads the real Sports config with it,
and checks what the Refresh produces.
"""

from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from conftest import sport_entry
from sports_hub.config import load_sports
from sports_hub.errors import ConfigError
from sports_hub.refresh import refresh

TODAY = date(2026, 10, 24)


def refresh_with(tmp_path: Path, client: httpx.Client, season_yaml: str, today: date = TODAY) -> Any:
    season = tmp_path / "season.yaml"
    season.write_text(season_yaml, encoding="utf-8")
    return refresh(today=today, client=client, previous=None, sports=load_sports(season_path=season))


def test_timed_entry_becomes_a_utc_event_using_its_zone(tmp_path: Path, client: httpx.Client) -> None:
    # Europe leaves summer time on 2026-10-25: 15:00 in Lisbon is 14:00Z the
    # day before and 15:00Z the day after.
    result = refresh_with(tmp_path, client, """
sports:
  sailgp:
    events:
      - { name: Lisbon Sail Grand Prix, session: Day 1, date: 2026-10-24, time: "15:00", tz: Europe/Lisbon,
          location: "Lisbon, Portugal", source: "https://example.org/a" }
      - { name: Lisbon Sail Grand Prix, session: Day 2, date: 2026-10-26, time: "15:00", tz: Europe/Lisbon,
          location: "Lisbon, Portugal", source: "https://example.org/a" }
""")

    events = sport_entry(result, "sailgp")["events"]
    assert [(e["session"], e["start"]) for e in events] == [
        ("Day 1", "2026-10-24T14:00:00Z"),
        ("Day 2", "2026-10-26T15:00:00Z"),
    ]
    assert events[0]["location"] == "Lisbon, Portugal"


def test_entry_without_a_time_is_all_day_and_keeps_its_end_date(tmp_path: Path, client: httpx.Client) -> None:
    result = refresh_with(tmp_path, client, """
sports:
  wec:
    events:
      - { name: 8 Hours of Bahrain, date: 2026-11-07, end_date: 2026-11-08, location: "Sakhir, Bahrain",
          source: "https://example.org/b" }
""")

    (event,) = sport_entry(result, "wec")["events"]
    assert event["all_day"] is True
    assert event["start"] is None
    assert event["date"] == "2026-11-07"
    assert event["end_date"] == "2026-11-08"


def test_off_season_label_and_note_come_from_the_season_file(tmp_path: Path, client: httpx.Client) -> None:
    result = refresh_with(tmp_path, client, """
sports:
  wec:
    returns: Returns Feb 2027
    offseason_note: The 2027 season opens in Qatar.
    events: []
  f1:
    returns: Returns Mar 2027
    offseason_note: The 2027 calendar hasn't been published yet.
""", today=date(2026, 12, 10))

    wec = sport_entry(result, "wec")
    assert (wec["status"], wec["returns"], wec["note"]) == ("off-season", "Returns Feb 2027", "The 2027 season opens in Qatar.")
    assert sport_entry(result, "f1")["returns"] == "Returns Mar 2027"


def test_entry_tags_appear_in_the_data(tmp_path: Path, client: httpx.Client) -> None:
    result = refresh_with(tmp_path, client, """
sports:
  wec:
    events:
      - { name: Test, date: 2026-11-07, location: X, source: "https://example.org/c", tags: [finale] }
""")

    assert sport_entry(result, "wec")["events"][0]["tags"] == ["finale"]


@pytest.mark.parametrize(
    ("entry", "complaint"),
    [
        ("{ name: X, location: Y, source: s }", "missing 'date'"),
        ("{ name: X, date: 2026-11-07, location: Y }", "missing 'source'"),
        ("{ name: X, date: 2026-11-07, time: '14:00', location: Y, source: s }", "needs a 'tz'"),
        ("{ name: X, date: 2026-11-07, time: '14:00', tz: Mars/Olympus, location: Y, source: s }", "unknown time zone"),
        ("{ name: X, date: 2026-11-07, time: '2pm', tz: UTC, location: Y, source: s }", "time '2pm'"),
    ],
)
def test_malformed_entry_stops_with_a_message_naming_it(tmp_path: Path, entry: str, complaint: str) -> None:
    season = tmp_path / "season.yaml"
    season.write_text(f"sports:\n  wec:\n    events:\n      - {entry}\n", encoding="utf-8")

    with pytest.raises(ConfigError, match=f"wec entry 1.*{complaint}"):
        load_sports(season_path=season)


def test_unknown_sport_in_the_season_file_is_an_error(tmp_path: Path) -> None:
    season = tmp_path / "season.yaml"
    season.write_text("sports:\n  cricket:\n    events: []\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="cricket"):
        load_sports(season_path=season)


def test_sport_section_that_is_not_a_mapping_is_an_error(tmp_path: Path) -> None:
    season = tmp_path / "season.yaml"
    season.write_text("sports:\n  wec: just some text\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="wec: expected fields"):
        load_sports(season_path=season)


def test_tags_written_as_text_instead_of_a_list_is_an_error(tmp_path: Path) -> None:
    season = tmp_path / "season.yaml"
    season.write_text(
        "sports:\n  wec:\n    events:\n      - { name: X, date: 2026-11-07, source: s, tags: finale }\n", encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="wec entry 1.*'tags' must be a list"):
        load_sports(season_path=season)
