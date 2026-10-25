"""Small parsing helpers shared by several fetchers."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def place(*parts: str | None) -> str | None:
    """Join the non-empty parts of a location, e.g. ("Beijing", "China") -> "Beijing, China"."""
    return ", ".join(p.strip() for p in parts if p and p.strip()) or None


def page_data(html: str) -> str:
    """Un-escape the JSON-in-JS data some sites embed in their pages, so it can be read with regexes."""
    return html.replace('\\"', '"')


def zone(name: str) -> ZoneInfo | None:
    """The IANA time zone called `name`, or None if there's no such zone."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None
