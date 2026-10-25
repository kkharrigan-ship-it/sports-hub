"""Command line: `sports-hub refresh` runs a real Refresh (real clock, live network).

`run()` takes the clock, the HTTP client, the environment and the mail sender
as arguments, so tests can drive the whole command with fakes; `main()` wires
in the real ones.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

import httpx

from sports_hub.config import load_sports
from sports_hub.errors import ConfigError, StateError
from sports_hub.mail import GmailSender, MailError, MailSender, MailSettings, Message
from sports_hub.model import State
from sports_hub.alert_mail import alert_message, not_updated_message
from sports_hub.refresh import DateWentBackwards, refresh
from sports_hub.run_outcome import BUILT, BUILT_ALERT_UNSENT, STOPPED_ALERTED, STOPPED_NOT_ALERTED
from sports_hub.serialize import state_from_json, state_to_json
from sports_hub.site import write_hub

# "Today" is the date in Memphis, where Katie is, taken from the real clock.
HOME_ZONE = ZoneInfo("America/Chicago")


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(HOME_ZONE).date()
    with httpx.Client() as client:
        return run(argv, today=today, client=client, env=os.environ, sender=None)


def run(
    argv: list[str] | None, *, today: date, client: httpx.Client, env: Mapping[str, str], sender: MailSender | None
) -> int:
    parser = argparse.ArgumentParser(prog="sports-hub")
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("refresh", help="fetch every Sport and write the Hub (page, data.json, calendar feeds)")
    cmd.add_argument("--out", type=Path, default=Path("dist"), help="output folder (default: dist)")
    cmd.add_argument(
        "--state", type=Path, default=Path("state/last_good.json"), help="last-good state file, read and updated"
    )
    cmd.add_argument("--send-alerts", action="store_true", help="email Katie about Alerts or a stopped Refresh")
    args = parser.parse_args(argv)

    # Alerts are only sent when asked to. If they're asked for but the mail
    # settings are missing, the Hub is still built and the run reports it.
    settings: MailSettings | None = None
    if args.send_alerts:
        missing = MailSettings.missing(env)
        if missing:
            print(f"Can't send alert emails: set {', '.join(missing)} (see the README).", file=sys.stderr)
        else:
            settings = MailSettings.from_env(env)
            sender = sender or GmailSender(settings)

    try:
        sports = load_sports()
        previous = _read_state(args.state)
        result = refresh(today=today, client=client, previous=previous, sports=sports)
    except (ConfigError, StateError, DateWentBackwards) as exc:
        print(f"Refresh stopped: {exc}", file=sys.stderr)
        if not args.send_alerts:
            return STOPPED_ALERTED  # nobody to tell; the command's own message is enough
        sent = bool(settings and sender and _send(sender, not_updated_message(str(exc), today, settings)))
        return STOPPED_ALERTED if sent else STOPPED_NOT_ALERTED

    write_hub(args.out, result)
    _write_json(args.state, state_to_json(result.state))
    print(f"Wrote the Hub to {args.out} for {today.isoformat()}")
    for alert in result.alerts:
        print(f"{alert.level.upper()}: {alert.sport_id}: {alert.message}", file=sys.stderr)

    if not args.send_alerts:
        return BUILT
    if not (settings and sender):
        return BUILT_ALERT_UNSENT
    message = alert_message(result.alerts, sports, today, settings)
    if message and not _send(sender, message):
        return BUILT_ALERT_UNSENT
    return BUILT


def _send(sender: MailSender, message: Message) -> bool:
    try:
        sender.send(message)
        return True
    except MailError as exc:
        print(f"Refresh couldn't send the alert email: {exc}", file=sys.stderr)
        return False


def _read_state(path: Path) -> State | None:
    if not path.exists():
        return None
    try:
        return state_from_json(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, StateError) as exc:
        raise StateError(
            f"{path} can't be read ({exc}). Restore it from git, or delete it to start fresh "
            "(stale fallback is unavailable for one run)."
        ) from exc


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
