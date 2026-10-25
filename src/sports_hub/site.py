"""Writes the Hub: the static page, its data.json and calendar feeds, as one folder.

The folder is built beside the target and swapped in at the end, so a failed
Refresh never leaves a half-written Hub behind.
"""

import json
import shutil
from pathlib import Path

from sports_hub.calendar_feed import FEEDS_DIR
from sports_hub.refresh import RefreshResult

SITE_SOURCE = Path(__file__).resolve().parents[2] / "site"


def write_hub(out: Path, result: RefreshResult) -> None:
    building = out.with_name(out.name + ".building")
    if building.exists():
        shutil.rmtree(building)
    shutil.copytree(SITE_SOURCE, building)
    (building / "data.json").write_text(json.dumps(result.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    feeds = building / FEEDS_DIR
    feeds.mkdir()
    for name, content in result.feeds.items():
        (feeds / name).write_bytes(content)

    previous = out.with_name(out.name + ".previous")
    if previous.exists():
        shutil.rmtree(previous)
    if out.exists():
        out.rename(previous)
    building.rename(out)
    if previous.exists():
        shutil.rmtree(previous)
