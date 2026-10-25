"""Winter-season arithmetic shared by the FIS and IBU fetchers."""

from datetime import date


def winter_start_year(today: date) -> int:
    """The year the current winter season began: from July on, the new season counts."""
    return today.year if today.month >= 7 else today.year - 1
