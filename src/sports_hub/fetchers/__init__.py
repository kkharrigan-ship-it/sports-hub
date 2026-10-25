"""Fetchers turn one source into Events.

Every fetcher has the same contract: given an HTTP client, the Sport and
"today", return that Sport's Events from the source, or raise SourceError.
Past Events may be included; the Refresh trims to the window. Fetchers only
need to reach far enough ahead for the window rule (the next 56 days, or the
next 6 Events if that is fewer).
"""

from collections.abc import Callable
from datetime import date

import httpx

from sports_hub.fetchers import fis, ibu, isu, jolpica, motogp, pwhl, season, six_nations, world_aquatics
from sports_hub.model import Event, Sport

Fetcher = Callable[[httpx.Client, Sport, date], list[Event]]

FETCHERS: dict[str, Fetcher] = {
    "jolpica": jolpica.fetch,
    "fis": fis.fetch,
    "ibu": ibu.fetch,
    "pwhl": pwhl.fetch,
    "world_aquatics": world_aquatics.fetch,
    "motogp": motogp.fetch,
    "six_nations": six_nations.fetch,
    "isu": isu.fetch,
    "season": season.fetch,
}

# How each source is named in Alerts, in plain words.
SOURCE_NAMES: dict[str, str] = {
    "jolpica": "the Jolpica F1 calendar",
    "fis": "the FIS calendar feed",
    "ibu": "the IBU results API",
    "pwhl": "the PWHL schedule feed",
    "world_aquatics": "the World Aquatics API",
    "motogp": "the MotoGP calendar",
    "six_nations": "the Six Nations fixtures page",
    "isu": "the ISU events page",
    "season": "the Season file",
}
