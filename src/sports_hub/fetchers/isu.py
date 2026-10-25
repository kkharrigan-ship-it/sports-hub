"""Speed Skating and Short Track events from the ISU website (isu-skating.com).

There's no public API, but each discipline's events page embeds its event list
as page data. Each event is read for its name, UTC date range, venue time zone
and place; junior events are left out. See docs/adr/0001-isu-events-from-page-data.md.
"""

import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.fetchers.parsing import page_data, place, zone
from sports_hub.model import Event, Sport

EVENTS_URL = "https://isu-skating.com/en/{discipline}/events/"

EVENT = re.compile(
    r'"from_date_utc":"(?P<start>[^"]+)","to_date_utc":"(?P<end>[^"]+)","time_zone":"(?P<tz>[^"]*)",'
    r'"city":"(?P<city>[^"]*)","country_code":"[^"]*","country_name":"(?P<country>[^"]*)",'
    r'"season":"[^"]*","event_type_name":"[^"]*","event_sub_type_name":"(?P<kind>[^"]*)"'
)
NAME = re.compile(r'"name":"([^"]+)"')
# How far back from an event's dates to look for its name in the page data.
NAME_LOOKBACK = 1500
# The ISU writes some countries formally; the Hub uses everyday names.
COUNTRY_NAMES = {"Republic of Korea": "South Korea", "United States of America": "USA"}


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    page = page_data(get(client, EVENTS_URL.format(discipline=sport.params["discipline"])).text)
    matches = list(EVENT.finditer(page))
    if not matches:
        raise SourceError("ISU events page has no event data; the page layout may have changed")

    events: dict[tuple[str, date], Event] = {}  # the page repeats events in several lists
    for m in matches:
        if "Junior" in m["kind"]:
            continue
        names = NAME.findall(page, max(0, m.start() - NAME_LOOKBACK), m.start())
        if not names:
            raise SourceError("an ISU event in the page data has no name")
        venue_zone = zone(m["tz"])
        if venue_zone is None:
            raise SourceError(f"ISU event {names[-1]!r} has an unknown time zone {m['tz']!r}")
        day = _local_date(m["start"], venue_zone)
        event = Event(
            sport_id=sport.id,
            name=names[-1],
            day=day,
            end_day=_local_date(m["end"], venue_zone),
            location=place(m["city"], COUNTRY_NAMES.get(m["country"], m["country"])),
        )
        events.setdefault((event.name, day), event)
    return list(events.values())


def _local_date(stamp: str, venue_zone: ZoneInfo) -> date:
    try:
        return datetime.fromisoformat(stamp).astimezone(timezone.utc).astimezone(venue_zone).date()
    except ValueError as exc:
        raise SourceError(f"ISU event date {stamp!r} isn't a timestamp") from exc
