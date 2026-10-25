"""Domain types: Sports, Events, Watch options and the last-good state (see CONTEXT.md)."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Literal

WatchType = Literal["have", "free", "vpn", "consider"]
SportStatus = Literal["in-season", "off-season", "unavailable"]

# Event tag marking a Grand Slam of Curling event (drives the ESPN+ reminder).
SLAM_TAG = "slam"


@dataclass(frozen=True)
class WatchOption:
    label: str
    type: WatchType
    price: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Sport:
    id: str
    name: str
    category: str
    sources: tuple[str, ...]
    watch: tuple[WatchOption, ...] = ()
    rights_unconfirmed: bool = False
    returns: str | None = None
    offseason_note: str | None = None
    params: dict[str, str] = field(default_factory=dict)
    season_events: tuple["Event", ...] = ()

    @property
    def ranked_watch(self) -> tuple[WatchOption, ...]:
        """Watch options as the Hub shows them: owned, then free, then paid.
        VPN routes appear only when there's no owned or free legal option."""
        def of_type(t: WatchType) -> tuple[WatchOption, ...]:
            return tuple(w for w in self.watch if w.type == t)

        legal = of_type("have") + of_type("free")
        return legal + of_type("consider") + (() if legal else of_type("vpn"))

    def state_key(self, source: str) -> str:
        """Last-good state is kept per source, so a Sport with two sources can fall back on just one."""
        return self.id if len(self.sources) == 1 else f"{self.id}/{source}"


@dataclass(frozen=True)
class Event:
    """One dated session or competition. `start` is None for all-day Events."""

    sport_id: str
    name: str
    day: date
    start: datetime | None = None
    session: str | None = None
    location: str | None = None
    end_day: date | None = None
    tags: tuple[str, ...] = ()
    source_url: str | None = None

    def __post_init__(self) -> None:
        if self.start is not None and self.start.utcoffset() != timezone.utc.utcoffset(None):
            raise ValueError("Event.start must be a UTC datetime")

    @property
    def last_day(self) -> date:
        return self.end_day or self.day

    @property
    def all_day(self) -> bool:
        return self.start is None

    @property
    def sort_key(self) -> tuple[date, datetime]:
        return (self.day, self.start or datetime.combine(self.day, datetime.min.time(), timezone.utc))


@dataclass(frozen=True)
class LastGood:
    """A Sport's Events from its most recent successful fetch."""

    fetched_on: date
    events: tuple[Event, ...]


@dataclass(frozen=True)
class State:
    """What a Refresh leaves for the next one: when it ran and each Sport's last-good Events."""

    refreshed_on: date
    sports: dict[str, LastGood]
    notified_on: date | None = None  # last Monday the Notification went out, so a re-run doesn't repeat it
