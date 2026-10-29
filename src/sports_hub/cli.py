"""Command line: `sports-hub refresh` runs a real Refresh (real clock, live network).

`run()` takes the clock, the HTTP client, the environment and the mail sender
as arguments, so tests can drive the whole command with fakes; `main()` wires
in the real ones.
"""

import argparse
import dataclasses
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

import httpx

from sports_hub.config import load_sports
from sports_hub.errors import ConfigError, StateError
from sports_hub.mail import ENV_NOTIFY_TO, GmailSender, MailError, MailSender, MailSettings, Message, recipients
from sports_hub.model import State
from sports_hub.notification import is_notification_day, notification_message
from sports_hub.alert_mail import alert_message, not_updated_message
from sports_hub.refresh import DateWentBackwards, refresh
from sports_hub.run_outcome import BUILT, BUILT_EMAIL_UNSENT, STOPPED_ALERTED, STOPPED_NOT_ALERTED
from sports_hub.serialize import state_from_json, state_to_json
from sports_hub.season_check import check, review_report
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
    cmd.add_argument(
        "--send-notification", action="store_true", help="on Mondays, email the week's highlights to SPORTS_HUB_NOTIFY_TO"
    )
    check_cmd = sub.add_parser("check-season", help="check the pages the Season file cites for changes")
    check_cmd.add_argument("--fingerprints", type=Path, default=Path("state/fingerprints.json"))
    check_cmd.add_argument("--report", type=Path, default=Path("season-review.md"), help="review written here if needed")
    check_cmd.add_argument("--season-file", type=Path, help="Season file to check (default: the current one)")
    check_cmd.add_argument("--delay", type=float, default=3.0, help="seconds between requests (be polite)")
    check_cmd.add_argument("--github-output", type=Path, help="append changed/claude/review results for the workflow")
    args = parser.parse_args(argv)
    if args.command == "check-season":
        return _check_season(args, today, client)

    # Alerts are only sent when asked to. If they're asked for but the mail
    # settings are missing, the Hub is still built and the run reports it.
    settings: MailSettings | None = None
    if args.send_alerts or args.send_notification:
        missing = MailSettings.missing(env)
        if missing:
            print(f"Can't send emails: set {', '.join(missing)} (see the README).", file=sys.stderr)
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
    print(f"Wrote the Hub to {args.out} for {today.isoformat()}")
    for alert in result.alerts:
        print(f"{alert.level.upper()}: {alert.sport_id}: {alert.message}", file=sys.stderr)

    all_sent = True
    if args.send_alerts:
        if settings is None or sender is None:
            all_sent = False
        else:
            message = alert_message(result.alerts, sports, today, settings)
            all_sent = message is None or _send(sender, message)

    # The Monday Notification, at most once per Monday even if the run is repeated.
    notified_on = previous.notified_on if previous else None
    if args.send_notification and is_notification_day(today) and notified_on != today:
        to = recipients(env.get(ENV_NOTIFY_TO))
        if not to:
            print(f"Can't send the Monday Notification: set {ENV_NOTIFY_TO} (see the README).", file=sys.stderr)
            all_sent = False
        elif settings and sender and _send(sender, notification_message(result.data, today, to, settings.hub_url)):
            notified_on = today
        else:
            all_sent = False

    _write_json(args.state, state_to_json(dataclasses.replace(result.state, notified_on=notified_on)))
    return BUILT if all_sent else BUILT_EMAIL_UNSENT


def _check_season(args: argparse.Namespace, today: date, client: httpx.Client) -> int:
    try:
        sports = load_sports(season_path=args.season_file)
    except ConfigError as exc:
        print(f"Season check stopped: {exc}", file=sys.stderr)
        return 1
    previous = json.loads(args.fingerprints.read_text(encoding="utf-8"))["pages"] if args.fingerprints.exists() else {}
    result = check(client, sports, previous, pause=lambda: time.sleep(args.delay))
    # No run date in the file: it only changes (and gets committed) when a page does.
    _write_json(args.fingerprints, {"pages": result.fingerprints})

    review = result.needs_claude(today)
    if review:
        args.report.write_text(review_report(result, today), encoding="utf-8")
    print(f"Season check: {len(result.changed)} changed, {len(result.unreachable)} couldn't check, review needed: {review}")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as out:
            out.write(f"changed={len(result.changed)}\nunreachable={len(result.unreachable)}\n")
            out.write(f"claude={str(review).lower()}\nreview={str(review).lower()}\n")
    return 0


def _send(sender: MailSender, message: Message) -> bool:
    try:
        sender.send(message)
        return True
    except MailError as exc:
        print(f"Refresh couldn't send the email \"{message.subject}\": {exc}", file=sys.stderr)
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
