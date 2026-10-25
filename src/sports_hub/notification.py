"""The Monday Notification: this week's highlights for Katie and Jason, by day, in Central time.

Built from the Refresh's own data.json content, so it always matches the Hub.
Same-Sport, same-day sessions share one line (e.g. "Practice 3 & Qualifying"),
as the old Cowork Digest did. Multi-day Events appear once, on the first day
of the week they're on.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sports_hub.mail import Message

CENTRAL = ZoneInfo("America/Chicago")
RULE = "─" * 29
NOTIFICATION_DAY = 0  # Monday

# One emoji per Sport, as in the old Digest (these sit in the email only, not the Hub's names).
SPORT_EMOJI = {
    "pwhl": "🏒", "curling-ca": "🥌", "curling-intl": "🥌", "speed-skating": "⛸️", "short-track": "⛸️",
    "swimming": "🏊", "diving": "🏊", "gymnastics": "🤸", "alpine": "⛷️", "freestyle": "⛷️", "snowboard": "🏂",
    "biathlon": "🎿", "f1": "🏎️", "motogp": "🏍️", "sailgp": "⛵", "wec": "🏁", "diamond-league": "🏃",
    "world-skate": "🛹", "ireland-rugby": "🏉",
}


def is_notification_day(today: date) -> bool:
    return today.weekday() == NOTIFICATION_DAY


@dataclass
class _Line:
    """One line of the email: an Event (or a Sport's same-day sessions of one Event)."""

    sport: dict[str, Any]
    name: str
    sort: str
    sessions: list[str] = field(default_factory=list)
    times: list[str] = field(default_factory=list)
    when: str | None = None  # for all-day and multi-day Events
    location: str | None = None


def notification_message(data: dict[str, Any], today: date, to: tuple[str, ...], hub_url: str | None) -> Message:
    week_end = today + timedelta(days=6)
    days: dict[date, dict[tuple[str, str], _Line]] = defaultdict(dict)
    later: list[tuple[str, str]] = []  # (sort key, description) of Events after this week

    for sport in data["sports"]:
        for ev in sport["events"]:
            day, sort, time_text = _placement(ev, today)
            if day is None or day > week_end:
                if day is not None:
                    later.append((sort, f"{sport['name']}: {ev['name']} on {_day_text(day)}"))
                continue
            line = days[day].setdefault((sport["id"], ev["name"]), _Line(sport=sport, name=ev["name"], sort=sort))
            if ev.get("session"):
                line.sessions.append(ev["session"])
            if time_text:
                line.times.append(time_text)
            elif line.when is None:
                line.when = _range_text(ev)
            line.location = line.location or ev.get("location")

    lines = [
        "Hi Katie and Jason!",
        "",
        "Here's what's on in sports this week. All times are Central (Memphis) time.",
        "",
    ]
    if days:
        for day in sorted(days):
            lines += [RULE, _day_text(day).upper(), RULE]
            for line in sorted(days[day].values(), key=lambda entry: entry.sort):
                lines += _line_text(line)
    else:
        nxt = min(later)[1] if later else None
        lines += [
            "Nothing on this week across all 19 sports. A good week for a walk! 🌿",
            f"Next up: {nxt}." if nxt else "The next dates haven't been announced yet.",
            "",
        ]

    reminder = _reminder_this_week(data, today, week_end)
    if reminder:
        starts = date.fromisoformat(reminder["date"])
        when = "is on now" if starts <= today else f"starts {_day_text(starts)}"
        lines += [f"📺 Heads-up: the {reminder['name']} Grand Slam {when}. Time to switch ESPN+ on if you'd like to watch.", ""]

    lines += ["Everything else, plus calendar links:" + (f" {hub_url}" if hub_url else " the Sports Hub page."), "",
              "— Your Sports Hub 🏅"]
    return Message(to=to, subject=f"🏅 What's on this week: Sports Hub, {today.strftime('%b')} {today.day}",
                   text="\n".join(lines) + "\n")


def _placement(ev: dict[str, Any], today: date) -> tuple[date | None, str, str | None]:
    """The day an Event shows on (Central time), a sort key, and its time text (None if all-day)."""
    if ev.get("start"):
        local = datetime.fromisoformat(ev["start"].replace("Z", "+00:00")).astimezone(CENTRAL)
        if local.date() < today:
            return None, "", None
        return local.date(), local.isoformat(), local.strftime("%I:%M %p").lstrip("0")
    first, last = date.fromisoformat(ev["date"]), date.fromisoformat(ev.get("end_date") or ev["date"])
    if last < today:
        return None, "", None
    shown = max(first, today)  # an Event already running shows on the first day of the week
    return shown, f"{shown.isoformat()}T00:00", None


def _line_text(line: _Line) -> list[str]:
    emoji = SPORT_EMOJI.get(line.sport["id"], "🏅")
    title = f"{line.sport['name']}: {line.name}"
    if line.sessions:
        title += f" ({' & '.join(line.sessions)})"
    detail = " & ".join(line.times) if line.times else (line.when or "All day")
    if line.location:
        detail += f" · {line.location}"
    out = [f"{emoji}  {title}", f"    {detail}"]
    if line.sport.get("watch"):
        best = line.sport["watch"][0]
        out.append(f"    📺 {best['label']}" + (f" ({best['note']})" if best.get("note") else ""))
    return out + [""]


def _range_text(ev: dict[str, Any]) -> str:
    first, last = date.fromisoformat(ev["date"]), date.fromisoformat(ev.get("end_date") or ev["date"])
    return f"{_day_text(first)} – {_day_text(last)}" if last != first else "All day"


def _day_text(day: date) -> str:
    return f"{day.strftime('%a, %b')} {day.day}"


def _reminder_this_week(data: dict[str, Any], today: date, week_end: date) -> dict[str, Any] | None:
    for r in data.get("reminders", []):
        if date.fromisoformat(r["show_from"]) <= week_end and date.fromisoformat(r["end_date"]) >= today:
            return dict(r)
    return None
