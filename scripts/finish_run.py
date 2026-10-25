"""The workflow's final step: emails Katie about anything she hasn't heard yet, and sets the run's result.

Runs with the system Python and no installed packages (it only needs
sports_hub.run_outcome and sports_hub.mail, which use the standard library),
so it works even when installing the project is what failed.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sports_hub.run_outcome import finish  # noqa: E402

sys.exit(finish(os.environ, sender=None))
