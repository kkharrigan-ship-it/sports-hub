"""MotoGP Grand Prix weekends from Pulselive, the API behind motogp.com.

Where a weekend's session times are published, the Hub gets Qualifying (Q2),
the Sprint and the Race as separate Events. Otherwise (e.g. next season before
timetables are out) the weekend is one all-day Event.
"""

from datetime import date, datetime, timezone
from typing import Any

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.model import Event, Sport

EVENTS_URL = "https://api.motogp.pulselive.com/motogp/v1/events"

# (Pulselive shortname, name shown on the Hub) for MotoGP-class sessions.
SESSIONS = {"Q2": "Qualifying", "SPR": "Sprint", "RAC": "Race"}


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    events: list[Event] = []
    for year in (today.year, today.year + 1):
        response = get(client, EVENTS_URL, {"seasonYear": str(year)})
        try:
            weekends = response.json()
            if not isinstance(weekends, list):
                raise SourceError("MotoGP events response is not a list")
            for weekend in weekends:
                if weekend["kind"] == "GP":
                    events.extend(_weekend(sport.id, weekend))
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceError(f"MotoGP event entry has an unexpected shape ({exc})") from exc
    return events


def grand_prix_name(additional_name: str) -> str:
    """'GREAT BRITAIN' -> 'Grand Prix of Great Britain'; short codes like 'USA' stay upper-case."""
    words = additional_name.split()
    return "Grand Prix of " + " ".join(w if len(w) <= 3 else w.title() for w in words)


def _weekend(sport_id: str, weekend: dict[str, Any]) -> list[Event]:
    name = grand_prix_name(weekend["additional_name"])
    circuit = weekend["circuit"]
    location = f"{circuit['name']}, {circuit['country']}"
    sessions = [
        b for b in weekend.get("broadcasts", [])
        if b.get("type") == "SESSION" and b["category"]["acronym"] == "MGP" and b["shortname"].strip() in SESSIONS
    ]
    if not sessions:
        return [
            Event(
                sport_id=sport_id,
                name=name,
                day=datetime.fromisoformat(weekend["date_start"]).date(),
                end_day=datetime.fromisoformat(weekend["date_end"]).date(),
                location=location,
            )
        ]
    events = []
    for b in sessions:
        start = datetime.fromisoformat(b["date_start"]).astimezone(timezone.utc)
        label = SESSIONS[b["shortname"].strip()]
        events.append(Event(sport_id=sport_id, name=name, session=label, day=start.date(), start=start, location=location))
    return events
