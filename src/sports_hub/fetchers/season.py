"""The Season file as a source: hand-checked Events, already loaded with the Sports config."""

from datetime import date

import httpx

from sports_hub.model import Event, Sport


def fetch(client: httpx.Client, sport: Sport, today: date) -> list[Event]:
    return list(sport.season_events)
