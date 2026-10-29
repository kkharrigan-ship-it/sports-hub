"""The weekly Season-file check (ticket 31), through the CLI with the fake internet.

Each test uses a small Season file whose entries cite a few made-up pages,
served by the fake internet, and checks the review the check would raise.
"""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from conftest import FakeInternet, FakeSender
from sports_hub.cli import run

TODAY = date(2026, 10, 28)
SEASON = """
sports:
  wec:
    events:
      - { name: 6 Hours of Monza, date: 2026-11-08, location: "Monza, Italy", source: "https://www.fia.example/monza" }
      - { name: Qatar 1812km, date: 2027-03-27, location: "Lusail, Qatar", source: "https://www.wec.example/calendar" }
      - { name: 6 Hours of Imola, date: 2027-04-11, location: "Imola, Italy", source: "https://www.wec.example/calendar" }
  curling-intl:
    events:
      - { name: European Curling Championships, date: 2026-10-27, end_date: 2026-11-01, location: "Ostrava", source: "https://curling.example/events" }
"""
PAGE = "<html><head><script>var build='{stamp}';</script></head><body><h1>Calendar</h1><p>{body}</p><footer>Updated {stamp}</footer></body></html>"


def page(body: str, stamp: str = "2026-10-28T07:00:01Z") -> bytes:
    return PAGE.format(body=body, stamp=stamp).encode()


@pytest.fixture
def season(tmp_path: Path) -> Path:
    path = tmp_path / "season.yaml"
    path.write_text(SEASON, encoding="utf-8")
    return path


def serve_all(internet: FakeInternet, monza: str = "Monza 8 November", calendar: str = "Qatar 27 March; Imola 11 April",
              stamp: str = "2026-10-28T07:00:01Z", curling_status: int = 403) -> None:
    internet.serve("www.fia.example", "/monza", page(monza, stamp))
    internet.serve("www.wec.example", "/calendar", page(calendar, stamp))
    internet.overrides["curling.example/events"] = lambda request: httpx.Response(curling_status, content=b"denied")


def check(tmp_path: Path, client: httpx.Client, season: Path, today: date = TODAY) -> dict[str, str]:
    out = tmp_path / "github_output.txt"
    out.write_text("")
    code = run(
        ["check-season", "--fingerprints", str(tmp_path / "fingerprints.json"), "--report", str(tmp_path / "review.md"),
         "--season-file", str(season), "--delay", "0", "--github-output", str(out)],
        today=today, client=client, env={}, sender=FakeSender(),
    )
    assert code == 0
    return dict(line.split("=", 1) for line in out.read_text().splitlines() if line)


def test_the_first_check_only_records_fingerprints(tmp_path: Path, client: httpx.Client, internet: FakeInternet,
                                                   season: Path) -> None:
    serve_all(internet)

    outputs = check(tmp_path, client, season)

    assert outputs["changed"] == "0"
    assert len(json.loads((tmp_path / "fingerprints.json").read_text())["pages"]) == 2


def test_an_unchanged_page_raises_nothing(tmp_path: Path, client: httpx.Client, internet: FakeInternet,
                                          season: Path) -> None:
    serve_all(internet)
    check(tmp_path, client, season)

    outputs = check(tmp_path, client, season, today=date(2026, 11, 4))

    assert outputs["changed"] == "0"


def test_only_a_timestamp_changing_is_not_a_change(tmp_path: Path, client: httpx.Client, internet: FakeInternet,
                                                   season: Path) -> None:
    serve_all(internet, stamp="2026-10-28T07:00:01Z")
    check(tmp_path, client, season)
    serve_all(internet, stamp="2026-11-04T07:00:09Z")

    assert check(tmp_path, client, season, today=date(2026, 11, 4))["changed"] == "0"


def test_a_changed_page_is_reported_with_the_entries_that_cite_it(tmp_path: Path, client: httpx.Client,
                                                                  internet: FakeInternet, season: Path) -> None:
    serve_all(internet)
    check(tmp_path, client, season)
    serve_all(internet, calendar="Qatar 27 March; Imola 18 April")

    outputs = check(tmp_path, client, season, today=date(2026, 11, 4))

    assert outputs["changed"] == "1"
    assert outputs["review"] == "true"
    report = (tmp_path / "review.md").read_text()
    assert "https://www.wec.example/calendar" in report
    assert "FIA WEC: Qatar 1812km (Sat, Mar 27, 2027)" in report
    assert "FIA WEC: 6 Hours of Imola (Sun, Apr 11, 2027)" in report
    assert "www.fia.example" not in report.split("## Couldn't check")[0]


def test_sites_that_refuse_us_are_listed_as_couldnt_check(tmp_path: Path, client: httpx.Client,
                                                          internet: FakeInternet, season: Path) -> None:
    serve_all(internet)

    outputs = check(tmp_path, client, season)

    report = (tmp_path / "review.md").read_text()
    assert "## Couldn't check" in report
    assert "https://curling.example/events (HTTP 403)" in report
    # The Euros are on now, inside 8 weeks, so Claude should look at them.
    assert outputs["claude"] == "true"


def test_unreachable_sources_with_nothing_soon_do_not_need_claude(tmp_path: Path, client: httpx.Client,
                                                                  internet: FakeInternet, season: Path) -> None:
    serve_all(internet)

    outputs = check(tmp_path, client, season, today=date(2026, 12, 15))

    assert outputs["claude"] == "false"
    assert outputs["review"] == "false"


def test_each_distinct_page_is_asked_for_once(tmp_path: Path, client: httpx.Client, internet: FakeInternet,
                                              season: Path) -> None:
    serve_all(internet)

    check(tmp_path, client, season)

    asked = [str(r.url) for r in internet.requests]
    assert sorted(asked) == ["https://curling.example/events", "https://www.fia.example/monza",
                             "https://www.wec.example/calendar"]
    assert all("sports-hub" in r.headers["User-Agent"] for r in internet.requests)


def test_an_unreachable_page_keeps_its_old_fingerprint(tmp_path: Path, client: httpx.Client, internet: FakeInternet,
                                                       season: Path) -> None:
    serve_all(internet)
    check(tmp_path, client, season)
    internet.break_host("www.wec.example")

    outputs = check(tmp_path, client, season, today=date(2026, 11, 4))
    serve_all(internet)
    later = check(tmp_path, client, season, today=date(2026, 11, 11))

    assert outputs["changed"] == "0"
    assert later["changed"] == "0"
