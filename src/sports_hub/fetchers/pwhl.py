"""PWHL games from HockeyTech, the stats feed behind thepwhl.com.

Two steps: the seasons list (to find the current regular season), then that
season's schedule.
"""

import json
from datetime import date, datetime, timezone
from typing import Any

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.fetchers.parsing import place
from sports_hub.model import Event, Sport

FEED_URL = "https://lscluster.hockeytech.com/feed/index.php"
# Not a secret: this is the public site key embedded in thepwhl.com's own pages.
SITE = {"feed": "modulekit", "key": "694cfeed58c932ee", "client_code": "pwhl", "fmt": "json"}


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    seasons = _feed_list(get(client, FEED_URL, {**SITE, "view": "seasons"}), "Seasons")
    season_id = _current_regular_season(seasons, today)
    games = _feed_list(get(client, FEED_URL, {**SITE, "view": "schedule", "season_id": season_id}), "Schedule")
    try:
        return [_game(sport.id, g) for g in games]
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"PWHL game entry has an unexpected shape ({exc})") from exc


def _feed_list(response: httpx.Response, key: str) -> list[dict[str, Any]]:
    text = response.text.strip()
    if text.startswith("(") and text.endswith(")"):  # the feed sometimes answers as JSONP
        text = text[1:-1]
    try:
        items = json.loads(text)["SiteKit"][key]
    except (ValueError, KeyError, TypeError) as exc:
        raise SourceError(f"PWHL feed no longer has the expected {key} list") from exc
    if not isinstance(items, list):
        raise SourceError(f"PWHL {key} is not a list")
    return items


def _current_regular_season(seasons: list[dict[str, Any]], today: date) -> str:
    """The regular season that is running or next to start (not preseason or playoffs)."""
    try:
        regular = [
            s for s in seasons
            if "Regular Season" in s["season_name"] and date.fromisoformat(s["end_date"]) >= today
        ]
        if not regular:
            raise SourceError("PWHL feed lists no current or upcoming regular season")
        return str(min(regular, key=lambda s: s["start_date"])["season_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"PWHL season entry has an unexpected shape ({exc})") from exc


def _game(sport_id: str, game: dict[str, Any]) -> Event:
    location = place(game["venue_name"].split("|")[0], game.get("venue_location"))
    name = f"{game['visiting_team_name']} at {game['home_team_name']}"
    if game.get("time_tbd") == "1":
        return Event(sport_id=sport_id, name=name, day=date.fromisoformat(game["date_played"]), location=location)
    start = datetime.fromisoformat(game["GameDateISO8601"]).astimezone(timezone.utc)
    return Event(sport_id=sport_id, name=name, day=start.date(), start=start, location=location)
