"""The weekly Season-file check: has any page the Season file cites changed?

Each distinct source page is fetched once (politely), reduced to its visible
text with obvious noise removed (scripts, styles, timestamps, build ids), and
fingerprinted. A changed fingerprint means a date may have moved, so the check
produces a review for Katie listing the page and the Season-file entries that
cite it. It never edits the Season file.

Sites that refuse automated visitors are listed as "couldn't check". Their
entries can't be fingerprinted, so instead each one gets two looks from the
Claude check (ticket 32), which can read other sources about it: the week it
enters the Hub's 8-week window, and the week it's two weeks away. That keeps a
site that always blocks us from raising a review (and using Pro allowance)
every single week.
"""

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from html.parser import HTMLParser

import httpx

from sports_hub.fetchers.http import USER_AGENT
from sports_hub.model import Sport
from sports_hub.window import horizon

# Start times stay in: a moved start time is a change worth seeing.
NOISE = [
    re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:?\d\d)?"),  # ISO timestamps
    re.compile(r"\b\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago\b", re.I),     # "3 days ago"
    re.compile(r"\b[A-Za-z0-9_-]{24,}\b"),                                         # build ids, nonces, hashes
]
WEEK = timedelta(days=7)
SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}


@dataclass(frozen=True)
class Citation:
    sport: str
    event: str
    day: date
    last_day: date


@dataclass
class Page:
    url: str
    citations: list[Citation] = field(default_factory=list)


@dataclass
class CheckResult:
    changed: list[Page]
    unreachable: list[tuple[Page, str]]
    fingerprints: dict[str, str]

    def needs_claude(self, today: date) -> bool:
        """A changed page with an entry still to come, or an unreachable page's entry that's due a look."""
        return any(_ahead(page, today) for page in self.changed) or any(
            _due(c, today) for page, _ in self.unreachable for c in page.citations
        )


def _ahead(page: Page, today: date) -> list[Citation]:
    return [c for c in page.citations if c.last_day >= today]


def _in_window(page: Page, today: date) -> list[Citation]:
    return [c for c in _ahead(page, today) if c.day <= horizon(today)]


def _due(c: Citation, today: date) -> bool:
    """The week an entry enters the 8-week window, or the week it's two weeks away (weekly runs)."""
    return horizon(today) - WEEK < c.day <= horizon(today) or today + WEEK < c.day <= today + 2 * WEEK


def cited_pages(sports: list[Sport]) -> list[Page]:
    pages: dict[str, Page] = {}
    for sport in sports:
        for e in sport.season_events:
            if e.source_url:
                pages.setdefault(e.source_url, Page(e.source_url)).citations.append(
                    Citation(sport.name, e.name, e.day, e.last_day)
                )
    return list(pages.values())


def check(client: httpx.Client, sports: list[Sport], previous: dict[str, str], pause: Callable[[], None]) -> CheckResult:
    changed: list[Page] = []
    unreachable: list[tuple[Page, str]] = []
    fingerprints = dict(previous)
    for n, page in enumerate(cited_pages(sports)):
        if n:
            pause()
        try:
            response = client.get(page.url, headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)
        except httpx.HTTPError as exc:
            unreachable.append((page, type(exc).__name__))
            continue
        if response.status_code != 200:
            unreachable.append((page, f"HTTP {response.status_code}"))
            continue
        fingerprint = page_fingerprint(response.text)
        if page.url in previous and previous[page.url] != fingerprint:
            changed.append(page)
        fingerprints[page.url] = fingerprint
    return CheckResult(changed=changed, unreachable=unreachable, fingerprints=fingerprints)


def page_fingerprint(html: str) -> str:
    text = _visible_text(html)
    for pattern in NOISE:
        text = pattern.sub(" ", text)
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


def review_report(result: CheckResult, today: date) -> str:
    lines = [f"# Season-file review: {_day(today)}", ""]
    changed = [(page, citations) for page in result.changed if (citations := _ahead(page, today))]
    if changed:
        lines += ["## Pages that changed", "",
                  "These pages are cited in `config/seasons/` and their text changed since last week. "
                  "Check whether any of these dates moved:", ""]
        for page, citations in changed:
            lines += [f"- {page.url}", *_entries(citations)]
        lines.append("")
    blocked = [(page, reason, citations) for page, reason in result.unreachable if (citations := _in_window(page, today))]
    if blocked:
        lines += ["## Couldn't check", "",
                  "These sites refused the check or didn't answer. Their entries in the next 8 weeks:", ""]
        for page, reason, citations in blocked:
            lines += [f"- {page.url} ({reason})", *_entries(citations)]
        lines.append("")
    lines += ["## What to do", "",
              "Open each page, compare it with the entries listed, and fix `config/seasons/2026-27.yaml` if a date moved. "
              "Close this issue once you've checked. Nothing is changed automatically.", ""]
    return "\n".join(lines)


def _entries(citations: list[Citation]) -> list[str]:
    return [f"  - {c.sport}: {c.event} ({_day(c.day, year=True)})" for c in citations]


def _day(d: date, year: bool = False) -> str:
    return f"{d.strftime('%a, %b')} {d.day}" + (f", {d.year}" if year else "")


class _TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skipping = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skipping += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skipping:
            self._skipping -= 1

    def handle_data(self, data: str) -> None:
        if not self._skipping:
            self.parts.append(data)


def _visible_text(html: str) -> str:
    parser = _TextOnly()
    parser.feed(html)
    return " ".join(parser.parts)
