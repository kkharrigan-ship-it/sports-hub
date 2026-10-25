"""JSON shapes: the Hub's data.json and the last-good state file."""

from datetime import date, datetime
from typing import Any

from sports_hub.calendar_feed import event_uid, feed_path
from sports_hub.errors import StateError
from sports_hub.model import Event, LastGood, Sport, SportStatus, State


def event_to_json(e: Event, stale_since: date | None = None) -> dict[str, Any]:
    return {
        "uid": event_uid(e),
        "name": e.name,
        "session": e.session,
        "date": e.day.isoformat(),
        "start": e.start.strftime("%Y-%m-%dT%H:%M:%SZ") if e.start else None,
        "all_day": e.all_day,
        "end_date": e.end_day.isoformat() if e.end_day else None,
        "location": e.location,
        "tags": list(e.tags),
        "source": e.source_url,
        "stale_since": stale_since.isoformat() if stale_since else None,
    }


def event_from_json(sport_id: str, d: dict[str, Any]) -> Event:
    return Event(
        sport_id=sport_id,
        name=d["name"],
        session=d.get("session"),
        day=date.fromisoformat(d["date"]),
        start=datetime.fromisoformat(d["start"]) if d.get("start") else None,
        location=d.get("location"),
        end_day=date.fromisoformat(d["end_date"]) if d.get("end_date") else None,
        tags=tuple(d.get("tags", ())),
        source_url=d.get("source"),
    )


def sport_to_json(
    sport: Sport, status: SportStatus, events: list[Event], stale: dict[Event, date] | None = None
) -> dict[str, Any]:
    """One Sport as the Hub page sees it.

    `stale` maps Events shown from last-good state to when they were fetched.
    The Sport's own stale_since is the oldest of those, so a Sport whose second
    source failed shows both its fresh and its stale Events, each marked.
    """
    stale = stale or {}
    stale_since = min((stale[e] for e in events if e in stale), default=None)
    off = status == "off-season"
    return {
        "id": sport.id,
        "name": sport.name,
        "category": sport.category,
        "status": status,
        "feed": feed_path(sport),
        "stale_since": stale_since.isoformat() if stale_since else None,
        "rights_unconfirmed": sport.rights_unconfirmed,
        "returns": sport.returns if off else None,
        "note": sport.offseason_note if off else None,
        "watch": [{"label": w.label, "type": w.type, "price": w.price, "note": w.note} for w in sport.ranked_watch],
        "events": [event_to_json(e, stale.get(e)) for e in events],
    }


def state_to_json(state: State) -> dict[str, Any]:
    return {
        "refreshed_on": state.refreshed_on.isoformat(),
        "notified_on": state.notified_on.isoformat() if state.notified_on else None,
        "sports": {
            sport_id: {"fetched_on": lg.fetched_on.isoformat(), "events": [event_to_json(e) for e in lg.events]}
            for sport_id, lg in state.sports.items()
        },
    }


def state_from_json(d: dict[str, Any]) -> State:
    try:
        return State(
            refreshed_on=date.fromisoformat(d["refreshed_on"]),
            notified_on=date.fromisoformat(d["notified_on"]) if d.get("notified_on") else None,
            sports={
                sport_id: LastGood(
                    fetched_on=date.fromisoformat(lg["fetched_on"]),
                    events=tuple(event_from_json(sport_id, e) for e in lg["events"]),
                )
                for sport_id, lg in d["sports"].items()
            },
        )
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise StateError(f"last-good state has an unexpected shape ({type(exc).__name__}: {exc})") from exc
