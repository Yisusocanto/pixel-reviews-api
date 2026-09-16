from datetime import UTC, datetime


def get_current_date() -> datetime:
    """Returns the current timestamp in UTC timezone."""
    return datetime.now(UTC)
