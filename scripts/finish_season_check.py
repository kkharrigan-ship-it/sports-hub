"""The Season-file check workflow's last step: emails Katie only when she needs to act.

Runs with the system Python and no installed packages (sports_hub.season_outcome
and sports_hub.mail use only the standard library).
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sports_hub.season_outcome import finish_check  # noqa: E402

today = datetime.now(ZoneInfo("America/Chicago")).date()
sys.exit(finish_check(os.environ, sender=None, today=today))
