"""Loads the Sports config and the current Season file into Sports.

The Sports config is the single source of truth for Sports and Watch options;
the Season file adds hand-checked Events and off-season labels.
"""

from pathlib import Path
from typing import Any, cast, get_args

import yaml

from sports_hub.errors import ConfigError
from sports_hub.fetchers import FETCHERS
from sports_hub.model import Sport, WatchOption, WatchType
from sports_hub.season_file import load_season_file

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
DEFAULT_SPORTS_FILE = CONFIG_DIR / "sports.yaml"
WATCH_TYPES = get_args(WatchType)


def current_season_file() -> Path:
    """The newest Season file, e.g. config/seasons/2026-27.yaml."""
    files = sorted((CONFIG_DIR / "seasons").glob("*.yaml"))
    if not files:
        raise ConfigError("no Season file found in config/seasons/")
    return files[-1]


def load_sports(path: Path = DEFAULT_SPORTS_FILE, season_path: Path | None = None) -> list[Sport]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"{path.name}: can't be read ({exc})") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("sports"), list):
        raise ConfigError(f"{path.name}: needs a top-level 'sports:' list")
    sports = [_sport(n, entry) for n, entry in enumerate(raw["sports"], start=1)]

    season = load_season_file(season_path or current_season_file())
    unknown = sorted(set(season) - {s.id for s in sports})
    if unknown:
        raise ConfigError(f"Season file lists Sports not in {path.name}: {', '.join(unknown)}")
    return [season[s.id].apply_to(s) if s.id in season else s for s in sports]


def _sport(n: int, entry: Any) -> Sport:
    if not isinstance(entry, dict):
        raise ConfigError(f"Sport #{n}: expected a mapping of fields")
    sport_id = entry.get("id") or f"#{n}"

    def required(key: str) -> str:
        value = entry.get(key)
        if not value:
            raise ConfigError(f"Sport {sport_id}: missing required field '{key}'")
        return str(value)

    raw_sources = entry.get("sources") or entry.get("source") or []
    if isinstance(raw_sources, str):  # `source: x` or `sources: x` both mean one source
        raw_sources = [raw_sources]
    if not raw_sources:
        raise ConfigError(f"Sport {sport_id}: missing required field 'source' (or a 'sources' list)")
    sources = tuple(str(s) for s in raw_sources)
    for source in sources:
        if source not in FETCHERS:
            known = ", ".join(sorted(FETCHERS))
            raise ConfigError(f"Sport {sport_id}: unknown source '{source}' (known: {known})")
    return Sport(
        id=required("id"),
        name=required("name"),
        category=required("category"),
        sources=sources,
        watch=tuple(_watch(sport_id, w) for w in entry.get("watch", [])),
        rights_unconfirmed=bool(entry.get("rights_unconfirmed", False)),
        params={k: str(v) for k, v in entry.get("params", {}).items()},
    )


def _watch(sport_id: str, w: Any) -> WatchOption:
    if not isinstance(w, dict) or not w.get("label"):
        raise ConfigError(f"Sport {sport_id}: each watch option needs a 'label'")
    if w.get("type") not in WATCH_TYPES:
        raise ConfigError(
            f"Sport {sport_id}: watch option {w['label']!r} has type {w.get('type')!r}; use one of {', '.join(WATCH_TYPES)}"
        )
    return WatchOption(label=w["label"], type=cast(WatchType, w["type"]), price=w.get("price"), note=w.get("note"))
