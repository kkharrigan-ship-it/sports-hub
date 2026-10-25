"""The Alert emails a Refresh sends Katie: problems after a run, or a note that the Hub wasn't updated.

(The Monday highlights email is the Notification, a separate thing.)
"""

from datetime import date

from sports_hub.mail import MailSettings, Message
from sports_hub.model import Sport
from sports_hub.refresh import Alert


def day_label(today: date) -> str:
    return today.strftime("%a, %b ") + str(today.day)


def hub_line(hub_url: str | None) -> list[str]:
    return [f"The Hub: {hub_url}"] if hub_url else []


def alert_message(alerts: list[Alert], sports: list[Sport], today: date, settings: MailSettings) -> Message | None:
    if not alerts:
        return None
    names = {s.id: s.name for s in sports}
    count = len(alerts)
    lines = [
        f"The Hub was still updated today, but {'a Sport needs' if count == 1 else 'some Sports need'} a look:",
        "",
        *[f"- {names.get(a.sport_id, a.sport_id)}: {a.message}" + (" (warning)" if a.level == "warning" else "") for a in alerts],
        "",
        "Sports whose source failed are showing their last good Events, marked stale.",
        "If a source keeps failing for a week or two, its page may have changed and the fetcher needs updating.",
        "",
        *hub_line(settings.hub_url),
    ]
    return Message(
        to=settings.alert_to,
        subject=f"Sports Hub: {count} problem{'s' if count != 1 else ''} in the {day_label(today)} Refresh",
        text="\n".join(lines) + "\n",
    )


def not_updated_message(reason: str, today: date, settings: MailSettings) -> Message:
    lines = [
        "The Refresh stopped, so the Hub was not updated today. It's still showing the last good version.",
        "",
        f"Why: {reason}",
        "",
        "Nothing is lost; once this is fixed the next Refresh catches up.",
        "",
        *hub_line(settings.hub_url),
    ]
    return Message(to=settings.alert_to, subject=f"Sports Hub: not updated on {day_label(today)}", text="\n".join(lines) + "\n")
