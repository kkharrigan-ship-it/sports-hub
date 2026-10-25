"""Milestone 2 completeness (ticket 15): the Hub has exactly the 19 agreed Sports, fully configured."""

import re
from datetime import date
from pathlib import Path

import httpx

from sports_hub.config import load_sports
from sports_hub.refresh import refresh

AGREED = {
    "pwhl", "curling-ca", "curling-intl", "speed-skating", "short-track", "swimming", "diving",
    "gymnastics", "alpine", "snowboard", "freestyle", "biathlon", "f1", "motogp", "sailgp", "wec",
    "diamond-league", "world-skate", "ireland-rugby",
}
WATCH_GUIDE = Path(__file__).parents[1] / "docs" / "research" / "watch-guide-2026-27.md"


def recheck_list() -> set[str]:
    """Sport ids listed under the watch guide's "Recheck list" heading."""
    text = WATCH_GUIDE.read_text(encoding="utf-8")
    section = text.split("## Recheck list", 1)[1].split("\n## ", 1)[0]
    bullets = [line for line in section.splitlines() if line.startswith("- ")]
    return {sport_id for line in bullets for sport_id in re.findall(r"[a-z]+(?:-[a-z]+)*", line.split("(")[0]) if sport_id != "and"}


def test_config_has_exactly_the_19_agreed_sports() -> None:
    ids = [s.id for s in load_sports()]

    assert len(ids) == len(set(ids)) == 19
    assert set(ids) == AGREED


def test_every_sport_has_watch_options_and_paid_ones_have_a_price() -> None:
    for sport in load_sports():
        assert sport.watch, sport.id
        for option in sport.watch:
            if option.type == "consider":
                assert option.price, f"{sport.id}: {option.label}"


def test_every_sport_has_an_off_season_label() -> None:
    for sport in load_sports():
        assert sport.returns and sport.offseason_note, sport.id


def test_rights_flags_match_the_watch_guide() -> None:
    assert recheck_list() >= {"wec", "ireland-rugby"}, "the Recheck list heading should still parse"
    assert {s.id for s in load_sports() if s.rights_unconfirmed} == recheck_list()


def test_a_full_refresh_has_no_alerts_and_every_sport_is_shown_or_labelled(client: httpx.Client) -> None:
    result = refresh(today=date(2026, 10, 24), client=client, previous=None, sports=load_sports())

    assert result.alerts == []
    for sport in result.data["sports"]:
        assert (sport["status"] == "in-season" and sport["events"]) or (
            sport["status"] == "off-season" and sport["returns"]
        ), sport["id"]
