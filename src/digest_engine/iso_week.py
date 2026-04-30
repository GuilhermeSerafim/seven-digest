from datetime import date, datetime, timedelta, timezone
import re

_WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")


def parse_iso_week(week_id: str) -> tuple[datetime, datetime]:
    m = _WEEK_RE.match(week_id)
    if not m:
        raise ValueError(f"invalid ISO week id: {week_id!r}")
    year, week = int(m.group(1)), int(m.group(2))
    if not 1 <= week <= 53:
        raise ValueError(f"week out of range: {week}")
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    start = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59, tzinfo=timezone.utc)
    return start, end


def current_iso_week(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"
