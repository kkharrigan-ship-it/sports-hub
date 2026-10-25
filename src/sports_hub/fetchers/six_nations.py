"""A team's Six Nations kickoffs from the official fixtures page (sixnationsrugby.com).

The Sport's `team` param picks the team by its three-letter code (e.g. IRE).

The page has no API; its fixture cards are embedded in the page's own data.
Each card is read for stadium, the two team codes and the kickoff (UTC), and
anything unexpected is a SourceError rather than a guess.
"""

import re
from datetime import date, datetime, timezone

import httpx

from sports_hub.errors import SourceError
from sports_hub.fetchers.http import get
from sports_hub.fetchers.parsing import page_data
from sports_hub.model import Event, Sport

FIXTURES_URL = "https://www.sixnationsrugby.com/en/m6n/fixtures/{year}00"
TEAMS = {"IRE": "Ireland", "ENG": "England", "FRA": "France", "SCO": "Scotland", "WAL": "Wales", "ITA": "Italy"}

CARD = '"data-testid":"fixture-card"'
STADIUM = re.compile(r'fixturesResultsCard_stadium[^"]*","children":"([^"]+)"')
TEAM_CODE = re.compile(r'fixturesResultsCard_teamName[^"]*","children":"([A-Z]{3})"')
KICKOFF = re.compile(r'"date":"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z)"')


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    page = page_data(get(client, FIXTURES_URL.format(year=championship_year(today))).text)
    cards = page.split(CARD)[1:]
    if not cards:
        raise SourceError("Six Nations fixtures page has no fixture cards; the page layout may have changed")
    events = [_match(sport.id, sport.params["team"], card) for card in cards]
    return [e for e in events if e is not None]


def championship_year(today: date) -> int:
    """The Six Nations runs Feb-Mar; from July on, the next one is shown."""
    return today.year + 1 if today.month >= 7 else today.year


def _match(sport_id: str, team: str, card: str) -> Event | None:
    stadium, kickoff = STADIUM.search(card), KICKOFF.search(card)
    codes = TEAM_CODE.findall(card)[:2]
    if stadium is None or kickoff is None or len(codes) != 2:
        raise SourceError("a Six Nations fixture card is missing its stadium, teams or kickoff")
    if team not in codes:
        return None
    unknown = [c for c in codes if c not in TEAMS]
    if unknown:
        raise SourceError(f"Six Nations fixture has an unknown team code {unknown[0]}")
    home, away = (TEAMS[c] for c in codes)
    start = datetime.fromisoformat(kickoff.group(1)).astimezone(timezone.utc).replace(microsecond=0)
    return Event(
        sport_id=sport_id,
        name=f"{home} v {away}",
        session="Six Nations",
        day=start.date(),
        start=start,
        location=stadium.group(1),
    )
