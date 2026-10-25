"""Subscribable calendar feeds (.ics): one per Sport, plus one for all Sports.

Feeds carry every upcoming Event, not just the Hub's 56-day window, so a
calendar subscription covers the whole season. Each Event's UID is built from
what identifies it (Sport, name, session, day), so when its time changes on
the same day a calendar app updates the entry instead of adding a duplicate.
"""

import hashlib
from datetime import datetime, timedelta

from icalendar import Calendar
from icalendar import Event as CalendarEvent

from sports_hub.model import Event, Sport

# Timed Events have no published end, so calendars get a sensible default length.
# The Hub page uses the same length (it's in data.json) for LIVE badges and its own .ics files.
DEFAULT_LENGTH = timedelta(hours=2)
PRODID = "-//Sports Hub//sports-hub//EN"
# Folder, inside the Hub, that holds the feeds.
FEEDS_DIR = "feeds"

SportEvents = tuple[Sport, list[Event]]


def feed_name(sport: Sport) -> str:
    return f"{sport.id}.ics"


def feed_path(sport: Sport) -> str:
    """Where the Hub page finds a Sport's feed, relative to the page."""
    return f"{FEEDS_DIR}/{feed_name(sport)}"


def build_feeds(events_by_sport: list[SportEvents], stamp: datetime) -> dict[str, bytes]:
    """Feeds keyed by file name. `stamp` (when the Refresh ran) is each entry's DTSTAMP."""
    feeds = {
        feed_name(sport): _calendar(sport.name, [(sport, e) for e in events], stamp) for sport, events in events_by_sport
    }
    everything = [(sport, e) for sport, events in events_by_sport for e in events]
    feeds["all.ics"] = _calendar("Sports Hub: all Sports", everything, stamp)
    return feeds


def event_uid(e: Event) -> str:
    """Stable while an Event's time changes on the same day. A move to another day
    gets a new id; subscribed calendars drop the old one when the feed updates."""
    key = "|".join([e.sport_id, e.name, e.session or "", e.day.isoformat()])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:20] + "@sports-hub"


def _calendar(title: str, entries: list[tuple[Sport, Event]], stamp: datetime) -> bytes:
    cal = Calendar()
    cal.add("prodid", PRODID)
    cal.add("version", "2.0")
    cal.add("x-wr-calname", title)
    for sport, e in sorted(entries, key=lambda pair: pair[1].sort_key):
        cal.add_component(_entry(sport, e, stamp))
    data: bytes = cal.to_ical()
    return data


def _entry(sport: Sport, e: Event, stamp: datetime) -> CalendarEvent:
    entry = CalendarEvent()
    entry.add("uid", event_uid(e))
    entry.add("dtstamp", stamp)
    entry.add("summary", f"{sport.name}: {e.name}" + (f" ({e.session})" if e.session else ""))
    if e.start is not None:
        entry.add("dtstart", e.start)
        entry.add("dtend", e.start + DEFAULT_LENGTH)
    else:
        entry.add("dtstart", e.day)
        entry.add("dtend", e.last_day + timedelta(days=1))  # iCal all-day ends are exclusive
    if e.location:
        entry.add("location", e.location)
    lines = [line for line in (e.session, e.location) if line]
    if sport.ranked_watch:
        lines.append(f"Watch: {sport.ranked_watch[0].label}")
    if e.source_url:
        lines.append(f"Checked at: {e.source_url}")
    entry.add("description", "\n".join(lines))
    return entry
