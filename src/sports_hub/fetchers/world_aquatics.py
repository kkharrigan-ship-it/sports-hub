"""Swimming and Diving competitions from the World Aquatics API.

One API serves both Sports; the Sport's params pick the `discipline` (SW or DV)
and which competition `types` count as top level (e.g. World Cup, Worlds).
"""

from datetime import date, datetime, timedelta
from typing import Any

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.fetchers.parsing import place
from sports_hub.model import Event, Sport

API_URL = "https://api.worldaquatics.com/fina/competitions"
# Ask from a month back (so competitions still running are included) to well past the window.
LOOKBACK_DAYS = 31
LOOKAHEAD_DAYS = 400
# Stamps are local midnight written in UTC. Adding this many hours lands inside
# the local day for any venue from UTC-9 to UTC+14 (all World Aquatics hosts).
LOCAL_DAY_SHIFT_HOURS = 14


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    top_level = set(sport.params["types"].split(","))
    params = {
        "pageSize": "100",
        "venueDateFrom": f"{(today - timedelta(days=LOOKBACK_DAYS)).isoformat()}T00:00:00+00:00",
        "venueDateTo": f"{(today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()}T00:00:00+00:00",
        "disciplines": sport.params["discipline"],
        "group": "FINA",
        "sort": "dateFrom,asc",
    }
    try:
        competitions = get(client, API_URL, params).json()["content"]
        return [_event(sport.id, c) for c in competitions if c["competitionType"]["code"] in top_level]
    except (ValueError, KeyError, TypeError) as exc:
        raise SourceError(f"World Aquatics data has an unexpected shape ({exc})") from exc


def local_date(stamp: str) -> date:
    """The venue's local date from a local-midnight-in-UTC stamp.

    Beijing's Dec 1 is written "2026-11-30T17:00:00Z", Christchurch's (UTC+13)
    Dec 9 is "2026-12-08T11:00:00Z" and Montreal's Feb 25 is "2027-02-25T05:00:00Z".
    """
    return (datetime.fromisoformat(stamp) + timedelta(hours=LOCAL_DAY_SHIFT_HOURS)).date()


def _event(sport_id: str, c: dict[str, Any]) -> Event:
    venue = c.get("location") or {}
    return Event(
        sport_id=sport_id,
        name=c["name"],
        day=local_date(c["dateFrom"]),
        end_day=local_date(c["dateTo"]),
        location=place(venue.get("city"), venue.get("countryName")),
    )
