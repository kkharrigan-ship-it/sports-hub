"""The Hub's window rule: the next 56 days, or the next 6 Events if that's fewer."""

from datetime import date, timedelta

from sports_hub.model import Event

WINDOW_DAYS = 56
MIN_EVENTS = 6


def horizon(today: date) -> date:
    return today + timedelta(days=WINDOW_DAYS)


def upcoming(events: list[Event], today: date) -> list[Event]:
    """Events not yet over, in time order. A multi-day Event still running today counts."""
    return sorted((e for e in events if e.last_day >= today), key=lambda e: e.sort_key)


def in_window(events: list[Event], today: date) -> list[Event]:
    ahead = upcoming(events, today)
    window = [e for e in ahead if e.day <= horizon(today)]
    return window if len(window) >= MIN_EVENTS else ahead[:MIN_EVENTS]
