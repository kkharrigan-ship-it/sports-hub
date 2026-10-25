"""Biathlon World Cup races from the IBU results API (biathlonresults.com).

Two steps: the season's meetings first, then the races inside each meeting.
Only meetings the Hub's window needs are looked up, so a run stays at a few
requests.
"""

from datetime import date, datetime
from typing import Any

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.model import Event, Sport
from sports_hub.season import winter_start_year
from sports_hub.window import MIN_EVENTS, horizon

API = "https://www.biathlonresults.com/modules/sportapi/api"


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    meetings = _json_list(get(client, f"{API}/Events", {"SeasonId": season_id(today), "Level": "1"}), "meetings")
    try:
        races: list[Event] = []
        for meeting in sorted(meetings, key=lambda m: m["StartDate"]):
            if _day(meeting["EndDate"]) < today:
                continue
            upcoming = sum(1 for r in races if r.day >= today)
            if _day(meeting["StartDate"]) > horizon(today) and upcoming >= MIN_EVENTS:
                break
            entries = _json_list(get(client, f"{API}/Competitions", {"EventId": meeting["EventId"]}), "races")
            races.extend(_race(sport.id, meeting, entry) for entry in entries if entry.get("StartTime"))
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"IBU data has an unexpected shape ({exc})") from exc
    return races


def season_id(today: date) -> str:
    """IBU season ids are two two-digit years: winter 2026-27 is '2627'."""
    first = winter_start_year(today)
    return f"{first % 100:02d}{(first + 1) % 100:02d}"


def _json_list(response: httpx.Response, what: str) -> list[dict[str, Any]]:
    try:
        data = response.json()
    except ValueError as exc:
        raise SourceError(f"IBU {what} response is not JSON") from exc
    if not isinstance(data, list):
        raise SourceError(f"IBU {what} response is not a list")
    return data


def _race(sport_id: str, meeting: dict[str, Any], entry: dict[str, Any]) -> Event:
    start = datetime.fromisoformat(entry["StartTime"])
    kind = "World Championships" if meeting["EventClassificationId"].endswith("CH") else "World Cup"
    return Event(
        sport_id=sport_id,
        name=f"{meeting['ShortDescription']} {kind}",
        session=entry["ShortDescription"],
        day=start.date(),
        start=start,
        location=f"{meeting['Organizer']}, {meeting['Nat']}",
    )


def _day(value: str) -> date:
    return datetime.fromisoformat(value).date()
