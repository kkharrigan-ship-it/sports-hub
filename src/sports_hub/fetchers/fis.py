"""Alpine, Snowboard and Freestyle World Cup races from the official FIS iCal service.

One feed pattern covers all three Sports; the Sport's `sector` param picks one
(AL, SB or FS).
"""

import re
from datetime import date, datetime, timezone
from typing import Any

import httpx
from icalendar import Calendar

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.model import Event, Sport
from sports_hub.season import winter_start_year

FEED_URL = "https://www.fis-ski.com/DB/services/public/icalendar-feed-fis-events.html"

GENDER = re.compile(r"Gender: ([^\\\n]+)")
DISCIPLINE = re.compile(r"Event: ([^\\\n]+)")
COUNTRY = re.compile(r"\(([A-Z]{3})\)")
POSSESSIVE = {"Men": "Men's", "Women": "Women's"}
NOT_RACES = ("Qualification", "Training")


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    sector = sport.params["sector"]
    params = {"seasoncode": str(season_code(today)), "sectorcode": sector, "categorycode": "WC"}
    try:
        calendar = Calendar.from_ical(get(client, FEED_URL, params).content)
    except ValueError as exc:
        raise SourceError("FIS calendar feed could not be read as iCal") from exc

    races = (_race(sport.id, v) for v in calendar.walk("VEVENT") if _is_world_cup(v, sector))
    return [race for race in races if race is not None]


def season_code(today: date) -> int:
    """FIS names a season after the year it ends: winter 2026-27 is 2027."""
    return winter_start_year(today) + 1


def _is_world_cup(vevent: Any, sector: str) -> bool:
    categories = vevent.get("CATEGORIES")
    if categories is None:
        return False
    names = [str(c) for c in getattr(categories, "cats", [categories])]
    return f"FIS-calendar-{sector}-WC" in names


def _race(sport_id: str, vevent: Any) -> Event | None:
    try:
        summary = str(vevent["SUMMARY"])
        place = str(vevent["LOCATION"])
        description = str(vevent.get("DESCRIPTION", ""))
        start_value = vevent.decoded("DTSTART")
    except KeyError as exc:
        raise SourceError(f"FIS race entry is missing {exc}") from exc

    discipline_match = DISCIPLINE.search(description)
    if discipline_match is None:
        raise SourceError("FIS race entry has no 'Event:' line in its description")
    discipline = discipline_match.group(1).strip()
    if any(word in discipline for word in NOT_RACES):
        return None
    gender_match = GENDER.search(description)
    if gender_match:
        gender = gender_match.group(1).strip()
        discipline = f"{POSSESSIVE.get(gender, gender)} {discipline}"

    country = COUNTRY.search(summary)
    location = f"{place}, {country.group(1)}" if country else place

    start: datetime | None = None
    if isinstance(start_value, datetime):
        start = start_value.astimezone(timezone.utc)
        day = start.date()
    else:
        day = start_value
    return Event(sport_id=sport_id, name=f"{place} World Cup", session=discipline, day=day, start=start, location=location)
