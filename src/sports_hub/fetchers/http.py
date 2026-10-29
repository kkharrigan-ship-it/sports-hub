"""Shared HTTP helper so every fetcher reports failures the same way."""

import httpx

from sports_hub.errors import SourceError

# Identifies us honestly, with a contact link, as sites like Wikipedia ask automated visitors to.
USER_AGENT = "sports-hub/0.1 (personal hobby project; twice-weekly schedule refresh; +https://github.com/kkharrigan-ship-it/sports-hub)"


def get(client: httpx.Client, url: str, params: dict[str, str] | None = None) -> httpx.Response:
    try:
        response = client.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    except httpx.HTTPError as exc:
        raise SourceError(f"couldn't reach {httpx.URL(url).host} ({type(exc).__name__})") from exc
    if response.status_code != 200:
        raise SourceError(f"{httpx.URL(url).host} answered HTTP {response.status_code}")
    return response
