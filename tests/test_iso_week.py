from datetime import datetime, timezone
import pytest
from digest_engine.iso_week import parse_iso_week, current_iso_week


def test_parse_iso_week_returns_monday_to_sunday_utc():
    start, end = parse_iso_week("2026-W17")
    # ISO week 17 of 2026 = Apr 20 (Mon) to Apr 26 (Sun)
    assert start == datetime(2026, 4, 20, 0, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 4, 26, 23, 59, 59, tzinfo=timezone.utc)


def test_parse_iso_week_rejects_malformed():
    with pytest.raises(ValueError):
        parse_iso_week("2026-17")
    with pytest.raises(ValueError):
        parse_iso_week("2026-W99")


def test_current_iso_week_returns_string_in_format():
    s = current_iso_week()
    assert len(s) == 8 and s[4] == "-" and s[5] == "W"
