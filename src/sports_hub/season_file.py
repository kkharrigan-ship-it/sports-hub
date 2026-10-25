"""Reads the Season file: hand-checked Events and off-season labels per Sport.

The file is meant to be edited by hand, so every problem is reported as a
ConfigError naming the Sport and entry number.
"""

import dataclasses
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from sports_hub.errors import ConfigError
from sports_hub.fetchers.parsing import zone
from sports_hub.model import Event, Sport

TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


@dataclass(frozen=True)
class SeasonSport:
    returns: str | None = None
    offseason_note: str | None = None
    events: tuple[Event, ...] = field(default_factory=tuple)

    def apply_to(self, sport: Sport) -> Sport:
        return dataclasses.replace(
            sport, returns=self.returns, offseason_note=self.offseason_note, season_events=self.events
        )


def load_season_file(path: Path) -> dict[str, SeasonSport]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"{path.name}: can't be read ({exc})") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("sports"), dict):
        raise ConfigError(f"{path.name}: needs a top-level 'sports:' mapping")
    return {str(sport_id): _season_sport(str(sport_id), body) for sport_id, body in raw["sports"].items()}


def _season_sport(sport_id: str, body: Any) -> SeasonSport:
    if body is None:
        return SeasonSport()
    if not isinstance(body, dict):
        raise ConfigError(f"Season file {sport_id}: expected fields (returns, offseason_note, events)")
    entries = body.get("events") or []
    if not isinstance(entries, list):
        raise ConfigError(f"Season file {sport_id}: 'events' must be a list of entries")
    return SeasonSport(
        returns=body.get("returns"),
        offseason_note=body.get("offseason_note"),
        events=tuple(_event(sport_id, n, e) for n, e in enumerate(entries, start=1)),
    )


def _event(sport_id: str, n: int, entry: Any) -> Event:
    where = f"{sport_id} entry {n}"
    if not isinstance(entry, dict):
        raise ConfigError(f"Season file {where}: expected a mapping of fields")
    for key in ("name", "date", "source"):
        if not entry.get(key):
            raise ConfigError(f"Season file {where}: missing '{key}'")
    tags = entry.get("tags", [])
    if not isinstance(tags, list):
        raise ConfigError(f"Season file {where}: 'tags' must be a list, e.g. [slam]")

    day = _date(where, "date", entry["date"])
    end_day = _date(where, "end_date", entry["end_date"]) if entry.get("end_date") else None
    start = None
    if entry.get("time"):
        time = str(entry["time"])
        if not TIME.match(time):
            raise ConfigError(f"Season file {where}: time '{time}' must be 24-hour HH:MM")
        if not entry.get("tz"):
            raise ConfigError(f"Season file {where}: a time needs a 'tz' (e.g. Europe/London)")
        venue_zone = zone(str(entry["tz"]))
        if venue_zone is None:
            raise ConfigError(f"Season file {where}: unknown time zone '{entry['tz']}'")
        local = datetime.combine(day, datetime.strptime(time, "%H:%M").time(), venue_zone)
        start = local.astimezone(timezone.utc)
        day = start.date()

    return Event(
        sport_id=sport_id,
        name=str(entry["name"]),
        session=entry.get("session"),
        day=day,
        start=start,
        location=entry.get("location"),
        end_day=end_day,
        tags=tuple(str(t) for t in tags),
        source_url=str(entry["source"]),
    )


def _date(where: str, key: str, value: Any) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ConfigError(f"Season file {where}: {key} '{value}' must be YYYY-MM-DD") from exc
