from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from listeners.briefing import _days_until

_LA = ZoneInfo("America/Los_Angeles")


def test_days_until_anchored_to_la_calendar():
    """Countdown is a calendar-day diff in America/Los_Angeles (matching the web
    board), NOT the server's local (UTC on Railway) date — otherwise the two
    surfaces disagree by a day late in the US evening."""
    la_today = datetime.now(_LA).date()
    assert _days_until(la_today.isoformat()) == 0
    assert _days_until((la_today + timedelta(days=8)).isoformat()) == 8
    assert _days_until((la_today - timedelta(days=3)).isoformat()) == -3


def test_days_until_handles_missing_and_bad_input():
    assert _days_until(None) is None
    assert _days_until("not-a-date") is None
