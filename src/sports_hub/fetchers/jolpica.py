"""Formula 1 sessions from Jolpica (the community successor to the Ergast API)."""

from datetime import date, datetime
from typing import Any

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.model import Event, Sport

SEASON_URL = "https://api.jolpi.ca/ergast/f1/{year}.json"

# Jolpica keys in weekend order, with the names shown on the Hub.
SESSIONS = [
    ("FirstPractice", "Practice 1"),
    ("SecondPractice", "Practice 2"),
    ("ThirdPractice", "Practice 3"),
    ("SprintQualifying", "Sprint Qualifying"),
    ("Sprint", "Sprint"),
    ("Qualifying", "Qualifying"),
]


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    # This season plus next, so the off-season gap is bridged once next year's
    # calendar is published (until then Jolpica returns an empty list).
    events: list[Event] = []
    for year in (today.year, today.year + 1):
        for race in _races(get(client, SEASON_URL.format(year=year), {"limit": "100"})):
            events.extend(_weekend(sport.id, race))
    return events


def _races(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        races = response.json()["MRData"]["RaceTable"]["Races"]
    except (ValueError, KeyError, TypeError) as exc:
        raise SourceError("Jolpica's response no longer has the expected race table") from exc
    if not isinstance(races, list):
        raise SourceError("Jolpica's race table is not a list")
    return races


def _weekend(sport_id: str, race: dict[str, Any]) -> list[Event]:
    try:
        grand_prix = race["raceName"]
        place = race["Circuit"]["Location"]
        location = f"{place['locality']}, {place['country']}"
        sessions = [(label, race[key]) for key, label in SESSIONS if key in race]
        sessions.append(("Race", {"date": race["date"], "time": race.get("time")}))
        return [_session(sport_id, grand_prix, label, when, location) for label, when in sessions]
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"Jolpica race entry has an unexpected shape ({exc})") from exc


def _session(sport_id: str, grand_prix: str, label: str, when: dict[str, Any], location: str) -> Event:
    time = when.get("time")
    return Event(
        sport_id=sport_id,
        name=grand_prix,
        session=label,
        day=date.fromisoformat(when["date"]),
        start=datetime.fromisoformat(f"{when['date']}T{time}") if time else None,
        location=location,
    )
