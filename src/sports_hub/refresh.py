"""The Refresh: fetch every Sport, apply the window rules, and produce the Hub's data.

This is the project's main seam. Callers (the CLI, the GitHub workflow, tests)
pass in "today", an HTTP client and the previous last-good state; nothing in
here reads the clock or the network on its own.

Reliability rules:
- One broken source never stops the others. Its Events come from last-good
  state, each marked stale, and an error Alert names the Sport (and, for a
  Sport with several sources, which source failed).
- "Today" may never be earlier than the previous Refresh (DateWentBackwards).
- A Sport whose Event count collapses over the same calendar range as the
  previous Refresh raises a warning Alert.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal

import httpx

from sports_hub.calendar_feed import DEFAULT_LENGTH, SportEvents, build_feeds
from sports_hub.errors import SourceError
from sports_hub.fetchers import FETCHERS, SOURCE_NAMES
from sports_hub.model import SLAM_TAG, Event, LastGood, Sport, State
from sports_hub.serialize import sport_to_json
from sports_hub.window import horizon, in_window, upcoming

# A drop warning needs at least this many previous Events in the overlap, and
# the new count must be below half of them.
DROP_MIN_PREVIOUS = 4
# The ESPN+ banner shows this long before each Grand Slam of Curling.
REMINDER_LEAD = timedelta(days=7)


class DateWentBackwards(Exception):
    """Today is earlier than the previous Refresh: the clock or the data is wrong."""


@dataclass(frozen=True)
class Alert:
    level: Literal["error", "warning"]
    sport_id: str
    message: str


@dataclass
class RefreshResult:
    data: dict[str, Any]
    state: State
    alerts: list[Alert] = field(default_factory=list)
    feeds: dict[str, bytes] = field(default_factory=dict)  # file name -> .ics content


def refresh(*, today: date, client: httpx.Client, previous: State | None, sports: list[Sport]) -> RefreshResult:
    if previous and previous.refreshed_on > today:
        raise DateWentBackwards(
            f"today is {today.isoformat()} but the last Refresh was {previous.refreshed_on.isoformat()}; "
            "refusing to publish older data"
        )

    alerts: list[Alert] = []
    entries: list[dict[str, Any]] = []
    last_good: dict[str, LastGood] = {}
    upcoming_by_sport: list[SportEvents] = []
    for sport in sports:
        events: list[Event] = []
        stale: dict[Event, date] = {}
        failed_without_last_good = 0
        for source in sport.sources:
            key = sport.state_key(source)
            previous_good = previous.sports.get(key) if previous else None
            try:
                fetched = FETCHERS[source](client, sport, today)
            except Exception as exc:  # one source must never take down the Refresh
                alerts.append(Alert("error", sport.id, _reason(sport, source, exc)))
                if previous_good:
                    last_good[key] = previous_good
                    events.extend(previous_good.events)
                    stale.update(dict.fromkeys(previous_good.events, previous_good.fetched_on))
                else:
                    failed_without_last_good += 1
                continue
            if previous and previous_good and (
                warning := _drop_warning(sport.id, fetched, previous_good, previous.refreshed_on, today)
            ):
                alerts.append(warning)
            last_good[key] = LastGood(fetched_on=today, events=tuple(fetched))
            events.extend(fetched)

        upcoming_by_sport.append((sport, upcoming(events, today)))
        if failed_without_last_good == len(sport.sources):
            entries.append(sport_to_json(sport, "unavailable", []))
        else:
            shown = in_window(events, today)
            entries.append(sport_to_json(sport, "in-season" if shown else "off-season", shown, stale))

    return RefreshResult(
        data={
            "last_updated": today.isoformat(),
            "event_length_hours": DEFAULT_LENGTH.total_seconds() / 3600,
            "sports": entries,
            "reminders": _espn_plus_reminders(upcoming_by_sport),
        },
        state=State(refreshed_on=today, sports=last_good),
        alerts=alerts,
        feeds=build_feeds(upcoming_by_sport, stamp=datetime.combine(today, time(), timezone.utc)),
    )


def _espn_plus_reminders(upcoming_by_sport: list[SportEvents]) -> list[dict[str, Any]]:
    """Grand Slams still to come, with the day the Hub should start reminding Katie to switch ESPN+ on."""
    slams = sorted((e for _, events in upcoming_by_sport for e in events if SLAM_TAG in e.tags), key=lambda e: e.day)
    return [
        {
            "id": f"{e.name}|{e.day.isoformat()}",  # one dismissal per Slam per season
            "kind": "espn-plus",
            "name": e.name,
            "date": e.day.isoformat(),
            "end_date": e.last_day.isoformat(),
            "show_from": (e.day - REMINDER_LEAD).isoformat(),
        }
        for e in slams
    ]


def _reason(sport: Sport, source: str, exc: Exception) -> str:
    reason = str(exc) if isinstance(exc, SourceError) else f"unexpected error while fetching ({type(exc).__name__}: {exc})"
    # With several sources, say which one failed, in plain words.
    return f"{SOURCE_NAMES[source]}: {reason}" if len(sport.sources) > 1 else reason


def _drop_warning(
    sport_id: str, events: list[Event], previous_good: LastGood, previous_refresh: date, today: date
) -> Alert | None:
    # Compare the same calendar range both Refreshes could see, so a season
    # tapering off (or ending) never looks like a drop.
    end = horizon(previous_refresh)
    then = sum(1 for e in previous_good.events if e.last_day >= today and e.day <= end)
    now = sum(1 for e in events if e.last_day >= today and e.day <= end)
    if then >= DROP_MIN_PREVIOUS and now * 2 < then:
        return Alert("warning", sport_id, f"Event count dropped from {then} to {now}; the source may have changed")
    return None
