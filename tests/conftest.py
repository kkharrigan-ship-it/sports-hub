"""Shared test helpers: a fake internet that serves saved real responses."""

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from sports_hub.mail import MailError, Message
from sports_hub.model import State
from sports_hub.config import load_sports
from sports_hub.refresh import RefreshResult, refresh
from sports_hub.serialize import state_from_json, state_to_json

FIXTURES = Path(__file__).parent / "fixtures"


def sport_entry(result: RefreshResult, sport_id: str) -> dict[str, Any]:
    """One Sport's entry in the Refresh's data.json."""
    found: dict[str, Any] = next(s for s in result.data["sports"] if s["id"] == sport_id)
    return found


def refreshed_entry(client: httpx.Client, sport_id: str, today: date) -> dict[str, Any]:
    """Run a full Refresh with the real config and return one Sport's entry."""
    result = refresh(today=today, client=client, previous=None, sports=load_sports())
    return sport_entry(result, sport_id)


@dataclass
class FakeSender:
    """Records messages instead of sending them (Seam 2). `refuse=True` behaves like Gmail saying no."""

    refuse: bool = False
    sent: list[Message] = field(default_factory=list)

    def send(self, message: Message) -> None:
        if self.refuse:
            raise MailError("Gmail couldn't be reached or refused the email (simulated)")
        self.sent.append(message)


def through_disk(state: State) -> State:
    """Round-trip state through its JSON file format, as the CLI does between runs."""
    return state_from_json(json.loads(json.dumps(state_to_json(state))))

# Saved responses keyed by (host, path, a query fragment that must be present).
ROUTES: list[tuple[str, str, str, str]] = [
    ("api.jolpi.ca", "/ergast/f1/2026.json", "", "jolpica_f1_2026.json"),
    ("api.jolpi.ca", "/ergast/f1/2027.json", "", "jolpica_f1_2027.json"),
    ("www.fis-ski.com", "/DB/services/public/icalendar-feed-fis-events.html", "sectorcode=AL", "fis_AL.ics"),
    ("www.fis-ski.com", "/DB/services/public/icalendar-feed-fis-events.html", "sectorcode=SB", "fis_SB.ics"),
    ("www.fis-ski.com", "/DB/services/public/icalendar-feed-fis-events.html", "sectorcode=FS", "fis_FS.ics"),
    ("www.biathlonresults.com", "/modules/sportapi/api/Events", "", "ibu_events_2627.json"),
    ("lscluster.hockeytech.com", "/feed/index.php", "view=seasons", "pwhl_seasons.json"),
    ("lscluster.hockeytech.com", "/feed/index.php", "season_id=11", "pwhl_modulekit_schedule_11.json"),
    ("api.worldaquatics.com", "/fina/competitions", "disciplines=SW", "wa_SW.json"),
    ("api.worldaquatics.com", "/fina/competitions", "disciplines=DV", "wa_DV.json"),
    ("api.motogp.pulselive.com", "/motogp/v1/events", "seasonYear=2026", "motogp_events_2026.json"),
    ("isu-skating.com", "/en/short-track/events/", "", "isu_short-track_events.html"),
    ("isu-skating.com", "/en/speed-skating/events/", "", "isu_speed-skating_events.html"),
    ("www.sixnationsrugby.com", "/en/m6n/fixtures/202700", "", "six_nations_m6n_2027.html"),
    ("api.motogp.pulselive.com", "/motogp/v1/events", "seasonYear=2027", "motogp_events_2027.json"),
] + [
    ("www.biathlonresults.com", "/modules/sportapi/api/Competitions", f"EventId={event_id}", f"ibu_competitions_{event_id}.json")
    for event_id in [f"BT2627SWRLCP0{n}" for n in range(1, 8)]
]


class FakeInternet:
    """Serves saved responses; individual URLs can be overridden to simulate breakage."""

    def __init__(self) -> None:
        self.overrides: dict[str, Callable[[httpx.Request], httpx.Response]] = {}
        self.query_overrides: list[tuple[str, str, bytes]] = []
        self.requests: list[httpx.Request] = []

    def break_host(self, host: str, response: httpx.Response | None = None) -> None:
        """Make every request to `host` fail (network error) or return `response`."""

        def handler(request: httpx.Request) -> httpx.Response:
            if response is None:
                raise httpx.ConnectError("simulated outage", request=request)
            return response

        self.overrides[host] = handler

    def serve(self, host: str, path: str, body: bytes) -> None:
        """Replace the saved response for one host+path."""
        self.overrides[host + path] = lambda request: httpx.Response(200, content=body)

    def serve_query(self, host: str, fragment: str, body: bytes) -> None:
        """Replace the saved response for requests to `host` whose query contains `fragment`."""
        self.query_overrides.append((host, fragment, body))

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = request.url
        for host, fragment, body in self.query_overrides:
            if url.host == host and fragment in url.query.decode():
                return httpx.Response(200, content=body)
        for key in (url.host + url.path, url.host):
            if key in self.overrides:
                return self.overrides[key](request)
        query = url.query.decode()
        for host, path, fragment, filename in ROUTES:
            if url.host == host and url.path == path and fragment in query:
                return httpx.Response(200, content=(FIXTURES / filename).read_bytes())
        return httpx.Response(404, content=b"no saved response for " + str(url).encode())


@pytest.fixture
def internet() -> FakeInternet:
    return FakeInternet()


@pytest.fixture
def client(internet: FakeInternet) -> Iterator[httpx.Client]:
    with httpx.Client(transport=httpx.MockTransport(internet.handle)) as c:
        yield c
